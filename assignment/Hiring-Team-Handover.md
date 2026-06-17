# Agentic Marketing Solution for Sentio - Hiring Team Handover

This document explains how to run the app locally and test the important flows. The primary path is AI-assisted setup with Codex or Claude CLI; manual macOS setup is included as a fallback.

## Repository Map

| Path | Purpose |
|---|---|
| `frontend/` | Next.js Sentio website and Sage widget |
| `backend/` | FastAPI backend, agents, scoring, chat orchestration |
| `prompts/` | Agent system prompts |
| `kb/` | Product knowledge base used by Sage RAG |
| `backend/app/scoring/data/` | CSV scoring weights and thresholds |
| `api-tests/` | Environment template, curl notes, smoke-test helper |
| `cache/apollo/` | Local Apollo response cache to avoid repeat API spend |
| `AI-Run-App.md` | Copy/paste AI runner prompt for Codex or Claude CLI |

## Prerequisites

- macOS with a `bash` or `zsh` terminal.
- Python 3.11+.
- Node.js and npm.
- API keys in `api-tests/.env`, copied from `api-tests/.env.example`.

If Python or Node is missing on macOS:

```bash
brew install python node
```

Required for full end-to-end runs:

- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, or a logged-in `claude` CLI fallback.
- `APOLLO_API_KEY`.
- `TAVILY_API_KEY`.
- `HUBSPOT_TOKEN`.

HubSpot constants are already defaulted in code and included in `.env.example`:

- Pipeline: `default`
- Demo requested stage: `3832955632`
- Disqualified stage: `3840698071`

## Primary Setup: AI-Assisted

For the fastest reviewer experience, open Codex or Claude CLI from the repository root and paste the prompt from [AI-Run-App.md](AI-Run-App.md).

The AI-assisted runner will:

- Check Python, Node.js, and npm.
- Create the backend virtual environment if needed.
- Install backend and frontend dependencies if needed.
- Build the Sage knowledge-base index.
- Run quick backend/frontend checks.
- Start the backend and frontend.
- Return the local URLs for testing.

Copy/paste this prompt into Codex or Claude CLI after opening it from the repository root:

```text
Read `AI-Run-App.md` and execute the "Copy/Paste Prompt for Codex or Claude CLI" section. Check dependencies, prepare the backend and frontend, start both local servers, and return the frontend, backend, and Swagger URLs. Do not print secrets or submit live demo/chat flows unless I explicitly ask.
```

The full operational prompt lives in [AI-Run-App.md](AI-Run-App.md) so the reviewer can also open that file and paste the longer version directly.

## Alternative Setup: Manual macOS

```bash
cp api-tests/.env.example api-tests/.env
```

Fill in real keys in `api-tests/.env`.

Backend setup, from repository root:

```bash
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m scripts.build_kb_index
```

Frontend setup, from repository root:

```bash
cd frontend
npm install
```

## Alternative Run: Manual macOS

Terminal 1, backend:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --port 8000
```

Backend URL:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

Terminal 2, frontend:

```bash
cd frontend
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

The frontend defaults to `http://localhost:8000` for the backend. To override:

```bash
export NEXT_PUBLIC_API_BASE="http://localhost:8000"
npm run dev
```

## Important Resource Warning

The browser demo form and terminal chat outcomes use real integrations.

- Apollo enrichment is on the free tier and restricted to company enrichment. Hence, the demo form collects the prospect's job title. 
- Tavily and LLM calls can spend tokens/searches. Tavily has aound 800 free credits remaining.
- HubSpot writes real contacts, deals, and notes.

## Scoring Logic Reference

The ICP fit score is deterministic and comes from `backend/app/scoring/data/`. Maximum fit score is 95 points.

