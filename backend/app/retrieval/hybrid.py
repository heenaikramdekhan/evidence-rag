"""Hybrid retrieval: fuse dense (vector) and sparse (BM25) results.

Uses Reciprocal Rank Fusion (RRF), which combines rankings without needing the
two score scales to be comparable — robust and parameter-light.
"""
from __future__ import annotations

from ..config import get_settings
from ..schemas import Chunk
from .bm25 import get_bm25_index
from .vector_store import get_vector_store

RRF_K = 60  # standard constant; dampens the influence of low ranks


def _rrf(rankings: list[list[Chunk]]) -> list[Chunk]:
    scores: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (RRF_K + rank + 1)
            by_id.setdefault(chunk.id, chunk)
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [by_id[cid].model_copy(update={"score": score}) for cid, score in fused]


def hybrid_search(question: str, top_k: int | None = None) -> list[Chunk]:
    settings = get_settings()
    vector_hits = get_vector_store().query(question, settings.top_k_vector)
    bm25_hits = get_bm25_index().query(question, settings.top_k_bm25)

    fused = _rrf([vector_hits, bm25_hits])
    if top_k is not None:
        fused = fused[:top_k]
    return fused
