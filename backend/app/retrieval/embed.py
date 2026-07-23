"""Local embedding model wrapper (sentence-transformers, CPU-friendly).

The model is loaded lazily and cached process-wide so importing this module is
cheap and the (slow) model load only happens the first time an embedding is
actually requested.
"""
from __future__ import annotations

from functools import lru_cache

from ..config import get_settings


@lru_cache
def _model():
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of documents."""
    if not texts:
        return []
    vectors = _model().encode(
        texts, normalize_embeddings=True, show_progress_bar=len(texts) > 64
    )
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    """Embed a single query string."""
    return _model().encode([text], normalize_embeddings=True)[0].tolist()
