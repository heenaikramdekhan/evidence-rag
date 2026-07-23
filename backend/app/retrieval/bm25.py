"""BM25 keyword index (pure Python via rank_bm25).

Rebuilt from the vector store's chunks. Cheap enough to build on demand and
cache in memory; call ``invalidate()`` after re-ingesting.
"""
from __future__ import annotations

import re

from ..schemas import Chunk


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Index:
    def __init__(self, chunks: list[Chunk]) -> None:
        from rank_bm25 import BM25Okapi

        self._chunks = chunks
        self._bm25 = BM25Okapi([_tokenize(c.text) for c in chunks]) if chunks else None

    def query(self, question: str, top_k: int) -> list[Chunk]:
        if not self._bm25 or not self._chunks:
            return []
        scores = self._bm25.get_scores(_tokenize(question))
        ranked = sorted(
            zip(self._chunks, scores), key=lambda x: x[1], reverse=True
        )[:top_k]
        out: list[Chunk] = []
        for chunk, score in ranked:
            out.append(chunk.model_copy(update={"score": float(score)}))
        return out


_index: BM25Index | None = None


def get_bm25_index() -> BM25Index:
    global _index
    if _index is None:
        from .vector_store import get_vector_store

        _index = BM25Index(get_vector_store().all_chunks())
    return _index


def invalidate() -> None:
    """Force a rebuild on next access (call after ingestion)."""
    global _index
    _index = None
