"""End-to-end RAG orchestration — plain Python, no framework.

    ingest:  files -> text -> chunks -> embeddings -> ChromaDB (+ BM25 rebuild)
    query:   question -> hybrid retrieve -> rerank -> generate -> cited answer
"""
from __future__ import annotations

import time

from . import db
from .config import get_settings
from .generation.answer import generate_answer
from .ingest.chunker import chunk_documents
from .ingest.loaders import load_directory
from .retrieval import bm25
from .retrieval.hybrid import hybrid_search
from .retrieval.rerank import rerank
from .retrieval.vector_store import get_vector_store
from .schemas import QueryResponse


def ingest_directory(reset: bool = True) -> tuple[int, int]:
    """Ingest everything under ``data/raw_docs``. Returns (n_docs, n_chunks)."""
    settings = get_settings()
    docs = load_directory(settings.raw_docs_path)
    chunks = chunk_documents(docs, settings.chunk_size, settings.chunk_overlap)

    store = get_vector_store()
    if reset:
        store.reset()
    store.add(chunks)
    bm25.invalidate()  # force BM25 rebuild against the new corpus
    return len(docs), len(chunks)


def answer_question(
    question: str, top_k: int | None = None, record: bool = True
) -> QueryResponse:
    settings = get_settings()
    started = time.perf_counter()

    # First-stage: cast a wide net with hybrid retrieval.
    candidates = hybrid_search(question)
    # Second-stage: precise rerank down to the final context set.
    final = rerank(question, candidates, top_k or settings.top_k_rerank)

    answer, citations, used_context = generate_answer(question, final)
    latency_ms = (time.perf_counter() - started) * 1000

    resp = QueryResponse(
        answer=answer,
        citations=citations,
        used_context=used_context,
        latency_ms=round(latency_ms, 1),
    )
    if record:
        # History is a nice-to-have; never fail a query because logging failed.
        try:
            db.save_query(question, resp)
        except Exception as exc:  # noqa: BLE001
            print(f"[history] failed to record query: {exc}")
    return resp
