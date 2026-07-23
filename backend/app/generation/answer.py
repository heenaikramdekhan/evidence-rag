"""Assemble the final answer: format context, call the LLM, map citations back
to their source chunks.
"""
from __future__ import annotations

from functools import lru_cache

import yaml

from ..config import get_settings
from ..schemas import Chunk, Citation
from .llm import get_llm

REFUSAL = "I don't have enough information in the provided sources to answer that."


@lru_cache
def _prompts() -> dict:
    with open(get_settings().prompts_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _format_context(chunks: list[Chunk]) -> str:
    """Render chunks as a numbered SOURCES block (1-indexed for the LLM)."""
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (from {c.source}, chunk {c.chunk_index})\n{c.text}")
    return "\n\n".join(blocks)


def generate_answer(question: str, chunks: list[Chunk]) -> tuple[str, list[Citation], bool]:
    """Return (answer_text, citations, used_context)."""
    if not chunks:
        return REFUSAL, [], False

    prompts = _prompts()
    context = _format_context(chunks)
    system = prompts["system"]
    user = prompts["user"].format(question=question, context=context)

    answer = get_llm().chat(system, user).strip()

    used_context = REFUSAL.lower()[:30] not in answer.lower()
    citations = _extract_citations(answer, chunks) if used_context else []
    return answer, citations, used_context


def _extract_citations(answer: str, chunks: list[Chunk]) -> list[Citation]:
    """Pull [n] markers from the answer and map them to the 1-indexed chunks."""
    import re

    cited_numbers = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
    citations: list[Citation] = []
    for n in sorted(cited_numbers):
        if 1 <= n <= len(chunks):
            c = chunks[n - 1]
            citations.append(
                Citation(
                    id=c.id,
                    source=c.source,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    score=c.score,
                )
            )
    # Fallback: if the model cited nothing parseable, surface the retrieved set
    # so the user can still verify provenance.
    if not citations:
        for c in chunks:
            citations.append(
                Citation(
                    id=c.id,
                    source=c.source,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    score=c.score,
                )
            )
    return citations
