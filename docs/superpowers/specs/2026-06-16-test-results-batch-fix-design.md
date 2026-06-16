# Test-results Batch Fix — Design

Fixes the five items in `Test-results.md`. Branch: `fix/test-results-batch`.

Each fix is independent; the three chat items (1, 2, 3) share one orchestration
refactor. Classification of every change as **prompt**, **code**, or **KB data**
is explicit below.

## #4 — Demo request returns 502 (code)

**Root cause (reproduced):** `apollo.enrich_person` calls `POST /people/match`,
which returns **403 Forbidden** — person enrichment is not on Apollo's free tier.
The unhandled `raise_for_status()` aborts `run_inbound_pipeline`, and
`routes.py` maps the exception to a 502. Org enrichment (`/organizations/enrich`)
works on the free tier.

**Why a graceful skip is safe:** the demo form already collects name, email, and
job title. Tracing usage: `adapter.py` sets `title = form.job_title or person.title`
(form wins); `fit.py` scores the stakeholder/persona from `lead.title` (form), not
Apollo seniority. The only field unique to person-match is `contact.seniority`,
which nothing downstream consumes. So person enrichment adds nothing the form
doesn't already provide.

**Fix:**
- Keep the `enrich_person` call. Wrap the request so an HTTP status error (403 and
  others) or network error → return `{"person": {}}` instead of raising.
- Pipeline then degrades to org enrichment + form data; scoring is unaffected.
- A future paid Apollo upgrade transparently restores person data.

**Test:** `enrich_person` 403 → `{"person": {}}`; inbound pipeline completes with
form title + org firmographics; `/demo` returns 200.

## #5 — Implementation timeline = 2 weeks (KB data + reindex)

Add an explicit statement to `kb/onboarding-and-support.md` (Time to Value) that
the **typical implementation timeline is about 2 weeks**, keeping the existing
day-by-day detail. Rebuild the Chroma index (`scripts.build_kb_index`). Sage is
KB-grounded, so it can then cite "~2 weeks"; one light line in the Sage prompt
encourages it to call this out when relevant.

**Test:** retrieval query for "implementation timeline" returns the onboarding doc.

## #1 + #2 + #3 — Sage chat overhaul (prompt + code)

### Prompt — `prompts/sage_agent.md`
- **Structured output:** return `{"answer": "...", "question": "..."}`, with
  `question` null on terminal turns. Enables answer and qualifying question as two
  separate chat bubbles (#1).
- **Tone:** explicitly conversational; **markdown rich text** allowed (bold, short
  lists) (#1).
- **ASCII punctuation only** — straight quotes and hyphens, no em-dashes or curly
  quotes — as defense against the `â€` mojibake (#1).
- **Off-topic → redirect:** when a question is outside Sentio's scope, say Sage only
  covers Sentio and steer back; do **not** escalate, stay in the conversation (#2).
- **Escalation message → ask for work email** and say a sales rep will follow up;
  remove the fake "connect you with our team" handoff that has no backing flow (#2).

### Prompt — `app/chat/outcome.py` (classifier)
- Align off-topic vs escalate semantics with the prompt: genuine escalation
  triggers (enterprise pricing, security/legal/procurement, explicit human request)
  → `outcome="escalate"`; off-topic chatter is not an escalation.

### Code
- **`sage.py`:** parse structured `{answer, question}`. Below-confidence retrieval
  (`top_score < threshold`) → return a **redirect** response (off-topic), not an
  escalation. Replace `ESCALATION_MESSAGE` with a `REDIRECT_MESSAGE`; escalation
  email-capture wording lives where the classifier outcome is handled.
- **`orchestrator.py`:** run the Sage answer call and the classifier call
  **concurrently** via `ThreadPoolExecutor` (both are blocking LLM calls; the
  classifier reads only visitor messages, so it does not depend on the new answer).
  When the classifier returns `escalate`, surface the email-capture message and
  capture the email.
- **`schemas.py` / `routes.py`:** `ChatResponse` carries `answer` and `question`
  as separate fields (plus existing `outcome`, `escalated`, `booked`, `sources`).
- **`frontend/src/lib/api.ts`:** update `ChatResponse` type.
- **`SageWidget.tsx`:** render markdown (rich text); **word-by-word typewriter**
  animation; answer and question as separate bubbles (#1, #3).

### Latency approach (#3)
Chosen: **parallelize + client typewriter** (no SSE). Today the two LLM calls run
sequentially; running them concurrently roughly halves turn latency, and the
client typewriter animation gives word-by-word perceived speed. No new endpoint
contract.

### Mojibake root cause (#1)
`â€` is UTF-8 punctuation decoded as cp1252 (the Windows default). Audit file reads
in the RAG path (`rag/store.py`, KB ingest) for explicit `encoding="utf-8"`; fix
the read **and** add the prompt ASCII-punctuation rule together.

## Constraints
- Heed `frontend/AGENTS.md`: read `node_modules/next/dist/docs/` before frontend
  edits. Render markdown with a minimal formatter unless `react-markdown` is already
  a dependency.
- No new Apollo credits burned (cache-first; person-match degrades on 403).
- Scores stay code-computed; no hardcoded outputs.

## Testing summary
- Apollo 403 → empty person → pipeline completes (`/demo` 200).
- Orchestrator: concurrent calls; `escalate` → email capture; off-topic → redirect
  (not escalated).
- KB reindex verified by an "implementation timeline" retrieval query.
- Existing pipeline/API/chat test suites stay green.
