"""CLI: ingest everything in data/raw_docs into the vector store + BM25 index.

    python -m scripts.ingest_docs
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline import ingest_directory  # noqa: E402


def main() -> None:
    print("Ingesting documents from data/raw_docs ...")
    n_docs, n_chunks = ingest_directory(reset=True)
    if n_docs == 0:
        print("No supported documents found. Drop PDFs/Markdown/HTML/TXT into "
              "backend/data/raw_docs and re-run.")
        return
    print(f"Done: {n_docs} document(s) -> {n_chunks} chunk(s) indexed.")


if __name__ == "__main__":
    main()
