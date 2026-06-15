# Sentio Agent Backend

Phase 1: foundation + API clients. Run from `backend/`:

    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt
    .venv/Scripts/python.exe -m pytest          # unit tests (no network)
    .venv/Scripts/python.exe -m uvicorn app.main:app --reload   # serve /health

Secrets load from `../api-tests/.env`. LLM model is pinned to `claude-sonnet-4-6`.
Clients: `app/clients/{anthropic,apollo,tavily,hubspot}_client.py`.
