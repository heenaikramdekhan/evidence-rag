"""Pydantic models shared across the API and pipeline."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A retrievable unit of text with provenance."""

    id: str
    text: str
    source: str  # filename the chunk came from
    chunk_index: int  # ordinal within the source document
    score: float | None = None  # relevance score attached during retrieval


class Citation(BaseModel):
    id: str
    source: str
    chunk_index: int
    text: str
    score: float | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    used_context: bool  # False when the model refused for lack of evidence
    latency_ms: float


class RetrieveResponse(BaseModel):
    """Retrieval-only result: the ranked chunks, no LLM generation."""

    question: str
    chunks: list[Chunk]
    latency_ms: float


class HistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    citations: list[Citation]
    used_context: bool
    latency_ms: float | None
    created_at: str  # ISO-8601 UTC timestamp


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    collection: str


class StatsResponse(BaseModel):
    collection: str
    chunks: int
    embedding_model: str
    llm_provider: str
