# Phases 5–7 Implementation Plan — API surface, website, chat widget

> **For agentic workers:** executed inline in this session (full backend context already loaded). Backend tasks are TDD; frontend tasks are authored then verified with `next build` / dev run.

**Goal:** Expose the inbound pipeline and Sage over HTTP, then build the Next.js site and page-aware chat widget on top.

**Architecture:** FastAPI gains `/demo` (runs `run_inbound_pipeline` → Lead Brief JSON) and `/chat` (server-side session state → Sage turn → outcome routing → CRM on Book/Disqualify). Next.js (App Router, TS, Tailwind) renders the five pages from `website-copy.md`, the demo form posts to `/demo`, and a site-wide widget posts to `/chat`.

**Tech Stack:** FastAPI + Starlette TestClient + pytest (backend); Next.js 14 App Router, TypeScript, Tailwind (frontend).

---

## Phase 5 — API surface (backend, TDD)

### Task 5.1: Chat session state + store
- Create `app/chat/models.py`: `QualificationState` (session_id, page, history: list[{role,content}], signals: dict[str,str], outcome: str, email: str|None, crm: CrmResult|None), `ChatTurn` (reply, escalated, outcome, sources, booked, session_id).
- Create `app/chat/session.py`: in-memory `SessionStore` (process-local dict) with `get_or_create(session_id, page)` and implicit save-by-reference.
- Test: store creates, returns same object, isolates by id.

### Task 5.2: Outcome classifier
- Create `app/chat/outcome.py`: `classify(history, signals, llm) -> OutcomeDecision` — one structured JSON LLM call over the transcript returning `{signals, outcome in continue|book|nurture|escalate|disqualify, email, reason}`. Reuse `_extract_json` pattern from research. Prompt inline (clean, visible).
- Test with a StubLLM returning each outcome; assert parse + defaults (unknown outcome → continue).

### Task 5.3: Chat orchestrator
- Create `app/chat/orchestrator.py`: `handle_turn(state, message, *, llm, retriever, apollo, tavily, hubspot) -> ChatTurn`.
  1. append user msg; 2. `sage.answer()` (retrieval gate → escalate path); 3. if answered, `outcome.classify()`; merge signals; 4. on `book` + email → synthesize form, `run_inbound_pipeline`, attach transcript note; 5. on `disqualify` + email → `sync_to_crm` disqualified + reason+transcript note; 6. persist, return ChatTurn.
- Resilience: CRM/enrichment errors are caught → reply still returned, `booked=False`.
- Tests: escalate (low conf), continue, book-with-email triggers pipeline (stubs), disqualify-with-email writes disqualified deal, disqualify-without-email closes warmly with no CRM.

### Task 5.4: Research search-fail resilience
- `app/agents/research.py`: catch `httpx.HTTPError` (not just `TavilyBudgetError`) around `tavily.search` → empty results. Test.

### Task 5.5: FastAPI endpoints + CORS
- `app/api/schemas.py`: Pydantic `DemoRequest`, `LeadBrief`, `ChatRequest`, `ChatResponse`.
- `app/api/routes.py` (or extend `main.py`): `POST /demo`, `POST /chat`, dependency providers (`get_llm`, `get_retriever`, real clients) overridable in tests. CORS for `http://localhost:3000`. Exit-check `ValueError` → 400; provider failure → 502 (frontend shows generic fallback).
- Tests with TestClient + dependency overrides (stubs): /demo qualified brief, /demo bad email → 400, /chat answer turn, /chat session continuity.

## Phase 6 — Website (Next.js)

### Task 6.1: Scaffold
- `frontend/` Next.js App Router + TS + Tailwind. `lib/sentio.ts` (brand/nav/footer/competitor content), `lib/api.ts` (`postDemo`, `postChat`, base URL from `NEXT_PUBLIC_API_BASE`). Verify `npm run build`.

### Task 6.2: Shell — layout, nav, footer, tokens
- `app/layout.tsx`, `components/Nav.tsx`, `components/Footer.tsx`, Tailwind theme. Brand "S · Sentio", nav links, header CTA.

### Task 6.3: Home `/`
- Hero, Problems (3), Features (4), Social proof (2), Integrations, CTA band — copy verbatim from `website-copy.md`.

### Task 6.4: Product `/product`, Pricing `/pricing`, Case Studies `/case-studies`
- Reuse card components; pricing 3 plans + FAQ; case studies 2 stories + disclaimer.

### Task 6.5: Demo `/demo` + form → `/demo` + Lead Brief
- Pitch column + form (all fields/options from copy), POST to `/demo`, render Lead Brief result state (scorecard, contact/company panels, research signal, draft email, HubSpot ref). Error → generic fallback.

## Phase 7 — Chat widget (Sage)

### Task 7.1: Widget component
- `components/SageWidget.tsx`: launcher, panel, message list, typing indicator, input. Greeting + strings from copy. Generates `session_id`, sends current `pathname` as page. Posts to `/chat`, threads `session_id`.

### Task 7.2: Mount site-wide + outcome UX
- Mount in `layout.tsx` (all pages, page-aware per Solution-Design-Document). Auto-open after 5s. Outcome states: book confirmation, escalation hand-off, nurture resource, warm disqualify. Connection-error fallback string.

### Task 7.3: End-to-end verify
- `next build`; run backend + frontend dev; manual smoke of form path + chat path.
