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

- [ ] ICP scoring CSV built from `sentio-company-profile.md` (weights as data)
- [ ] Fit-score calculator (headcount, industry, title, geography, business model) → A/B/C grade
- [ ] Industry disambiguation (Financial Services → Apollo `technologies`, Tavily fallback)
- [ ] Intent score from available signal (thin for form, richer for chat)
- [ ] Routing / exit gate (C-grade → disqualified path; A/B → research/email path)
- [ ] Tests: known-input fixtures → expected grade/score (deterministic, reproducible)

## Phase 3 — The agents (backend)

- [ ] **Research Agent** — Apollo-first signal mining, Tavily supplement loop, JSON brief output
- [ ] **Copywriter Agent** — stakeholder-framed email + SDR notes, sourced-facts-only guardrails
- [ ] **CRM Agent** — HubSpot upsert, stage-by-outcome, mandatory notes (qualified + disqualified)
- [ ] **Sage Agent** — RAG-grounded chat: KB retrieval, 5-signal qualification, outcomes (book/escalate/nurture/disqualify), cosine<0.75 escalation
  - [ ] RAG setup: sentence-transformers embeddings + ChromaDB, ingest `kb/*.md`
  - [ ] Post-email-capture hook: on Book → enrich → score → research → CRM upsert
- [ ] Tests: each agent against fixtures; assert no fabricated facts, correct branching

## Phase 4 — Inbound pipeline orchestration

- [ ] Chain: exit check → cache/enrich → score → route → Research → Copywriter → CRM
- [ ] C-grade short-circuit → CRM disqualified (skip Research/Copywriter)
- [ ] End-to-end pipeline test with a sample lead (A, B, and C fixtures)
- [ ] **Iteration log** — record what broke and how it was fixed (assignment values this)

## Phase 5 — API surface

- [ ] `POST /demo` — runs inbound pipeline, returns lead brief
- [ ] `POST /chat` — drives Sage turn-by-turn, maintains server-side qualification state
- [ ] Error handling + graceful fallbacks (enrichment miss, search fail, HubSpot down)

---

## Phase 6 — Website (Next.js)

- [ ] Scaffold Next.js app (fresh — `archive/frontend` is superseded, do not reuse)
- [ ] Pages from `website-copy.md`: Home, Product, Pricing, Case Studies, Demo
- [ ] Demo form → `POST /demo`; render Lead Brief result state
- [ ] Deploy target (Vercel)

## Phase 7 — Chat widget (Sage)

- [ ] Widget component wired to `POST /chat`
- [ ] Mount on **all pages**, pass current page at init (page-aware intent)
- [ ] Outcome UX: book confirmation, escalation, nurture resource, warm disqualify

## Phase 8 — Deliverables

- [ ] End-to-end demo run-through (form path + chat path)
- [ ] Loom video — camera-on, under 5 min, CMO narrative
- [ ] Final design doc polish + trade-offs / what-was-cut section
- [ ] GitHub repo, README, reproducible setup

---

## Open items / blockers

- [x] **Disqualified stage** — created (`3840698071`, "Agent Disqualified"). Pipeline is `default` (the `246500414` in old docs was the portal id, now corrected everywhere).
- [ ] `CLAUDE.md` line 25 still says widget on `/pricing` + `/demo` — update to "all pages" if desired (minor)
- [ ] Confirm Apollo + Tavily + HubSpot free-tier limits are enough for the demo
