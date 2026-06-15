# Sentio Agent Backend

Phase 1: foundation + API clients. Run from `backend/`:

    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt
    .venv/Scripts/python.exe -m pytest          # unit tests (no network)
    .venv/Scripts/python.exe -m uvicorn app.main:app --reload   # serve /health

Secrets load from `../api-tests/.env`. LLM model is pinned to `claude-sonnet-4-6`.
Clients: `app/clients/{anthropic,apollo,tavily,hubspot}_client.py`.

LLM access goes through `app/clients/llm.py` → `get_llm().complete(system, user, max_tokens)`.
It uses the Anthropic API when `ANTHROPIC_API_KEY` is set, and falls back to the
logged-in `claude` CLI (headless `claude -p`) when it is not — so agents run locally
without a key. The CLI fallback only works where Claude Code is logged in (not CI/deploy)
and is slower/costlier per call. Agents should call `get_llm()`, not `AnthropicClient` directly.
