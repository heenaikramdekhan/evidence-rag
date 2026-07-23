"""Cross-encoder reranker.

Takes the fused candidate set from hybrid retrieval and re-scores each
(query, chunk) pair jointly — far more precise than the bi-encoder used for
first-stage retrieval, at the cost of running only over a small candidate set.
"""
from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from ..schemas import Chunk


@lru_cache
def _model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(get_settings().reranker_model)


def rerank(question: str, chunks: list[Chunk], top_k: int) -> list[Chunk]:
    if not chunks:
        return []
    settings = get_settings()
    if not settings.use_reranker:
        return chunks[:top_k]

    pairs = [(question, c.text) for c in chunks]
    scores = _model().predict(pairs)
    reranked = sorted(
        zip(chunks, scores), key=lambda x: x[1], reverse=True
    )[:top_k]
    return [c.model_copy(update={"score": float(s)}) for c, s in reranked]
