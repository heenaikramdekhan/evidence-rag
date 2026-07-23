"""Central configuration, loaded from environment / `.env`.

Every setting has a sensible default so the system runs out of the box; the
only thing you *must* provide for cloud generation is ``GROQ_API_KEY``.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo-relative base so paths resolve no matter where you launch from.
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    llm_provider: str = "groq"  # "groq" | "ollama"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    # --- Embeddings / reranking ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # --- Storage ---
    chroma_dir: str = "./data/chroma"
    collection_name: str = "evidence"
    history_db: str = "./data/history.db"

    # --- Chunking ---
    chunk_size: int = 700
    chunk_overlap: int = 100

    # --- Retrieval ---
    top_k_vector: int = 10
    top_k_bm25: int = 10
    top_k_rerank: int = 5
    use_reranker: bool = True

    @property
    def chroma_path(self) -> Path:
        p = Path(self.chroma_dir)
        return p if p.is_absolute() else (BACKEND_DIR / p)

    @property
    def history_db_path(self) -> Path:
        p = Path(self.history_db)
        return p if p.is_absolute() else (BACKEND_DIR / p)

    @property
    def raw_docs_path(self) -> Path:
        return BACKEND_DIR / "data" / "raw_docs"

    @property
    def prompts_path(self) -> Path:
        return BACKEND_DIR / "config" / "prompts.yaml"


@lru_cache
def get_settings() -> Settings:
    return Settings()
