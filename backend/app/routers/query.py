"""Query + stats endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from .. import db
from ..config import get_settings
from ..generation.llm import LLMError
from ..pipeline import answer_question, retrieve_only
from ..retrieval.vector_store import get_vector_store
from ..schemas import (
    DocumentInfo,
    DocumentsResponse,
    HistoryItem,
    QueryRequest,
    QueryResponse,
    RetrieveResponse,
    StatsResponse,
)

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    if get_vector_store().count() == 0:
        raise HTTPException(
            status_code=409,
            detail="No documents ingested yet. Add files to data/raw_docs and POST /ingest.",
        )
    try:
        return answer_question(req.question, req.top_k)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: QueryRequest) -> RetrieveResponse:
    """Return the ranked chunks for a question — retrieval only, no LLM."""
    if get_vector_store().count() == 0:
        raise HTTPException(
            status_code=409,
            detail="No documents ingested yet. Add files to data/raw_docs and POST /ingest.",
        )
    return retrieve_only(req.question, req.top_k)


@router.get("/history", response_model=list[HistoryItem])
def history(limit: int = Query(default=50, ge=1, le=200)) -> list[HistoryItem]:
    return db.list_history(limit)


@router.delete("/history")
def clear_history() -> dict[str, int]:
    return {"deleted": db.clear_history()}


@router.get("/documents", response_model=DocumentsResponse)
def documents() -> DocumentsResponse:
    """List the distinct source files in the corpus with their chunk counts."""
    sources = get_vector_store().list_sources()
    docs = [DocumentInfo(source=s, chunks=n) for s, n in sources]
    return DocumentsResponse(
        documents=docs,
        total_documents=len(docs),
        total_chunks=sum(d.chunks for d in docs),
    )


@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    settings = get_settings()
    return StatsResponse(
        collection=settings.collection_name,
        chunks=get_vector_store().count(),
        embedding_model=settings.embedding_model,
        llm_provider=settings.llm_provider,
    )
