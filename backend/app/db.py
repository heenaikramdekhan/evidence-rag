"""SQLite-backed query history.

Uses Python's built-in ``sqlite3`` — no extra dependency, one file on disk,
$0. Records every answered question (from the API and the CLI) so the frontend
can show a history view. The DB file is git-ignored.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import get_settings
from .schemas import Citation, HistoryItem, QueryResponse

_initialized = False


@contextmanager
def _connect():
    settings = get_settings()
    path = settings.history_db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create the history table if it doesn't exist (idempotent)."""
    global _initialized
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS query_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                question     TEXT    NOT NULL,
                answer       TEXT    NOT NULL,
                citations    TEXT    NOT NULL DEFAULT '[]',
                used_context INTEGER NOT NULL DEFAULT 0,
                latency_ms   REAL,
                created_at   TEXT    NOT NULL
            )
            """
        )
    _initialized = True


def _ensure() -> None:
    if not _initialized:
        init_db()


def save_query(question: str, resp: QueryResponse) -> int:
    """Persist one answered query. Returns the new row id."""
    _ensure()
    citations_json = json.dumps([c.model_dump() for c in resp.citations])
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO query_history
                (question, answer, citations, used_context, latency_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                question,
                resp.answer,
                citations_json,
                int(resp.used_context),
                resp.latency_ms,
                created_at,
            ),
        )
        return int(cur.lastrowid)


def list_history(limit: int = 50) -> list[HistoryItem]:
    """Return the most recent queries, newest first."""
    _ensure()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM query_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_item(r) for r in rows]


def clear_history() -> int:
    """Delete all history. Returns the number of rows removed."""
    _ensure()
    with _connect() as conn:
        cur = conn.execute("DELETE FROM query_history")
        return cur.rowcount


def _row_to_item(row: sqlite3.Row) -> HistoryItem:
    return HistoryItem(
        id=row["id"],
        question=row["question"],
        answer=row["answer"],
        citations=[Citation(**c) for c in json.loads(row["citations"])],
        used_context=bool(row["used_context"]),
        latency_ms=row["latency_ms"],
        created_at=row["created_at"],
    )
