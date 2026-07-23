"""Ingestion endpoints: upload files and (re)build the index."""
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from ..config import get_settings
from ..ingest.loaders import SUPPORTED_SUFFIXES
from ..pipeline import ingest_directory
from ..schemas import IngestResponse

router = APIRouter(tags=["ingest"])


@router.post("/upload", response_model=IngestResponse)
async def upload(files: list[UploadFile] = File(...)) -> IngestResponse:
    """Save uploaded files into data/raw_docs, then reindex the whole corpus."""
    settings = get_settings()
    settings.raw_docs_path.mkdir(parents=True, exist_ok=True)
    for f in files:
        suffix = "." + (f.filename or "").rsplit(".", 1)[-1].lower()
        if suffix not in SUPPORTED_SUFFIXES:
            continue
        dest = settings.raw_docs_path / (f.filename or "upload")
        dest.write_bytes(await f.read())

    n_docs, n_chunks = ingest_directory(reset=True)
    return IngestResponse(
        documents=n_docs, chunks=n_chunks, collection=settings.collection_name
    )


@router.post("/ingest", response_model=IngestResponse)
def ingest() -> IngestResponse:
    """Reindex whatever is already sitting in data/raw_docs."""
    settings = get_settings()
    n_docs, n_chunks = ingest_directory(reset=True)
    return IngestResponse(
        documents=n_docs, chunks=n_chunks, collection=settings.collection_name
    )