| Dimension | Parameter | Points |
|---|---|---:|
| Headcount | 51-99 employees | 10 |
| Headcount | 100-300 employees | 25 |
| Headcount | 301-800 employees | 20 |
| Headcount | 801-2,000 employees | 5 |
| Headcount | 2,001+ employees | 0 |
| Industry | Computer Software | 20 |
| Industry | Internet | 18 |
| Industry | Information Technology and Services | 15 |
| Industry | Financial Services with SaaS/API/platform signal | 15 |
| Industry | Human Resources | 12 |
| Industry | Marketing and Advertising | 12 |
| Industry | Telecommunications or E-learning | 5 |
| Industry | Financial Services without SaaS signal | 5 |
| Title | VP/Head of Customer Success | 20 |
| Title | Director of Customer Success | 18 |
| Title | CS Ops / Customer Success Operations | 17 |
| Title | CRO / Chief Revenue Officer | 15 |
| Title | CFO / VP Finance | 12 |
| Title | RevOps leadership | 12 |
| Title | Customer Success Manager / CS lead | 8 |
| Title | Senior CSM, AE, SDR, or similar end-user title | 3 |
| Title | CTO / VP Engineering / Head of IT | 0 |
| Title | CEO / Founder | 0 |
| Geography | United States | 15 |
| Geography | Canada or United Kingdom | 12 |
| Geography | Australia or New Zealand | 10 |
| Geography | Priority Western Europe markets | 7 |
| Business model | B2B signal present | 10 |
| Business model | SaaS signal present | 5 |

Grade thresholds:

- A: 60+ points.
- B: 30-59 points.
- C: below 30 points.

## Cached Test Prospects

Use these prospects for repeatable browser and API tests. Their person and organization records are already present in `cache/apollo/`, so using the same email/domain should avoid additional Apollo spend.

| Email | Prospect | Company | Expected grade | Fit score | Expected route | Score breakdown | Best test flow |
|---|---|---|---|---:|---|---|---|
| `marcus.wong@nimbuscs.io` | Marcus Wong, VP of Customer Success | NimbusCS | A | 95 | `qualified` | Headcount 25, industry 20, title 20, geography 15, business model 15 | Strong qualified demo request or Sage book flow |
| `claire.hassan@leapfroganalytics.co.uk` | Claire Hassan, Customer Success Manager | Leapfrog Analytics | B | 52 | `qualified` | Headcount 10, industry 12, title 8, geography 12, business model 10 | Lower-priority but still qualified lead |
| `raj.pillai@vertexhr.com` | Raj Pillai, VP of Revenue Operations | VertexHR Corp | B | 54 | `edge_fit` | Headcount 5, industry 12, title 12, geography 15, business model 10 | Edge-fit lead above the 800-employee sweet spot |
| `priya.sharma@harborviewfreight.com` | Priya Sharma, Marketing Manager | Harborview Freight | C | 10 | `disqualified` | Headcount 0, industry 0, title 0, geography 0, business model 10 | Disqualification path with reason note |

Suggested form fields:

- Use the prospect's first name, last name, email, company, and title from the table.
- Use `surprise churn` or `health-score visibility` as the problem for qualified tests.
- For the C-grade test, keep the Harborview Freight company/title values so the disqualification remains reproducible.

## Automated Checks

Run backend tests:

```bash
cd backend
.venv/bin/python -m pytest
```

Run frontend lint:

```bash
cd frontend
npm run lint
```

## Offline / Low-Cost CLI Tests

These are useful before testing the browser.

Deterministic scoring only, no LLM:

```bash
cd backend
.venv/bin/python -m scripts.cli score --headcount 220 --industry "Computer Software" --title "VP of Customer Success" --country "United States" --b2b --problem "surprise churn"
```

Expected:

- Fit grade A.
- Fit score should be 95 for this example: headcount 25, industry 20, title 20, geography 15, B2B 10, SaaS 5.
- Route `qualified`.
- Score breakdown printed.

Dry-run full inbound pipeline, no Apollo, no HubSpot write:

```bash
.venv/bin/python -m scripts.cli pipeline --email marcus.wong@nimbuscs.io --first-name Marcus --last-name Wong --company "NimbusCS" --title "VP of Customer Success" --size "201-500" --problem "surprise churn" --industry "Computer Software" --headcount 180 --country "United States" --tech Salesforce Segment --how-heard "Website"
```

Expected:

- Route `qualified`.
- Fit score should be 95 with the same breakdown as the scoring-only test.
- Research signal printed if found.
- Draft email printed.
- HubSpot operations shown as `[dry-run]`.

Sage RAG answer:

```bash
.venv/bin/python -m scripts.cli sage "What are your pricing tiers?" --page /pricing
```

Expected:

- Sentio pricing answer grounded in KB.
- `redirected=False`.
- Source list printed.

## Browser Flow Tests

Open:

```text
http://localhost:3000
```

### Flow 1: Demo Form, Qualified Lead

Go to `/demo` and submit:

