from __future__ import annotations

import json
import subprocess
from typing import Callable

from app.config import get_settings


class LLMError(RuntimeError):
    """Raised when an LLM transport fails to produce a usable result."""


def _default_runner(args: list[str]) -> str:
    """Run the claude CLI and return stdout, raising LLMError on failure.

    `encoding="utf-8"` is mandatory: the CLI emits UTF-8 JSON, but text-mode
    subprocess decoding otherwise defaults to the locale codec (cp1252 on Windows),
    which turns UTF-8 punctuation into mojibake (the classic `a-circumflex` bug).
    """
    proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip()
        raise LLMError(f"claude CLI exited {proc.returncode}: {detail}")
    return proc.stdout


class ClaudeCliBackend:
    """LLM transport that shells out to the logged-in `claude` CLI (headless).

    Fallback used when no ANTHROPIC_API_KEY is set: it reuses the Claude Code
    session login. Single-shot only (`--max-turns 1`). The `runner` is injectable
    so tests never spawn a real `claude` process.
    """

    def __init__(
        self,
        runner: Callable[[list[str]], str] | None = None,
        model: str | None = None,
    ) -> None:
        self._runner = runner or _default_runner
        self._model = model or get_settings().claude_model

    def complete(self, system: str, user: str, max_tokens: int = 1024,
                 reasoning_effort: str | None = None) -> str:
        # max_tokens / reasoning_effort are accepted for interface parity with the
        # SDK backend; the headless CLI surface exposes neither, so they are ignored.
        args = [
            "claude",
            "-p",
            user,
            "--system-prompt",
            system,
            "--model",
            self._model,
            "--output-format",
            "json",
            "--max-turns",
            "1",
            # These are pure text-generation calls. Disable all tools so the model
            # answers directly instead of attempting a tool call (e.g. web search),
            # which would consume the single allowed turn and fail as max_turns.
            "--tools",
            "",
        ]
        raw = self._runner(args)
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMError(f"claude CLI returned non-JSON output: {raw[:200]!r}") from exc
        if data.get("is_error"):
            raise LLMError(
                f"claude CLI error (status={data.get('api_error_status')}, "
                f"subtype={data.get('subtype')})"
            )
        result = data.get("result")
        if result is None:
            raise LLMError(f"claude CLI response missing 'result': {raw[:200]!r}")
        return result
