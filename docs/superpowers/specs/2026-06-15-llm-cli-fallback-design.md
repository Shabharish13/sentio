# LLM CLI Fallback — Design

## Problem

The agents call Claude through `AnthropicClient`, which requires `ANTHROPIC_API_KEY`. In local/demo runs that key is often absent, but the machine is already logged into Claude Code (the `claude` CLI is authenticated). We want the agents to fall back to that logged-in session when no API key is present, with **no change to agent code**.

## Decision

A single backend-agnostic interface, `LLM.complete(system, user, max_tokens) -> str`, selects its transport **once at construction**:

- **`ANTHROPIC_API_KEY` present → SDK transport** (preferred). Delegates to the existing `AnthropicClient` (official `anthropic` SDK, model `claude-sonnet-4-6`). Unchanged behaviour.
- **`ANTHROPIC_API_KEY` absent → CLI transport.** Shells out to the logged-in `claude` CLI in headless mode and parses the result.

Agents (Phase 3) depend only on `LLM.complete`; they never know which transport ran.

> Verified working in this session: `claude -p "..." --model claude-sonnet-4-6 --output-format json` returns `{"...","result":"ok",...}` using the logged-in account, no API key.

## Components

### `app/clients/cli_backend.py` — `ClaudeCliBackend`

- `complete(system, user, max_tokens) -> str`.
- Builds argv: `["claude", "-p", user, "--system-prompt", system, "--model", settings.claude_model, "--output-format", "json", "--max-turns", "1"]`. `--max-turns 1` caps the nested session at a single model turn, so it cannot run a tool-use loop and behaves as a one-shot completion. (`--system-prompt` replaces the default session prompt so our agent prompt is the only instruction — to be confirmed with a real headless call during implementation.)
- Runs it via an **injectable runner** `runner: Callable[[list[str]], str]` (default: a thin `subprocess.run` wrapper returning stdout). Tests stub the runner — no real `claude` call.
- Parses stdout JSON; returns the `result` field.
- `max_tokens` is accepted for interface parity. (The CLI has no direct per-call max-output flag in the headless surface we use; it is documented as best-effort/ignored rather than silently implying enforcement.)

### `app/clients/llm.py` — `LLM` facade + `get_llm()` factory

- `LLM` wraps one backend object exposing `complete(system, user, max_tokens) -> str`.
- `get_llm() -> LLM`: reads `get_settings()`; if `anthropic_api_key` is non-empty → wrap `AnthropicClient()`; else → wrap `ClaudeCliBackend()`.
- `AnthropicClient` already satisfies the `complete` signature, so it is used directly as the SDK backend (no adapter needed).

### `app/clients/anthropic_client.py` — unchanged

Stays the SDK transport. `load_prompt` stays here.

## Data flow

```
agent → LLM.complete(system, user, max_tokens)
          └─ SDK backend  → anthropic SDK → claude-sonnet-4-6      (key present)
          └─ CLI backend  → claude -p ... --output-format json     (key absent)
                              → parse .result → str
```

## Error handling — `LLMError`

A new `LLMError(RuntimeError)` raised by the CLI backend when:
- the runner exits non-zero (include captured stderr/stdout in the message), or
- stdout is not valid JSON, or
- the JSON has `is_error: true` (include `api_error_status` / `subtype`), or
- the `result` field is missing.

The SDK backend continues to surface the SDK's own typed exceptions (unchanged).

## Testing

All unit tests stub external calls — no real `claude` process, no network.

- `get_llm` selects the SDK backend when `ANTHROPIC_API_KEY` is set (monkeypatch a non-empty key), and the CLI backend when it is empty.
- `ClaudeCliBackend.complete` with a stub runner returning a success JSON blob returns `"ok"` and builds argv containing `-p`, the user text, `--system-prompt`, the system text, `--model claude-sonnet-4-6`, `--output-format json`.
- `ClaudeCliBackend.complete` raises `LLMError` when the runner returns `{"is_error": true, ...}`, and when stdout is non-JSON.

## Out of scope

- Streaming, tool use, or multi-turn through the CLI (single-shot only).
- Making the CLI fallback work in deployed/CI environments — it only works where the `claude` CLI is logged in. The API key remains the path for non-interactive deployment.
- Changing any agent code (agents don't exist yet; this just shapes the interface they'll use in Phase 3).
