from __future__ import annotations

import anthropic

from app.config import PROMPTS_DIR, get_settings


def load_prompt(name: str) -> str:
    """Read a system prompt markdown file from the repo `prompts/` dir."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


class AnthropicClient:
    """Thin wrapper over the official Anthropic SDK.

    The SDK client is injectable so tests can run against a mocked transport.
    Model defaults to the project-pinned claude-sonnet-4-6.
    """

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self._client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = model or settings.claude_model

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