- First name: Marcus
- Last name: Wong
- Work email: `marcus.wong@nimbuscs.io`
- Company: NimbusCS
- Job title: VP of Customer Success
- Company size: 201-500
- Problem: surprise churn or health-score visibility

This address/domain has a local Apollo cache entry, so repeat tests should avoid additional Apollo spend.

Expected:

- Browser shows a "Request received" confirmation screen. The full pipeline runs in the background.
- HubSpot deal is in demo-requested stage (stage `3832955632`).
- HubSpot deal note contains: fit grade A, score breakdown (100-300 employee sweet spot, Computer Software, VP Customer Success, United States, B2B/SaaS), research signal, and SDR draft email.

### Flow 2: Demo Form, Disqualified Lead

Go to `/demo` and submit:

- Work email: valid email.
- Company size: 1-10.
- Job title: Student or Office Manager.
- Problem: not related to CS/churn.

Expected:

- Browser shows the same "Request received" confirmation (the visitor always sees a clean screen).
- HubSpot deal is in disqualified stage (stage `3840698071`).
- HubSpot note explains why: failed ICP dimensions, no draft email generated.

### Flow 3: Demo Form, Invalid Email

Submit `/demo` with:

```text
not-an-email
```

Expected:

- Backend returns HTTP 400.
- Frontend shows a generic failure message.
- No CRM write should happen.

### Flow 4: Sage Grounded Q&A

Open Sage and ask:

```text
What are your pricing tiers?
```

Expected:

- Sage answers from the KB.
- Sage asks one qualifying question in a separate bubble.
- No sales handoff occurs yet.

### Flow 5: Sage Book

Ask:

```text
I'm VP of Customer Success at a 200-person B2B SaaS company. We're fighting surprise churn and evaluating tools this quarter.
```

When Sage asks for email, reply with a work email:

```text
marcus.wong@nimbuscs.io
```

Expected:

- Sage confirms the team will reach out to set up the demo.
- Response returns quickly because CRM work is scheduled in the background.
- HubSpot receives a demo-requested deal.
- Chat transcript and collected signals are attached.
- The booked chat lead runs through the same inbound enrichment/scoring/research pipeline.

### Flow 6: Sage Escalate

Ask:

```text
I need custom enterprise pricing, security review, and procurement support.
```

When asked, provide an email.

Expected:

- Sage asks for email before claiming handoff.
- HubSpot receives a high-priority sales handoff note.
- The transcript explains the enterprise/security request.

### Flow 7: Sage Disqualify

Ask:

```text
It's just me, pre-revenue, and I do not have a customer success team.
```

Expected:

- Sage closes warmly.
- If email is captured or available, HubSpot receives a disqualified deal with reason and transcript.
- Sage does not push aggressively for an email on a clear non-fit.

### Flow 8: Off-Topic Question

Ask:

```text
What is the gold price in Chennai today?
```

Expected:

- Sage should not invent an answer.
- Sage should redirect back to Sentio/product help or ask for email only if the classifier detects a legitimate handoff need.

## API Endpoints

Health:

```text
GET /health
```

Demo form:

```text
POST /demo
```

Payload:

```json
{
  "first_name": "Marcus",
  "last_name": "Wong",
  "work_email": "marcus.wong@nimbuscs.io",
  "company_name": "NimbusCS",
  "job_title": "VP of Customer Success",
  "company_size": "201-500",
  "problem_stated": "surprise churn",
  "how_heard": "Website"
}
```

Chat:

```text
POST /chat
```

Payload:

```json
{
  "message": "What are your pricing tiers?",
  "page": "/pricing",
  "session_id": null
}
```

Reuse the returned `session_id` for multi-turn chat.

## What to Verify in HubSpot

- Contact is deduped by email.
- Repeated submissions update the same deal path rather than creating duplicates.
- Qualified/booked leads go to demo-requested stage.
- Disqualified leads go to disqualified stage.
- Every deal has a note.
- Qualified notes include score, persona, research signal, and draft email.
- Chat notes include transcript and collected signals.

## Known Trade-Offs

- The chat "book demo" flow creates a sales handoff/demo-requested deal; it does not select a live calendar slot.
- Full outbound personalization and stale-lead reactivation are not implemented as separate workflows.
- Browser form tests with real emails may spend Apollo credits and create HubSpot records.
- RAG answers depend on the local KB index; rebuild it after KB edits.
