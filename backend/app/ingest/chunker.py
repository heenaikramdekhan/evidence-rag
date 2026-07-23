"""Sliding-window chunker.

Approximates token counts with a simple word-based heuristic (~0.75 words per
token) so we stay dependency-free. Chunks target ``chunk_size`` tokens with
``chunk_overlap`` tokens of overlap to preserve context across boundaries.
"""
from __future__ import annotations

import hashlib
import re

from ..schemas import Chunk

# Rough words-per-token ratio for English. Good enough for windowing; the
# embedding model does the real tokenization downstream.
_WORDS_PER_TOKEN = 0.75


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[Chunk]:
    """Split ``text`` into overlapping chunks tagged with ``source``."""
    words = re.findall(r"\S+", text)
    if not words:
        return []

    # Convert token targets into word windows.
    window = max(1, int(chunk_size * _WORDS_PER_TOKEN))
    step = max(1, window - int(overlap * _WORDS_PER_TOKEN))

    chunks: list[Chunk] = []
    idx = 0
    start = 0
    while start < len(words):
        piece = " ".join(words[start : start + window]).strip()
        if piece:
            chunk_id = _chunk_id(source, idx, piece)
            chunks.append(
                Chunk(id=chunk_id, text=piece, source=source, chunk_index=idx)
            )
            idx += 1
        if start + window >= len(words):
            break
        start += step
    return chunks


def chunk_documents(
    docs: dict[str, str],
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for source, text in docs.items():
        all_chunks.extend(chunk_text(text, source, chunk_size, overlap))
    return all_chunks


def _chunk_id(source: str, idx: int, text: str) -> str:
    digest = hashlib.sha1(f"{source}:{idx}:{text}".encode()).hexdigest()[:10]
    return f"{source}::{idx}::{digest}"
