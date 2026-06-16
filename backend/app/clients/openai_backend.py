from __future__ import annotations

import openai

from app.clients.cli_backend import LLMError
from app.config import get_settings


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

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMError("OpenAI returned empty content")
        return content
