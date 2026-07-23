"""CLI: inspect retrieval (hybrid + rerank) for a question — no LLM call.

    python -m scripts.retrieve "chain of custody signing"
    python -m scripts.retrieve "storage rules" --top-k 3

Shows the ranked chunks with their rerank scores, so you can judge retrieval
quality independently of the generation step.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline import retrieve_only  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", nargs="+", help="the query to retrieve for")
    ap.add_argument("--top-k", type=int, default=None, help="how many chunks to keep")
    args = ap.parse_args()

    resp = retrieve_only(" ".join(args.question), args.top_k)
    print("\n" + "=" * 72)
    print(f"Q: {resp.question}   ({resp.latency_ms:.0f} ms, no LLM)")
    print("=" * 72)
    if not resp.chunks:
        print("No chunks retrieved — is the corpus ingested?")
        return
    for rank, c in enumerate(resp.chunks, start=1):
        score = f"{c.score:.3f}" if c.score is not None else "n/a"
        preview = c.text[:160].replace("\n", " ")
        print(f"\n#{rank}  score={score}  {c.source} (chunk {c.chunk_index})")
        print(f"    {preview}...")
    print()


if __name__ == "__main__":
    main()
