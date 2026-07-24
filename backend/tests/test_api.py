"""FastAPI integration tests (TestClient).

Run against an empty, isolated index — so they exercise routing, validation,
status codes, and the refuse-when-empty behavior without any models or LLM.
"""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_stats_on_empty_index(client):
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["chunks"] == 0
    assert body["collection"] == "test_evidence"
    # These come from settings and should always be present.
    assert body["embedding_model"]
    assert body["llm_provider"]


def test_query_on_empty_index_returns_409(client):
    r = client.post("/query", json={"question": "anything at all"})
    assert r.status_code == 409
    assert "ingest" in r.json()["detail"].lower()


def test_retrieve_on_empty_index_returns_409(client):
    r = client.post("/retrieve", json={"question": "anything at all"})
    assert r.status_code == 409


def test_query_rejects_empty_question(client):
    # question has min_length=1 -> validation error before any work happens.
    r = client.post("/query", json={"question": ""})
    assert r.status_code == 422


def test_query_requires_question_field(client):
    r = client.post("/query", json={})
    assert r.status_code == 422


def test_history_starts_empty(client):
    r = client.get("/history")
    assert r.status_code == 200
    assert r.json() == []


def test_history_limit_is_validated(client):
    # limit is bounded 1..200.
    assert client.get("/history?limit=0").status_code == 422
    assert client.get("/history?limit=201").status_code == 422
    assert client.get("/history?limit=50").status_code == 200


def test_clear_history_on_empty(client):
    r = client.delete("/history")
    assert r.status_code == 200
    assert r.json() == {"deleted": 0}


def test_documents_on_empty_index(client):
    r = client.get("/documents")
    assert r.status_code == 200
    body = r.json()
    assert body == {"documents": [], "total_documents": 0, "total_chunks": 0}


def test_openapi_documents_core_routes(client):
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    for route in (
        "/query",
        "/retrieve",
        "/ingest",
        "/upload",
        "/history",
        "/stats",
        "/documents",
    ):
        assert route in paths, f"{route} missing from OpenAPI schema"
