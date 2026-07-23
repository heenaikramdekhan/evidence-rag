"""SQLite query-history tests (uses a temp DB, no models/network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import Citation, QueryResponse  # noqa: E402


def _fresh_db(tmp_path, monkeypatch):
    """Point the settings at a throwaway DB file and return the db module."""
    monkeypatch.setenv("HISTORY_DB", str(tmp_path / "history.db"))
    from app.config import get_settings

    get_settings.cache_clear()
    from app import db

    db._initialized = False
    db.init_db()
    return db


def _resp(answer="An answer [1].", used=True):
    return QueryResponse(
        answer=answer,
        citations=[Citation(id="d::0::x", source="d.md", chunk_index=0, text="ctx", score=0.9)],
        used_context=used,
        latency_ms=12.3,
    )


def test_save_and_list_roundtrip(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    rid = db.save_query("What is X?", _resp())
    assert rid == 1

    items = db.list_history()
    assert len(items) == 1
    item = items[0]
    assert item.question == "What is X?"
    assert item.used_context is True
    assert item.citations[0].source == "d.md"
    assert item.created_at  # ISO timestamp present


def test_history_is_newest_first(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    db.save_query("first", _resp())
    db.save_query("second", _resp())
    questions = [i.question for i in db.list_history()]
    assert questions == ["second", "first"]


def test_clear_history(tmp_path, monkeypatch):
    db = _fresh_db(tmp_path, monkeypatch)
    db.save_query("q", _resp())
    assert db.clear_history() == 1
    assert db.list_history() == []
