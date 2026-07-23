"""LLM client abstraction over Groq (cloud free-tier) and Ollama (local).

Both providers expose a single ``chat(system, user)`` method so the rest of the
codebase is provider-agnostic. Selection is driven by ``LLM_PROVIDER``.
"""
from __future__ import annotations

from ..config import get_settings


class LLMError(RuntimeError):
    pass


class GroqClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise LLMError(
                "GROQ_API_KEY is not set. Add it to backend/.env or switch "
                "LLM_PROVIDER=ollama for fully offline generation."
            )
        from groq import Groq

        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.groq_model

    def chat(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
        )
        return resp.choices[0].message.content or ""


class OllamaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model

    def chat(self, system: str, user: str) -> str:
        import httpx

        try:
            resp = httpx.post(
                f"{self._base}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "options": {"temperature": 0.1},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=120,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(
                f"Ollama request failed ({exc}). Is `ollama serve` running and "
                f"has `{self._model}` been pulled?"
            ) from exc
        return resp.json()["message"]["content"]


def get_llm():
    provider = get_settings().llm_provider.lower()
    if provider == "groq":
        return GroqClient()
    if provider == "ollama":
        return OllamaClient()
    raise LLMError(f"Unknown LLM_PROVIDER: {provider!r} (use 'groq' or 'ollama')")
