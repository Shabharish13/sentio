from __future__ import annotations

from typing import Protocol

import anthropic
import openai

from app.clients.anthropic_client import AnthropicClient
from app.clients.cli_backend import ClaudeCliBackend, LLMError
from app.clients.openai_backend import OpenAIBackend
from app.config import get_settings

# Errors that mean "this backend is unavailable — try the next one".
_RECOVERABLE = (LLMError, openai.OpenAIError, anthropic.AnthropicError)


class LLMBackend(Protocol):
    """Anything that can turn a system+user prompt into a string."""

    def complete(self, system: str, user: str, max_tokens: int = ...) -> str: ...


class LLM:
    """Ordered chain of LLM backends with fall-through on provider errors."""

    def __init__(self, backends: list[LLMBackend]) -> None:
        if not backends:
            raise ValueError("LLM requires at least one backend")
        self._backends = backends

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        last_error: Exception | None = None
        for backend in self._backends:
            try:
                return backend.complete(system, user, max_tokens)
            except _RECOVERABLE as exc:
                last_error = exc
                continue
        raise LLMError(f"all LLM backends failed; last error: {last_error}")


def get_llm() -> LLM:
    """Build the backend chain by key precedence: OpenAI -> Anthropic -> claude CLI.

    The claude CLI is always the final fallback (works wherever Claude Code is
    logged in). A backend that errors at call time (e.g. OpenAI quota 429) falls
    through to the next backend automatically.
    """
    settings = get_settings()
    backends: list[LLMBackend] = []
    if settings.openai_api_key:
        backends.append(OpenAIBackend())
    if settings.anthropic_api_key:
        backends.append(AnthropicClient())
    backends.append(ClaudeCliBackend())
    return LLM(backends)
