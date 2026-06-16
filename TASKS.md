# Build Task List — Sentio Agentic Marketing Tool

Build order is **backend-first**: agents + API integrations built and tested in isolation, then the website and chat widget on top. Due **17 June 2026, 10:00 PM IST**.

Legend: `[x]` done · `[ ]` to do · `[~]` partial / build delta

---

## Done — design & content (no code yet)

- [x] **Solution Design Document** — `Solution-Design-Document.md`, aligned to the build
- [x] **Company profile** — `sentio-company-profile.md` (ICP weights, personas, intent triggers, pricing)
- [x] **Knowledge base** — 11 markdown files in `kb/` (product, pricing, security, ROI, competitors, onboarding, integrations, 2 case studies, FAQ/objections)
- [x] **Website copy spec** — `website-copy.md` (verbatim copy for all pages + widget)
- [x] **Agent prompts** — `prompts/research_agent.md`, `copywriter_agent.md`, `crm_agent.md`, `sage_agent.md`
- [x] **API connectivity verified** — `api-tests/` (cURL reference + smoke test). Apollo, Tavily, HubSpot (Service Key) all return 200 against live APIs. Anthropic deferred.
- [x] **Key decisions locked:**
  - Four named agents: Research, Copywriter, CRM, Sage
  - Deterministic scoring by code (CSV), LLM only after scoring
  - Apollo cache-first (skip API on email hit)
  - CRM upsert by email (no duplicates on repeat bookings)
  - Disqualified leads → disqualified stage + mandatory reason notes
  - Tavily for supplemental research (replaced Brave)
  - Sage on all pages, page-aware; enrich→score→research fires after email capture

---

## Phase 1 — Backend foundation & API integrations

- [x] FastAPI project scaffold (`backend/`), config + `.env` loading, dependency setup
- [x] Secrets/keys wired: Anthropic, Apollo, Tavily, HubSpot
- [x] **Anthropic client** — `claude-sonnet-4-6`, shared prompt-loading helper (reads `prompts/*.md`)
- [x] **Apollo integration** — people + org enrichment, **response cache to local JSON**, cache-first lookup by email
- [x] **Tavily integration** — search client, capped at 3 calls per research run
- [x] **HubSpot integration** — contact + deal upsert, note attach, stage setters (pipeline `default`; qualified `3832955632`; disqualified `3840698071`)
- [x] Tests: each integration mocked + one live smoke test per provider (mind free-tier limits)

## Phase 2 — Deterministic scoring engine

- [x] ICP scoring CSV built from `sentio-company-profile.md` (weights as data)
- [x] Fit-score calculator (headcount, industry, title, geography, business model) → A/B/C grade
- [x] Industry disambiguation (Financial Services → Apollo `technologies`, Tavily fallback) — *Tavily-fallback path deferred to Phase 3/4 enrichment; code uses the `technologies` field*
- [x] Intent score from available signal (thin for form, richer for chat) — *form-path rubric done; chat-path intent is Phase 3 (Sage)*
- [x] Routing / exit gate (C-grade → disqualified path; A/B → research/email path)
- [x] Tests: known-input fixtures → expected grade/score (deterministic, reproducible)

## Phase 3 — The agents (backend)

- [x] **Research Agent** — Apollo-first signal mining, capped Tavily loop, JSON brief output (`app/agents/research.py`)
- [x] **Copywriter Agent** — stakeholder-framed email + SDR notes, sourced-facts-only guardrails (`app/agents/copywriter.py`)
- [x] **CRM Agent** — HubSpot upsert, stage-by-outcome, mandatory notes (qualified + disqualified) (`app/agents/crm.py`)
- [x] **Sage Agent** — RAG-grounded chat: KB retrieval + confidence-gated escalation (threshold recalibrated to 0.35 for MiniLM) (`app/agents/sage.py`)
  - [x] RAG setup: ChromaDB default MiniLM (all-MiniLM-L6-v2, no torch) over `kb/*.md` (`app/rag/store.py` + `scripts/build_kb_index.py`)
  - [x] Post-email-capture hook (on Book → enrich → score → research → CRM) + chat-path outcome routing — *built in Phase 5 (`app/chat/orchestrator.py`)*
