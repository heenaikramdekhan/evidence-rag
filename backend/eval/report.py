"""Render the latest eval run as a Markdown table (for the README / PR comment).

    python -m eval.report > eval_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.generation.answer import REFUSAL  # noqa: E402
from app.pipeline import answer_question  # noqa: E402
from eval.evaluate import _overlap, load_golden  # noqa: E402


def main() -> None:
    # The report uses unicode (✅/❌); keep it printable when stdout is a
    # Windows console or a redirected file (both default to cp1252).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # pragma: no cover  (very old Python)
        pass

    rows = load_golden()
    print("# Evidence-RAG evaluation report\n")
    print("| Question | Expected | Result | Detail |")
    print("|---|---|---|---|")
    passed = 0
    for row in rows:
        resp = answer_question(row["question"], record=False)
        refused = REFUSAL.lower()[:30] in resp.answer.lower()
        if row.get("expect_refusal"):
            ok = refused
            detail = "refused"
            expected = "refusal"
        else:
            score = _overlap(resp.answer, row.get("ground_truth", ""))
            ok = (not refused) and score >= 0.34
            detail = f"overlap={score:.2f}"
            expected = "answer"
        passed += int(ok)
        q = row["question"].replace("|", "\\|")[:60]
        print(f"| {q} | {expected} | {'✅' if ok else '❌'} | {detail} |")
    if rows:
        print(f"\n**Score: {passed}/{len(rows)} = {passed / len(rows):.1%}**")


if __name__ == "__main__":
    main()
