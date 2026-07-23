"""Shared pytest fixtures.

The ``client`` fixture spins up the FastAPI app against a throwaway, EMPTY
Chroma collection and a temp SQLite DB — so API tests are fast, isolated, and
never touch your real index, load ML models, or call the LLM.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    # Point storage at throwaway locations BEFORE the app reads settings.
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("COLLECTION_NAME", "test_evidence")
    monkeypatch.setenv("HISTORY_DB", str(tmp_path / "history.db"))

    # Reset cached settings + singletons so the temp paths take effect.
    from app.config import get_settings
    from app.retrieval import vector_store
    from app import db

    get_settings.cache_clear()
    vector_store._store = None
    db._initialized = False

    from app.main import app

    with TestClient(app) as c:
        yield c

    # Clean up global state so later tests don't inherit temp settings.
    get_settings.cache_clear()
    vector_store._store = None
    db._initialized = False