- [x] Tests: each agent against stub fixtures; correct branching, no real network/LLM in unit suite

## Phase 4 — Inbound pipeline orchestration

- [x] Chain: exit check → cache/enrich → score → route → Research → Copywriter → CRM (`app/pipeline/inbound.py`)
- [x] C-grade short-circuit → CRM disqualified (skip Research/Copywriter)
- [x] End-to-end pipeline test with sample leads (A qualified, C disqualified, exit-check fixtures; B routes through the same qualified branch)
- [x] **Iteration log** — `ITERATION-LOG.md` (portal-id, JSON extraction, Sage threshold, OpenAI quota, Apollo cache)

## Phase 5 — API surface

- [x] `POST /demo` — runs inbound pipeline, returns Lead Brief (`app/api/routes.py`, `schemas.py`)
- [x] `POST /chat` — drives Sage turn-by-turn, server-side qualification state + outcome routing (`app/chat/`: `session.py`, `outcome.py`, `orchestrator.py`)
  - Book → synthesizes a form, runs the same enrich→score→research→CRM pipeline, attaches the chat transcript as a deal note
  - Disqualify (with email) → disqualified-stage deal + mandatory reason note; without email → warm close, no CRM
- [x] Error handling + graceful fallbacks: exit-check → 400, provider failure → 502, Tavily search-fail degrades to no-results, chat CRM errors swallowed (reply always returned). CORS for the Next.js dev origin.
- [x] Tests: `test_chat_session.py`, `test_chat_outcome.py`, `test_chat_orchestrator.py`, `test_api.py` (TestClient + dependency overrides). Full suite 98 passing.

---

## Phase 6 — Website (Next.js)

- [x] Scaffold fresh Next.js 16 app (App Router, TS, Tailwind v4) in `frontend/`
- [x] Pages from `website-copy.md`: Home, Product, Pricing, Case Studies, Demo (copy in `src/lib/sentio.ts`)
- [x] Demo form → `POST /demo` (`src/app/demo/page.tsx`); renders Lead Brief result state (scorecard, contact/company panels, research signal, draft email, HubSpot ref)
- [x] `next build` clean — all 6 routes prerender; all pages serve 200 in dev
- [ ] Deploy to Vercel — *not run (set `NEXT_PUBLIC_API_BASE` to the deployed backend)*

## Phase 7 — Chat widget (Sage)

- [x] Widget component wired to `POST /chat` (`src/components/SageWidget.tsx`), threads `session_id`
- [x] Mounted on **all pages** via `layout.tsx`, passes current `pathname` as page (page-aware); auto-opens after 5s on `/pricing` + `/demo`
- [x] Outcome UX: book confirmation, escalation hand-off, nurture resource note, warm disqualify; connection-error fallback string
- [x] End-to-end verified: live `/chat` returns a grounded answer citing real KB sources; site renders with widget mounted

## Phase 8 — Deliverables

- [ ] End-to-end demo run-through (form path + chat path)
- [ ] Loom video — camera-on, under 5 min, CMO narrative
- [ ] Final design doc polish + trade-offs / what-was-cut section
- [ ] GitHub repo, README, reproducible setup

---

## Open items / blockers

- [x] **Disqualified stage** — created (`3840698071`, "Agent Disqualified"). Pipeline is `default` (the `246500414` in old docs was the portal id, now corrected everywhere).
- [x] Widget reconciled: mounted on **all pages** (per Solution-Design-Document), auto-opens after 5s only on `/pricing` + `/demo` (per website-copy)
- [ ] Confirm Apollo + Tavily + HubSpot free-tier limits are enough for the demo
