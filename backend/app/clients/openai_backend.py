from __future__ import annotations

import openai

from app.clients.cli_backend import LLMError
from app.config import get_settings

# gpt-5 is a reasoning model: reasoning tokens count against max_completion_tokens.
# On real prompts it spends ~1000 tokens reasoning *before* emitting any content, so
# a small budget (e.g. 300-400) is consumed entirely by reasoning and content comes
# back empty -> LLMError -> silent fall-through to the slow CLI. The caller's
# max_tokens is the desired *content* budget; we add this headroom so reasoning has
# room and content still fits. (Ignored by non-reasoning models, which just cap higher.)
REASONING_HEADROOM = 1536


class OpenAIBackend:
    """LLM transport using the OpenAI Chat Completions API (default model gpt-5).

    Primary backend when OPENAI_API_KEY is set. Provider failures
    (quota/auth/rate/connection) propagate as `openai.OpenAIError` so the LLM
    facade can fall through to the next backend in the chain.
    """

    def __init__(
        self,
        client: openai.OpenAI | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        # max_retries=0: fail fast so a quota/rate error falls through to the
        # fallback backend instead of retrying with backoff first.
        self._client = client or openai.OpenAI(
            api_key=settings.openai_api_key, max_retries=0
        )
        self._model = model or settings.openai_model

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 reasoning_effort: str | None = None) -> str:
        # reasoning_effort (e.g. "minimal") lets callers trade reasoning depth for
        # latency on calls that don't need deep reasoning — the conversational Sage
        # reply uses "minimal"; action-deciding agents keep the model default.
        extra = {"reasoning_effort": reasoning_effort} if reasoning_effort else {}
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=max_tokens + REASONING_HEADROOM,
            **extra,
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI returned empty content")
        return content
