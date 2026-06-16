# Sentio Agent Backend

Phase 1: foundation + API clients. Run from `backend/`:

    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt
    .venv/Scripts/python.exe -m pytest          # unit tests (no network)
    .venv/Scripts/python.exe -m uvicorn app.main:app --reload   # serve /health

Secrets load from `../api-tests/.env`. LLM model is pinned to `claude-sonnet-4-6`.
Clients: `app/clients/{anthropic,apollo,tavily,hubspot}_client.py`.

LLM access goes through `app/clients/llm.py` → `get_llm().complete(system, user, max_tokens)`.
`get_llm()` builds an ordered backend chain by key precedence and falls through on
provider errors (e.g. an OpenAI quota 429 transparently routes to the next backend):

1. **OpenAI** (`OPENAI_API_KEY`) — primary, flagship model `gpt-5` (`OPENAI_MODEL` to override)
2. **Anthropic** (`ANTHROPIC_API_KEY`) — `claude-sonnet-4-6`
3. **claude CLI** (headless `claude -p`) — always-present final fallback; uses the
   logged-in Claude Code session, so agents run locally even with no LLM key.

The CLI fallback only works where Claude Code is logged in (not CI/deploy) and is
slower/costlier per call. Agents should call `get_llm()`, never a concrete backend.
