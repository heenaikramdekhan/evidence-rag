# CLAUDE.md — Evidence-RAG

Guidance for AI assistants working in this repo.

## What this is
A production-shaped, **$0-budget** Retrieval-Augmented Generation system over a
document corpus (default domain: evidence-handling / legal). Portfolio project.
Everything runs on local models + a free-tier LLM API — no paid services.

## Layout
```
backend/          FastAPI + Python RAG pipeline
  app/
    ingest/       loaders.py (pdf/md/html/txt) → chunker.py (sliding window)
    retrieval/    embed.py, vector_store.py (Chroma), bm25.py, hybrid.py (RRF), rerank.py (cross-encoder)
    generation/   llm.py (Groq | Ollama), answer.py (citation formatting + refusal)
    routers/      query.py, ingest.py
    pipeline.py   orchestration (ingest_directory, answer_question)
    config.py     env-driven Settings; schemas.py Pydantic models
  scripts/        ingest_docs.py, ask.py (CLI)
  eval/           golden_set.jsonl, evaluate.py (CI gate), report.py
  data/raw_docs/  the corpus (only the sample file is committed)
frontend/         React 19 + Vite + TypeScript chat UI (plain CSS, no Tailwind)
.github/workflows/eval.yml   CI: pytest + golden-set eval gate
```

## Data flow
- **Ingest:** files → text → chunks → embeddings → ChromaDB; BM25 index rebuilt from Chroma.
- **Query:** question → hybrid (vector + BM25, fused with RRF) → cross-encoder rerank → LLM with numbered SOURCES → answer with `[n]` citations mapped back to chunks. Refuses when evidence is insufficient.

## Conventions
- Config comes from `backend/.env` (never committed). `.env.example` documents every key. Only `GROQ_API_KEY` is required for cloud generation.
- Prompts live in `backend/config/prompts.yaml` — version them; don't hardcode prompt text in Python.
- Chunks are 1-indexed when shown to the LLM; citation `[n]` maps to the n-th reranked chunk.
- Models load lazily and are cached (`@lru_cache`) — importing modules stays cheap.
- Keep it dependency-light; avoid adding heavy libs (e.g. `unstructured`, LangChain) without reason.

## Running
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
- CLI: `python -m scripts.ingest_docs` then `python -m scripts.ask "..."`
- Frontend: `cd frontend && npm install && npm run dev`
- Tests: `cd backend && pytest` (no model downloads needed)

## Gotchas
- The vector store must be non-empty before `/query` (returns 409 otherwise) — ingest first.
- `bm25.invalidate()` must be called after re-ingesting (pipeline does this).
- Switching LLM: set `LLM_PROVIDER=ollama` + run `ollama serve` for fully offline use.
