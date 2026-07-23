"""FastAPI application entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import ingest, query

app = FastAPI(
    title="Evidence-RAG",
    version="0.1.0",
    description="Hybrid retrieval + reranking RAG with enforced citations.",
)

# Allow the Vite dev server (and anything else, for a local portfolio demo).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router)
app.include_router(ingest.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
