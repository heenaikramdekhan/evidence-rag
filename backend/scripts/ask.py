"""CLI: ask the RAG system a question.

    python -m scripts.ask "What is the refund policy?"
    python -m scripts.ask            # interactive REPL
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.pipeline import answer_question  # noqa: E402


def _print(question: str) -> None:
    resp = answer_question(question)
    print("\n" + "=" * 70)
    print(resp.answer)
    print("-" * 70)
    if resp.citations:
        print("Citations:")
        for i, c in enumerate(resp.citations, start=1):
            preview = c.text[:120].replace("\n", " ")
            print(f"  [{i}] {c.source} (chunk {c.chunk_index}): {preview}...")
    print(f"({resp.latency_ms:.0f} ms, used_context={resp.used_context})")
    print("=" * 70 + "\n")


def main() -> None:
    # Answers/citations come from documents and may contain unicode the Windows
    # console (cp1252) can't encode — keep stdout from crashing on them.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # pragma: no cover  (very old Python)
        pass

    if len(sys.argv) > 1:
        _print(" ".join(sys.argv[1:]))
        return
    print("Evidence-RAG REPL. Ctrl-C to exit.")
    try:
        while True:
            q = input("\n> ").strip()
            if q:
                _print(q)
    except (KeyboardInterrupt, EOFError):
        print("\nbye")


if __name__ == "__main__":
    main()
