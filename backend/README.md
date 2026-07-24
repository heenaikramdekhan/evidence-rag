# Evidence-RAG — Backend

Hybrid-retrieval RAG (vector + BM25 → cross-encoder rerank → cited generation),
built entirely on free-tier / local tools. FastAPI + ChromaDB + sentence-transformers.

## Setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# macOS/Linux:         source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your GROQ_API_KEY (free, no card)
```

Get a free Groq key at <https://console.groq.com>. For fully offline use, set
`LLM_PROVIDER=ollama`, run `ollama serve`, and `ollama pull llama3.2:3b`.

## Ingest & ask (CLI)

```bash
python -m scripts.ingest_docs                 # indexes data/raw_docs/
python -m scripts.ask "What is the retention period after a case closes?"
python -m scripts.ask                          # interactive REPL
python -m scripts.retrieve "chain of custody"   # inspect retrieval only (no LLM)
```

The repo ships with one sample document so this works immediately. Replace
`data/raw_docs/` with your own 10–50 PDFs/Markdown/HTML files, then re-ingest.

## API

```bash
uvicorn app.main:app --reload --port 8000
```

| Method | Path       | Purpose                                        |
|--------|------------|------------------------------------------------|
| GET    | `/health`  | Liveness check                                 |
| GET    | `/stats`   | Chunk count, models, provider                  |
| POST   | `/ingest`  | Reindex whatever is in `data/raw_docs/`        |
| POST   | `/upload`  | Upload files (multipart) then reindex          |
| POST   | `/query`   | `{ "question": "..." }` → cited answer         |
| POST   | `/retrieve`| Ranked chunks + scores, **no LLM** (inspect retrieval) |
| GET    | `/documents`| Source files in the corpus + per-file chunk counts |
| GET    | `/documents/{source}`| One document's full text, chunk by chunk (view) |
| GET    | `/history` | Recent queries (persisted in SQLite)           |
| DELETE | `/history` | Clear all query history                        |

Interactive docs at <http://localhost:8000/docs>.

## Evaluation

```bash
# eval/golden_set.jsonl ships a real set seeded from the sample doc;
# swap in your own Q/A pairs once you load your corpus.
python -m eval.evaluate --threshold 0.9        # exits non-zero if below threshold
python -m eval.report > eval_report.md
```

### Provider comparison (Groq vs. Ollama)

```bash
python -m eval.compare_providers               # both; writes eval/provider_comparison.md
python -m eval.compare_providers --providers groq
```

Runs the golden set through each provider on identical retrieved context and
scores accuracy + refusal + latency. For the local side, run `ollama serve` and
`ollama pull llama3.2:3b` first; an unreachable provider is reported as
*unavailable* instead of crashing.

## Tests

```bash
pytest        # chunker + retrieval logic; no model downloads needed
```

## Architecture

```
files ─▶ loaders ─▶ chunker ─▶ embed ─▶ ChromaDB
                                  └────▶ BM25 index
question ─▶ hybrid (RRF) ─▶ cross-encoder rerank ─▶ LLM (Groq/Ollama) ─▶ cited answer
```
