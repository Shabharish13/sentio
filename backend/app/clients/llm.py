from __future__ import annotations

from typing import Protocol

from app.clients.anthropic_client import AnthropicClient
from app.clients.cli_backend import ClaudeCliBackend
from app.config import get_settings


class LLMBackend(Protocol):
    """Anything that can turn a system+user prompt into a string."""

    def complete(self, system: str, user: str, max_tokens: int = ...) -> str: ...


class LLM:
    """Backend-agnostic LLM facade. Agents depend only on `.complete(...)`."""

    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        return self._backend.complete(system, user, max_tokens)


def get_llm() -> LLM:
    """Select the transport: SDK when an API key is present, else the CLI fallback."""
    if get_settings().anthropic_api_key:
        return LLM(AnthropicClient())
    return LLM(ClaudeCliBackend())
