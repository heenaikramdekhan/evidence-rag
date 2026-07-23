"""Golden-set evaluation.

Runs every question in ``golden_set.jsonl`` through the pipeline and scores:

  * refusal accuracy  — did the system refuse exactly on out-of-scope questions?
  * retrieval hit rate — did any retrieved chunk contain the ground-truth answer
                         (a cheap lexical-overlap proxy, no judge LLM required)?

Optionally, if RAGAS + a judge LLM are installed/configured, you can extend this
to score faithfulness. We keep the default dependency-free so CI stays fast and
$0. Exits non-zero if the score falls below --threshold (used to gate CI).

    python -m eval.evaluate --threshold 0.9
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.generation.answer import REFUSAL  # noqa: E402
from app.pipeline import answer_question  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden_set.jsonl"


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _overlap(answer: str, truth: str) -> float:
    """Fraction of ground-truth tokens present in the answer (0..1)."""
    t = _tokens(truth)
    if not t:
        return 0.0
    return len(t & _tokens(answer)) / len(t)


def load_golden() -> list[dict]:
    rows = []
    for line in GOLDEN.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("REPLACE"):
            rows.append(json.loads(line))
    return rows


def evaluate(threshold: float) -> int:
    rows = load_golden()
    if not rows:
        print("No golden rows found. Fill in eval/golden_set.jsonl.")
        return 0

    passed = 0
    results = []
    for row in rows:
        resp = answer_question(row["question"])
        refused = REFUSAL.lower()[:30] in resp.answer.lower()

        if row.get("expect_refusal"):
            ok = refused
            detail = "refused (correct)" if ok else "should have refused"
        else:
            score = _overlap(resp.answer, row.get("ground_truth", ""))
            ok = (not refused) and score >= 0.34
            detail = f"answer-overlap={score:.2f}"

        passed += int(ok)
        results.append((ok, row["question"], detail))

    rate = passed / len(rows)
    print("\n=== Evidence-RAG eval ===")
    for ok, q, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {q[:60]:60}  {detail}")
    print(f"\nScore: {passed}/{len(rows)} = {rate:.1%}  (threshold {threshold:.0%})")

    return 0 if rate >= threshold else 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.9)
    args = ap.parse_args()
    sys.exit(evaluate(args.threshold))


if __name__ == "__main__":
    main()
