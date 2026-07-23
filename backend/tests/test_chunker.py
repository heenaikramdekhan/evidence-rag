"""Chunker unit tests — no models or network required."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest.chunker import chunk_text  # noqa: E402


def test_empty_text_yields_no_chunks():
    assert chunk_text("", "doc.txt") == []


def test_short_text_is_single_chunk():
    chunks = chunk_text("hello world foo bar", "doc.txt", chunk_size=700, overlap=100)
    assert len(chunks) == 1
    assert chunks[0].source == "doc.txt"
    assert chunks[0].chunk_index == 0


def test_long_text_produces_overlapping_chunks():
    words = " ".join(f"w{i}" for i in range(2000))
    chunks = chunk_text(words, "doc.txt", chunk_size=200, overlap=50)
    assert len(chunks) > 1
    # Chunk indices are contiguous starting at 0.
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # Overlap: last words of chunk 0 reappear at the start of chunk 1.
    first_tail = set(chunks[0].text.split()[-30:])
    second_head = set(chunks[1].text.split()[:30])
    assert first_tail & second_head


def test_chunk_ids_are_unique():
    words = " ".join(f"w{i}" for i in range(1000))
    chunks = chunk_text(words, "doc.txt", chunk_size=150, overlap=30)
    assert len({c.id for c in chunks}) == len(chunks)
