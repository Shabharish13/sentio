# AI-Assisted App Runner

Use this when a reviewer wants Codex or Claude to prepare and run the Sentio agentic marketing solution locally.

## Copy/Paste Prompt for Codex or Claude CLI

Run this from the repository root:

```text
You are in the Sentio agentic marketing solution repository.

Goal: check local dependencies, prepare the app if needed, and start both backend and frontend so I can test the demo form and Sage chat in the browser.

Please do the following:

1. Confirm the current directory is the repository root by checking for `backend/`, `frontend/`, `kb/`, `api-tests/`, and `Hiring-Team-Handover.md`.
2. Check that Python 3.11+, Node.js, and npm are available.
3. If Python or Node is missing, stop and tell me exactly what to install on macOS. Do not attempt destructive system changes.
4. Check whether `api-tests/.env` exists.
   - If it does not exist, copy `api-tests/.env.example` to `api-tests/.env`, then stop and ask me to fill in the API keys before continuing.
   - If it exists, continue without printing secrets.
5. Prepare the backend:
   - If `backend/.venv` does not exist, create it with `python3 -m venv backend/.venv`.
   - Install backend dependencies with `backend/.venv/bin/python -m pip install -r backend/requirements.txt`.
   - Build the Sage knowledge-base index with `cd backend && .venv/bin/python -m scripts.build_kb_index`.
6. Prepare the frontend:
   - If `frontend/node_modules` does not exist, run `npm install` from `frontend/`.
7. Run a quick non-network verification:
   - From `backend/`, run `.venv/bin/python -m pytest`.
   - From `frontend/`, run `npm run lint`.
   - If tests or lint fail, summarize the failure and continue only if the servers can still run.
8. Start the backend:
   - Prefer port `8000`: `cd backend && .venv/bin/python -m uvicorn app.main:app --port 8000`.
   - If port `8000` is busy, choose the next open port and remember it as the backend URL.
9. Start the frontend:
   - Prefer port `3000`.
   - Set `NEXT_PUBLIC_API_BASE` to the backend URL before starting Next.js.
   - From `frontend/`, run `npm run dev`.
   - If port `3000` is busy, use the next available frontend port.
10. Keep both servers running and report:
   - Backend URL.
   - Swagger URL.
   - Frontend URL.
   - Any skipped checks.
   - Whether the app is ready for browser testing.

Important:

- Do not print API secrets.
- Do not submit demo forms or chat booking flows unless I explicitly ask, because those can write real HubSpot records and spend API credits.
- Prefer cached test prospects from `Hiring-Team-Handover.md` when I ask for test data.
- If you need approval to install dependencies or run long-lived dev servers, ask for it clearly.
```

## Expected Result

The AI assistant should leave two local servers running:

| Service | Default URL |
|---|---|
| Backend | `http://localhost:8000` |
| Swagger | `http://localhost:8000/docs` |
| Frontend | `http://localhost:3000` |

Once those are running, use the cached test prospects in `Hiring-Team-Handover.md` to test the demo form and Sage chat flows.

