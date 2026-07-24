
# Evidence-RAG

> A production-shaped Retrieval-Augmented Generation system with hybrid retrieval,
> cross-encoder reranking, and **enforced citations** — built entirely on
> free-tier APIs and local models. **No cost incurred.**

Ask questions about your own document corpus and get answers that are grounded in
the source text, cite the exact chunks they came from, and **refuse to answer**
when the evidence isn't there.

![CI](https://img.shields.io/badge/eval-CI%20gated-6ea8fe)
![cost](https://img.shields.io/badge/cost-%240-9d7bff)

---

## Features
- **Grounded answers with inline `[n]` citations** — every claim maps back to the exact retrieved chunk.
- **Refusal when unsupported** — the system says so instead of hallucinating when the evidence isn't in the corpus.
- **Hybrid retrieval + reranking** — vector + BM25 fused with RRF, then a cross-encoder reranks the top results.
- **Sentence/paragraph-aware chunking** — chunks never cut mid-sentence; overlap carries whole sentences for context.
- **Document upload** — drop PDF/Markdown/HTML/TXT files straight from the UI (or the CLI) and re-index.
- **Query history** — every question/answer is persisted in SQLite and browsable in the UI.
- **Retrieval inspector** — a UI panel that shows the ranked chunks and rerank scores for any query, with **no LLM call**.
- **CI eval gate** — a golden-set eval scores answer accuracy + refusal on every PR and blocks merges below threshold.

## Architecture

```
                 ┌─────────── INGEST ───────────┐
  raw files ──▶  loaders ──▶ chunker ──▶ embed ──▶ ChromaDB
  (pdf/md/html)                              └────▶ BM25 index

                 ┌─────────── QUERY ────────────┐
  question ──▶ hybrid retrieval (vector + BM25, RRF)
           ──▶ cross-encoder rerank (top-5)
           ──▶ LLM (Groq free-tier | Ollama local)
           ──▶ answer with [n] citations  +  refusal when unsupported
```

## The $0 stack

| Layer            | Tool                                                    |
|------------------|---------------------------------------------------------|
| Parsing          | `pypdf`, `markdown-it-py`, `beautifulsoup4`             |
| Chunking         | Sentence/paragraph-aware windows (~700 tok, 100 overlap)|
| Embeddings       | `sentence-transformers` · `all-MiniLM-L6-v2` (local CPU)|
| Vector store     | ChromaDB (on-disk)                                      |
| Keyword search   | `rank_bm25`                                             |
| Fusion           | Reciprocal Rank Fusion                                  |
| Reranker         | `cross-encoder/ms-marco-MiniLM-L-6-v2`                  |
| Generation       | **Groq** free-tier (Llama 3.3) · **Ollama** offline     |
| API              | FastAPI                                                 |
| Frontend         | React 19 + Vite + TypeScript                            |
| CI / eval gate   | GitHub Actions + golden-set script                     |

## Quickstart

**1. Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env          # add your free GROQ_API_KEY (console.groq.com)
python -m scripts.ingest_docs # indexes the sample doc in data/raw_docs
uvicorn app.main:app --reload --port 8000
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

Then ask a question in the UI — or from the CLI:
```bash
python -m scripts.ask "What is the retention period after a case closes?"
```

## Using your own documents
Drop 10–50 PDF/Markdown/HTML/TXT files into `backend/data/raw_docs/`, then
`python -m scripts.ingest_docs` (or POST `/upload` from the UI). Update
`backend/eval/golden_set.jsonl` with question/answer pairs from *your* corpus.

## Evaluation & CI
`backend/eval/golden_set.jsonl` ships a real evaluation set seeded from the
sample policy — in-scope questions with source-grounded answers plus
out-of-scope questions that must be refused. `backend/eval/evaluate.py` scores it
(answer accuracy + refusal correctness) and exits non-zero below the threshold.
The GitHub Actions workflow (`.github/workflows/eval.yml`) runs unit tests + the
eval on every PR, gating merges on quality. Swap in your own Q/A pairs once you
load your corpus.

> CI's eval job needs a `GROQ_API_KEY` repository secret
> (Settings → Secrets and variables → Actions) to call the LLM.

## Project layout
See [`CLAUDE.md`](./CLAUDE.md) for a full map. Backend details in
[`backend/README.md`](./backend/README.md).

## Roadmap (per the build plan)
- [x] Phase 1 — core pipeline (ingest → retrieve → cited generation) + API + UI
- [x] Phase 2 — hybrid retrieval, reranking, refusal logic, versioned prompts
- [x] Phase 3 — golden-set eval + CI gating
- [ ] Phase 4 (stretch) — local (Ollama) vs. free-tier (Groq) comparison write-up

---
*Built with free-tier APIs and local tools — no cost incurred.*
