"""ChromaDB-backed vector store (local, on-disk, free).

We manage embeddings ourselves (via ``embed.py``) rather than letting Chroma
call an embedding function, so the exact same model is used everywhere and the
store stays provider-agnostic.
"""
from __future__ import annotations

from ..config import get_settings
from ..schemas import Chunk
from .embed import embed_query, embed_texts


class VectorStore:
    def __init__(self) -> None:
        import chromadb

        settings = get_settings()
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(settings.chroma_path))
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # --- writes ---
    def add(self, chunks: list[Chunk], batch_size: int = 128) -> None:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            self._collection.add(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                embeddings=embed_texts([c.text for c in batch]),
                metadatas=[
                    {"source": c.source, "chunk_index": c.chunk_index} for c in batch
                ],
            )

    def reset(self) -> None:
        """Drop and recreate the collection."""
        settings = get_settings()
        try:
            self._client.delete_collection(settings.collection_name)
        except Exception:  # noqa: BLE001 - fine if it didn't exist
            pass
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # --- reads ---
    def count(self) -> int:
        return self._collection.count()

    def all_chunks(self) -> list[Chunk]:
        """Return every stored chunk (used to build the BM25 index)."""
        got = self._collection.get(include=["documents", "metadatas"])
        chunks: list[Chunk] = []
        for cid, doc, meta in zip(got["ids"], got["documents"], got["metadatas"]):
            chunks.append(
                Chunk(
                    id=cid,
                    text=doc,
                    source=meta.get("source", "unknown"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                )
            )
        return chunks

    def list_sources(self) -> list[tuple[str, int]]:
        """Distinct source files with their chunk counts, sorted by name."""
        got = self._collection.get(include=["metadatas"])
        counts: dict[str, int] = {}
        for meta in got["metadatas"]:
            src = meta.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return sorted(counts.items())

    def chunks_for(self, source: str) -> list[Chunk]:
        """Every chunk belonging to one source file, ordered by chunk_index."""
        got = self._collection.get(
            where={"source": source}, include=["documents", "metadatas"]
        )
        chunks = [
            Chunk(
                id=cid,
                text=doc,
                source=meta.get("source", "unknown"),
                chunk_index=int(meta.get("chunk_index", 0)),
            )
            for cid, doc, meta in zip(got["ids"], got["documents"], got["metadatas"])
        ]
        return sorted(chunks, key=lambda c: c.chunk_index)

    def query(self, question: str, top_k: int) -> list[Chunk]:
        if self.count() == 0:
            return []
        res = self._collection.query(
            query_embeddings=[embed_query(question)],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        chunks: list[Chunk] = []
        ids = res["ids"][0]
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            # cosine distance -> similarity in [0, 1]
            chunks.append(
                Chunk(
                    id=cid,
                    text=doc,
                    source=meta.get("source", "unknown"),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    score=1.0 - float(dist),
                )
            )
        return chunks


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
