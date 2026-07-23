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


# --- sentence-awareness ---

def _sentences(n: int) -> str:
    # Each sentence is ~10 words and ends with a period.
    return " ".join(f"Sentence number {i} has some filler words here to pad it out." for i in range(n))


def test_chunks_never_cut_mid_sentence():
    chunks = chunk_text(_sentences(60), "doc.txt", chunk_size=120, overlap=20)
    assert len(chunks) > 1
    # Every chunk should end at a sentence boundary (terminal punctuation).
    for c in chunks:
        assert c.text.rstrip().endswith((".", "!", "?"))


def test_overlap_carries_a_whole_sentence():
    chunks = chunk_text(_sentences(60), "doc.txt", chunk_size=120, overlap=20)
    # The start of chunk 1 should repeat a full sentence from the end of chunk 0.
    import re

    def sents(text):
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

    tail = set(sents(chunks[0].text)[-3:])
    head = set(sents(chunks[1].text)[:3])
    assert tail & head  # at least one shared full sentence


def test_paragraphs_split_into_sentences():
    text = "First para sentence one. First para sentence two.\n\nSecond paragraph only sentence."
    chunks = chunk_text(text, "doc.txt", chunk_size=700, overlap=100)
    # Small enough to be one chunk, and paragraph newlines are normalized away.
    assert len(chunks) == 1
    assert "\n\n" not in chunks[0].text
    assert "sentence two." in chunks[0].text


def test_respects_token_budget_approximately():
    chunks = chunk_text(_sentences(100), "doc.txt", chunk_size=100, overlap=10)
    word_budget = int(100 * 0.75)
    # No chunk should blow far past the word budget (allow one sentence of slack).
    for c in chunks:
        assert len(c.text.split()) <= word_budget + 15
