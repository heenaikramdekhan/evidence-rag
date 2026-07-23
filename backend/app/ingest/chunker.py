"""Sentence/paragraph-aware chunker.

Rather than cutting on raw word windows (which slices sentences in half and
hurts both retrieval and citation readability), this packs whole sentences —
respecting paragraph boundaries — into chunks that target ``chunk_size`` tokens,
carrying ``chunk_overlap`` tokens of trailing sentences into the next chunk for
context continuity.

Token counts are approximated from word counts (~0.75 words/token) so the module
stays dependency-free; the embedding model does the real tokenization downstream.
Unstructured text with no sentence punctuation (e.g. a table dump) falls back to
overlapping word windows so nothing is lost.
"""
from __future__ import annotations

import hashlib
import re

from ..schemas import Chunk

# Rough words-per-token ratio for English. Good enough for windowing.
_WORDS_PER_TOKEN = 0.75

# End of sentence: terminal punctuation (., !, ?) followed by whitespace.
# Fixed-width lookbehind (single char) per Python's re engine.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    """Split into sentences, treating blank-line paragraph breaks as boundaries."""
    sentences: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        flat = re.sub(r"\s+", " ", paragraph)
        for sentence in _SENTENCE_SPLIT.split(flat):
            sentence = sentence.strip()
            if sentence:
                sentences.append(sentence)
    return sentences


def _to_units(sentences: list[str], word_budget: int, overlap_words: int) -> list[str]:
    """Turn sentences into packable units, hard-splitting any that alone exceed
    the budget into *overlapping* word windows (so long, punctuation-free spans
    still get chunked with overlap)."""
    step = max(1, word_budget - overlap_words)
    units: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if len(words) <= word_budget:
            units.append(sentence)
            continue
        start = 0
        while start < len(words):
            units.append(" ".join(words[start : start + word_budget]))
            if start + word_budget >= len(words):
                break
            start += step
    return units


def _overlap_tail(units: list[str], overlap_words: int) -> list[str]:
    """Trailing units summing to ~overlap_words, to seed the next chunk.
    Never returns the whole chunk (guarantees forward progress)."""
    if overlap_words <= 0:
        return []
    tail: list[str] = []
    total = 0
    for unit in reversed(units):
        tail.insert(0, unit)
        total += len(unit.split())
        if total >= overlap_words:
            break
    if len(tail) >= len(units):
        tail = tail[1:]
    return tail


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[Chunk]:
    """Split ``text`` into sentence-aware, overlapping chunks tagged ``source``."""
    sentences = _split_sentences(text)
    if not sentences:
        return []

    word_budget = max(1, int(chunk_size * _WORDS_PER_TOKEN))
    overlap_words = max(0, int(overlap * _WORDS_PER_TOKEN))
    units = _to_units(sentences, word_budget, overlap_words)

    chunks: list[Chunk] = []
    idx = 0
    current: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal idx, current, current_words
        piece = " ".join(current).strip()
        if piece:
            chunks.append(
                Chunk(id=_chunk_id(source, idx, piece), text=piece, source=source, chunk_index=idx)
            )
            idx += 1

    for unit in units:
        words = len(unit.split())
        if current and current_words + words > word_budget:
            flush()
            current = _overlap_tail(current, overlap_words)
            current_words = sum(len(u.split()) for u in current)
        current.append(unit)
        current_words += words

    if current:
        flush()
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
