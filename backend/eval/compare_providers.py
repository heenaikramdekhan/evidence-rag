"""Phase 4 — local (Ollama) vs. free-tier (Groq) provider comparison.

Runs the golden set through each LLM provider *against the same retrieved
context* and scores them identically to ``eval/evaluate.py`` (answer accuracy +
refusal correctness), while also measuring end-to-end latency. The result is a
markdown report you can drop straight into the repo.

Only the generation step changes between providers — ingestion, retrieval, and
reranking are shared and deterministic, so any difference in the table is the
LLM's doing.

    # both providers (needs `ollama serve` + a pulled model for the local side)
    python -m eval.compare_providers

    # just one, or a custom output path
    python -m eval.compare_providers --providers groq
    python -m eval.compare_providers --out eval/provider_comparison.md

If a provider is unreachable (e.g. Ollama isn't running) it's reported as
*unavailable* instead of crashing the whole run.
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.generation.answer import REFUSAL  # noqa: E402
from app.pipeline import answer_question  # noqa: E402
from eval.evaluate import _overlap, load_golden  # noqa: E402

OUT_DEFAULT = Path(__file__).resolve().parent / "provider_comparison.md"
OVERLAP_THRESHOLD = 0.34


def _use_provider(name: str):
    """Point the pipeline at ``name`` and return the refreshed settings."""
    os.environ["LLM_PROVIDER"] = name
    get_settings.cache_clear()
    return get_settings()


def _model_for(name: str, settings) -> str:
    return settings.groq_model if name == "groq" else settings.ollama_model


def _score_row(row: dict, answer: str) -> tuple[bool, str]:
    """Mirror eval/evaluate.py scoring so the numbers are comparable."""
    refused = REFUSAL.lower()[:30] in answer.lower()
    if row.get("expect_refusal"):
        return refused, "refused" if refused else "should have refused"
    score = _overlap(answer, row.get("ground_truth", ""))
    ok = (not refused) and score >= OVERLAP_THRESHOLD
    return ok, f"overlap={score:.2f}"


def run_provider(name: str, rows: list[dict]) -> dict:
    settings = _use_provider(name)
    model = _model_for(name, settings)
    result: dict = {"provider": name, "model": model, "available": True,
                    "error": None, "rows": []}

    for row in rows:
        try:
            started = time.perf_counter()
            resp = answer_question(row["question"], record=False)
            latency_ms = (time.perf_counter() - started) * 1000
        except Exception as exc:  # noqa: BLE001  (LLMError, connection errors, ...)
            # First failing call almost always means the provider is unreachable
            # (Ollama not serving, key rejected, ...). Report, don't crash.
            result["available"] = False
            result["error"] = str(exc).splitlines()[0][:200]
            return result

        ok, detail = _score_row(row, resp.answer)
        result["rows"].append({
            "question": row["question"],
            "expect_refusal": bool(row.get("expect_refusal")),
            "ok": ok,
            "detail": detail,
            "latency_ms": round(latency_ms, 1),
        })

    _summarize(result)
    return result


def _summarize(result: dict) -> None:
    rows = result["rows"]
    in_scope = [r for r in rows if not r["expect_refusal"]]
    refusals = [r for r in rows if r["expect_refusal"]]
    latencies = [r["latency_ms"] for r in rows]

    result["accuracy"] = _rate(in_scope)
    result["refusal_acc"] = _rate(refusals)
    result["overall"] = _rate(rows)
    result["avg_latency_ms"] = round(statistics.mean(latencies), 1) if latencies else 0.0
    result["p50_latency_ms"] = round(statistics.median(latencies), 1) if latencies else 0.0


def _rate(rows: list[dict]) -> float:
    return sum(r["ok"] for r in rows) / len(rows) if rows else 0.0


def _pct(x: float) -> str:
    return f"{x:.0%}"


def build_report(results: list[dict]) -> str:
    live = [r for r in results if r["available"]]
    down = [r for r in results if not r["available"]]

    lines: list[str] = []
    lines.append("# Provider comparison — Groq (cloud) vs. Ollama (local)\n")
    lines.append(
        "Same corpus, same retrieval + reranking, same golden set — only the "
        "generation LLM changes. Scoring matches `eval/evaluate.py` "
        f"(in-scope answers need ≥{OVERLAP_THRESHOLD:.0%} ground-truth token "
        "overlap; out-of-scope questions must be refused).\n"
    )

    # --- summary table ---
    lines.append("## Summary\n")
    lines.append("| Provider | Model | Accuracy (in-scope) | Refusal | Overall | Avg latency | p50 latency |")
    lines.append("|----------|-------|--------------------:|--------:|--------:|------------:|------------:|")
    for r in live:
        lines.append(
            f"| {r['provider']} | `{r['model']}` | {_pct(r['accuracy'])} "
            f"| {_pct(r['refusal_acc'])} | {_pct(r['overall'])} "
            f"| {r['avg_latency_ms']:.0f} ms | {r['p50_latency_ms']:.0f} ms |"
        )
    for r in down:
        lines.append(
            f"| {r['provider']} | `{r['model']}` | — | — | — | — | — |"
        )
    lines.append("")

    for r in down:
        lines.append(
            f"> ⚠️ **{r['provider']} unavailable** — {r['error']}\n>\n"
            f"> Start it with `ollama serve` and `ollama pull {r['model']}`, "
            "then re-run `python -m eval.compare_providers`.\n"
        )

    # --- per-question detail ---
    for r in live:
        lines.append(f"## {r['provider']} — per question\n")
        lines.append("| Question | Type | Result | Detail | Latency |")
        lines.append("|----------|------|:------:|--------|--------:|")
        for row in r["rows"]:
            q = row["question"][:60] + ("…" if len(row["question"]) > 60 else "")
            typ = "refusal" if row["expect_refusal"] else "in-scope"
            mark = "✅" if row["ok"] else "❌"
            lines.append(
                f"| {q} | {typ} | {mark} | {row['detail']} | {row['latency_ms']:.0f} ms |"
            )
        lines.append("")

    # --- takeaways ---
    lines.append("## Takeaways\n")
    if len(live) >= 2:
        a, b = live[0], live[1]
        faster, slower = sorted(live, key=lambda x: x["avg_latency_ms"])[:2]
        speedup = slower["avg_latency_ms"] / faster["avg_latency_ms"] if faster["avg_latency_ms"] else 0
        lines.append(
            f"- **Latency:** `{faster['provider']}` averaged "
            f"{faster['avg_latency_ms']:.0f} ms vs `{slower['provider']}` at "
            f"{slower['avg_latency_ms']:.0f} ms (~{speedup:.1f}× faster)."
        )
        lines.append(
            f"- **Quality:** `{a['provider']}` scored {_pct(a['overall'])} overall "
            f"vs `{b['provider']}` at {_pct(b['overall'])} on the same golden set."
        )
    elif len(live) == 1:
        r = live[0]
        lines.append(
            f"- Only `{r['provider']}` ran: {_pct(r['overall'])} overall, "
            f"{r['avg_latency_ms']:.0f} ms average latency."
        )
    lines.append(
        "- **Cost:** both are $0 here — Groq on its free tier, Ollama fully "
        "local. Groq trades a network hop for a far larger model; Ollama trades "
        "model size for offline privacy and no rate limits."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--providers", nargs="+", default=["groq", "ollama"],
                    help="providers to compare (default: groq ollama)")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT,
                    help=f"markdown report path (default: {OUT_DEFAULT.name})")
    args = ap.parse_args()

    # The report uses unicode (≥, ✅) — keep it printable on Windows consoles.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:  # pragma: no cover  (very old Python)
        pass

    rows = load_golden()
    if not rows:
        print("No golden rows found. Fill in eval/golden_set.jsonl first.")
        sys.exit(1)

    results = [run_provider(p, rows) for p in args.providers]
    report = build_report(results)

    args.out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
