"""Retrieval-logic tests that don't require model downloads."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.bm25 import BM25Index  # noqa: E402
from app.retrieval.hybrid import _rrf  # noqa: E402
from app.schemas import Chunk  # noqa: E402


def _chunk(cid: str, text: str) -> Chunk:
    return Chunk(id=cid, text=text, source="d.txt", chunk_index=0)


def test_bm25_ranks_keyword_match_first():
    chunks = [
        _chunk("a", "the cat sat on the mat"),
        _chunk("b", "quantum chromodynamics and gluon fields"),
        _chunk("c", "a dog ran in the park"),
    ]
    idx = BM25Index(chunks)
    hits = idx.query("gluon fields", top_k=1)
    assert hits and hits[0].id == "b"


def test_rrf_rewards_agreement_across_rankings():
    a, b, c = _chunk("a", "x"), _chunk("b", "y"), _chunk("c", "z")
    # 'a' is top of both rankings -> should win the fusion.
    fused = _rrf([[a, b, c], [a, c, b]])
    assert fused[0].id == "a"
    assert {ch.id for ch in fused} == {"a", "b", "c"}


def test_bm25_empty_index_returns_nothing():
    assert BM25Index([]).query("anything", top_k=5) == []
