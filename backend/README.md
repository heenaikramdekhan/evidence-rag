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

Interactive docs at <http://localhost:8000/docs>.

## Evaluation

```bash
# Fill in eval/golden_set.jsonl with your own Q/A pairs first.
python -m eval.evaluate --threshold 0.9        # exits non-zero if below threshold
python -m eval.report > eval_report.md
```

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
