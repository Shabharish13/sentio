# Sentio — Manual Test Plan

End-to-end test guide for the form path (`/demo`) and chat path (Sage widget).

## Run the servers

| Service | Command (from) | URL |
|---|---|---|
| Backend (FastAPI) | `backend/` → `.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000` | http://localhost:8000 |
| Frontend (Next.js) | `frontend/` → `npm run dev` | http://localhost:3000 |
| API docs (Swagger) | — | http://localhost:8000/docs |

> Node isn't on PATH by default here. In PowerShell first run:
> `$env:Path = "C:\Program Files\nodejs;" + $env:Path`

## ⚠️ What spends real resources

The web `/demo` and chat **Book/Disqualify** paths use the **real** clients — no dry-run:

- Every `/demo` submit writes a **real HubSpot deal** and spends an **Apollo credit**
  (cache-first, so repeating the *same email domain* costs nothing).
- Tavily + OpenAI tokens are used during research.
- Clean up test deals in HubSpot afterward.

For **cheap, controlled branch testing** (offline scoring, HubSpot dry-run by default),
use the CLI / slash commands instead: `/sentio-score`, `/sentio-sage`,
`/sentio-research`, or `backend/scripts/cli.py`.

---

## Form path — `/demo`

| # | Flow | Input | Expect |
|---|---|---|---|
| 1 | Qualified (A/B) | Real mid-market SaaS work email · title "VP of Customer Success" · size 201–500 · problem "surprise churn" | route=qualified · research signal · **draft email** · HubSpot deal in demo-requested stage (`3832955632`) |
| 2 | Disqualified (C) | Tiny company · size 1–10 · off-ICP title (e.g. "Student" / "Office Manager") | route=disqualified · **reason** shown · deal in disqualified stage (`3840698071`) · no email draft |
| 3 | Exit check | `work_email` = `not-an-email` | "Something went wrong. Please try again." (HTTP 400) |
| 4 | Dedupe | Submit the **same email twice** | Same HubSpot deal updated — no duplicate |

Lead Brief should render: scorecard (fit grade / fit score / intent / routing),
contact panel, company panel, research signal, draft email (qualified) or
disqualification reason, and `Synced to HubSpot · ref {id}`.

---

## Chat path — Sage widget

Widget is bottom-right on every page; auto-opens after 5s on `/pricing` and `/demo`.

| # | Flow | Say | Expect |
|---|---|---|---|
| 5 | Grounded Q&A | "What are your pricing tiers?" | Accurate answer citing the KB, then **one** qualifying question; not escalated |
| 6 | Off-topic escalate | "Write me a poem about cats" | Escalation message; no sources |
| 7 | Escalate to human | "I need custom enterprise pricing and a security review" | escalate outcome |
| 8 | **Book** | "I'm VP of CS at a 200-person SaaS, fighting surprise churn, evaluating this quarter" → give a work email when asked | "Demo booked" confirmation · HubSpot deal (demo-requested) with **transcript note** |
| 9 | **Disqualify** | "It's just me, pre-revenue side project, no CS team" → give an email | Warm close · disqualified deal + **reason** note |
| 10 | Continuity | Multi-turn conversation | Context carried across turns (same `session_id`) |

---

## Verify in HubSpot

- Deal stage matches the outcome (demo-requested vs disqualified).
- Contact deduped by email (no duplicate contacts/deals on repeat).
- **Every deal has a note** — qualified = SDR hand-off (+ chat transcript on the
  chat path); disqualified = mandatory reason.

## Expected outcomes reference

- Pipeline / stages: `Solution-Design-Document.md`
- ICP scoring weights & thresholds: `backend/app/scoring/data/*.csv`, `sentio-company-profile.md`
- Known bugs already fixed: `ITERATION-LOG.md`
