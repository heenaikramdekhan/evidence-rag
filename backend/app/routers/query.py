"""Query + stats endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..generation.llm import LLMError
from ..pipeline import answer_question
from ..retrieval.vector_store import get_vector_store
from ..schemas import QueryRequest, QueryResponse, StatsResponse

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


@router.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    settings = get_settings()
    return StatsResponse(
        collection=settings.collection_name,
        chunks=get_vector_store().count(),
        embedding_model=settings.embedding_model,
        llm_provider=settings.llm_provider,
    )
