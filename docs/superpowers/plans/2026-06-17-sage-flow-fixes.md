# Sage Chat Flow Fixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the Sage chat qualify→book flow so visitors are actually qualified, the Book path can collect an email and run the CRM pipeline, plain demo requests stop misrouting to escalate, and terminal turns can't be dropped or contradicted.

**Architecture:** Four root causes, validated live against `POST /chat` on 2026-06-17, all in the chat runtime (`backend/app/chat/`). Fixes are small and additive: a deterministic fallback in the classifier, an email ask on the Book branch, a prompt clarification, and a restructure of the orchestrator's terminal/redirect handling. LLM behaviour is mocked in unit tests, so each task pairs unit tests with a final live-verification task.

**Tech Stack:** Python 3.11+, FastAPI, pytest. Backend venv: `backend/.venv/Scripts/python.exe`. Run tests from `backend/`.

---

## Background — the four validated root causes

1. **Qualification loop dead.** `outcome.py` classifier returns `next_question: null` even on a cold `continue` turn with zero signals (live-confirmed), so Sage never asks the binary qualifying questions. → Task 1.
2. **Escalate over-triggers.** A plain "Can you book a demo for me?" classifies as `escalate` (live-confirmed `outcome: "escalate"`), so it never enters the qualify→book path. → Task 2.
3. **Book never asks for the email.** `orchestrator.py:184-187` appends the email ask only on `escalate`. A real `book` outcome with no email solicits nothing, schedules nothing, `booked` stays false. → Task 3.
4. **Redirect guard drops/contradicts terminal turns.** `orchestrator.py:158` returns early on `sage.redirected` for everything except `escalate`, bouncing short booking replies; and the terminal `reply` is raw `sage.answer`, which can contradict the action ("I cannot capture emails" while capturing). → Task 4.

Then Task 5 verifies all four live.

## File Structure

- Modify: `backend/app/chat/outcome.py` — add deterministic `next_question` fallback (Task 1); tighten escalate scoping in the prompt (Task 2).
- Modify: `backend/app/chat/orchestrator.py` — add `BOOK_EMAIL_PROMPT` + book email ask (Task 3); restructure terminal/redirect handling + confirmation replies (Task 4).
- Modify: `backend/tests/test_chat_outcome.py` — fallback tests; update `test_classify_blank_next_question_is_none` (behaviour changes).
- Modify: `backend/tests/test_chat_orchestrator.py` — book-email-ask, redirect-survival, reply-reconciliation tests.

---

### Task 1: Classifier always yields a qualifying question on non-terminal turns

**Files:**
- Modify: `backend/app/chat/outcome.py`
- Test: `backend/tests/test_chat_outcome.py`

Root cause: the live gpt-5 classifier frequently omits `next_question`. Fix = a deterministic fallback (the LLM stays primary; code guarantees a question) plus a small `max_tokens` bump to reduce truncation. No change to `classify`'s call signature, so test stubs are unaffected.

- [ ] **Step 1: Write/replace the failing tests**

In `backend/tests/test_chat_outcome.py`, **replace** `test_classify_blank_next_question_is_none` (its behaviour changes — a blank on a non-terminal turn now falls back) and add two tests:

```python
def test_classify_falls_back_to_question_when_llm_omits_it():
    # Live gpt-5 frequently drops next_question; on a non-terminal turn we synthesize
    # one deterministically so qualification never stalls.
    d = classify([], {}, StubLLM(json.dumps({"outcome": "continue"})))
    assert d.next_question is not None
    assert d.next_question.endswith("?")


def test_fallback_question_skips_already_collected_signals():
    # use_case + team_context known -> the fallback targets the next gap (authority).
    d = classify([], {"use_case": "churn", "team_context": "CS team"},
                 StubLLM(json.dumps({"outcome": "continue"})))
    assert "broader group" in d.next_question


def test_classify_blank_next_question_falls_back_on_continue():
    # A blank/whitespace question no longer passes through as None on a non-terminal
    # turn; it is replaced by a deterministic fallback.
    d = classify([], {}, StubLLM(json.dumps({"outcome": "continue", "next_question": "  "})))
    assert d.next_question is not None
    assert d.next_question.endswith("?")
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_outcome.py -q`
Expected: the three new/updated tests FAIL (fallback returns `None` today).

- [ ] **Step 3: Implement the fallback in `outcome.py`**

Add, immediately after the `CLASSIFIER_PROMPT` string (before `@dataclass class OutcomeDecision`):

```python
# Ordered deterministic fallback questions, one per qualifying signal. Used when the
# LLM omits next_question on a non-terminal turn so qualification never silently
# stalls. Phrasing mirrors the suggestions in CLASSIFIER_PROMPT above.
_FALLBACK_QUESTIONS: list[tuple[str, str]] = [
    ("use_case", "Is the main thing you're solving surprise churn, or giving your CS team a consistent view of account health?"),
    ("team_context", "Are you on a customer success team, or more of a RevOps / operations role?"),
    ("authority", "Are you evaluating this for your own team, or is there a broader group - finance, IT - who'd be involved?"),
    ("timeline", "Is this something you're actively solving this quarter, or still in early research?"),
    ("company_scale", "Are you working with a CS team of roughly 10 or fewer, or larger than that?"),
]


def _fallback_question(known: dict[str, str]) -> str | None:
    """First qualifying question whose signal has not been collected yet."""
    for signal, question in _FALLBACK_QUESTIONS:
        if not known.get(signal):
            return question
    return None
```

In `classify`, change the call's `max_tokens` and replace the terminal-null guard block. Current:

```python
    raw = llm.complete(CLASSIFIER_PROMPT, user, max_tokens=300)
```
becomes:
```python
    raw = llm.complete(CLASSIFIER_PROMPT, user, max_tokens=500)
```

Current tail:
```python
    # Defense in depth: a terminal outcome never carries a qualifying question, so the
    # close stays clean even if the model emits one against instructions.
    if outcome in ("book", "escalate", "disqualify"):
        next_question = None

    return OutcomeDecision(outcome=outcome, signals=merged, email=email, reason=reason,
                           next_question=next_question)
```
becomes:
```python
    # A terminal outcome never carries a qualifying question (clean close, even if the
    # model emits one). On a non-terminal turn, guarantee a question deterministically
    # when the model omitted it, so qualification always advances.
    if outcome in ("book", "escalate", "disqualify"):
        next_question = None
    elif next_question is None:
        next_question = _fallback_question({**signals, **merged})

    return OutcomeDecision(outcome=outcome, signals=merged, email=email, reason=reason,
                           next_question=next_question)
```

- [ ] **Step 4: Run the file's tests**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_outcome.py -q`
Expected: PASS (all, including the existing `test_classify_returns_next_question_on_continue` — a provided question is still preserved — and `test_classify_nulls_next_question_on_every_terminal_outcome`).

- [ ] **Step 5: Commit**

```bash
git add backend/app/chat/outcome.py backend/tests/test_chat_outcome.py
git commit -m "fix(chat): guarantee a qualifying question on non-terminal turns"
```

---

### Task 2: Stop plain demo requests from misrouting to escalate

**Files:**
- Modify: `backend/app/chat/outcome.py` (the `CLASSIFIER_PROMPT` text only)
- Test: `backend/tests/test_chat_outcome.py`

Root cause: the escalate rule treats "talk to sales / book a demo" as a human handoff. Demo/booking intent must flow through qualify→book, not escalate. This is a prompt fix; LLM routing is verified live in Task 5. A guard test pins the clarifying text so it can't be silently deleted.

- [ ] **Step 1: Write the failing guard test**

Add to `backend/tests/test_chat_outcome.py`:

```python
def test_classifier_prompt_excludes_demo_requests_from_escalation():
    from app.chat.outcome import CLASSIFIER_PROMPT
    text = CLASSIFIER_PROMPT.lower()
    assert "book a demo" in text
    assert "not an escalation" in text
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_outcome.py::test_classifier_prompt_excludes_demo_requests_from_escalation -q`
Expected: FAIL ("not an escalation" not yet in prompt).

- [ ] **Step 3: Edit the escalate bullet in `CLASSIFIER_PROMPT`**

Find the `CRITICAL:` line inside the `"escalate"` bullet and append a second clarifying sentence right after it. Current passage ends:

```python
  certifications (e.g. "are you SOC 2 certified?", "are you GDPR compliant?",
  "do you support SSO?"), pricing, or features is NOT an escalation - Sage answers
  those from its knowledge base, so they are "continue". Escalate needs intent to
  involve a human, not just mention of a sensitive topic. Off-topic chatter, jokes,
  or unrelated questions are also "continue" (the assistant redirects them).
```
Replace with:
```python
  certifications (e.g. "are you SOC 2 certified?", "are you GDPR compliant?",
  "do you support SSO?"), pricing, or features is NOT an escalation - Sage answers
  those from its knowledge base, so they are "continue". Escalate needs intent to
  involve a human, not just mention of a sensitive topic. Off-topic chatter, jokes,
  or unrelated questions are also "continue" (the assistant redirects them).
  ALSO NOT an escalation: wanting a demo, asking to "book a demo", "schedule a demo",
  or "get started". A demo request is the Book path - return "continue" and keep
  qualifying until company scale + champion role + active timeline are known, at which
  point it becomes "book". Only route to a human via escalate for the (a)/(b)/(c)
  triggers above.
```

- [ ] **Step 4: Run the file's tests**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_outcome.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/chat/outcome.py backend/tests/test_chat_outcome.py
git commit -m "fix(chat): route demo requests to qualify->book, not escalate"
```

---

### Task 3: Book outcome asks for the visitor's email

**Files:**
- Modify: `backend/app/chat/orchestrator.py`
- Test: `backend/tests/test_chat_orchestrator.py`

Root cause: only the escalate branch appends an email ask. Add a Book email prompt so the Book pipeline can collect its required input.

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/test_chat_orchestrator.py`:

```python
def test_book_without_email_asks_for_email_no_crm():
    # A qualified booker with no email yet must be ASKED for it (the Book pipeline
    # needs it). Previously the book branch said nothing and the lead dead-ended.
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "book",
                          "signals": {"authority": "VP of Customer Success",
                                      "timeline": "this quarter", "company_scale": "200+"}})
    turn = handle_turn(_state(), "yes, I'd like to book a demo", llm=StubLLM(payload),
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "book"
    assert turn.booked is False           # no email captured yet
    assert "work email" in turn.reply     # email-capture ask appended
    assert turn.question is None          # terminal: no qualifying question
    assert hubspot.calls == []            # nothing written without an email
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_orchestrator.py::test_book_without_email_asks_for_email_no_crm -q`
Expected: FAIL ("work email" not in reply — book branch asks nothing today).

- [ ] **Step 3: Add the constant and the book email ask**

In `backend/app/chat/orchestrator.py`, after the `ESCALATION_REDIRECT_REPLY` constant, add:

```python
# Asked for on a Book outcome when we don't yet have the visitor's email — the Book
# pipeline (enrich -> score -> research -> CRM) needs it to run.
BOOK_EMAIL_PROMPT = (
    " Happy to set that up - what's the best work email for our team to send the "
    "demo details to?"
)
```

Then locate the existing escalate-ask block:
```python
    wants_escalation = decision.outcome == "escalate"
    if wants_escalation and not state.email:
        # No email yet: ask for one so a rep can follow up (no fake live handoff).
        reply = reply.rstrip() + ESCALATION_EMAIL_PROMPT
```
and add a book case immediately below it:
```python
    if decision.outcome == "book" and not state.email:
        # Qualified to book but no email yet: ask for it so the Book pipeline can run.
        reply = reply.rstrip() + BOOK_EMAIL_PROMPT
```

- [ ] **Step 4: Run the orchestrator tests**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_orchestrator.py -q`
Expected: PASS (new test + all existing).

- [ ] **Step 5: Commit**

```bash
git add backend/app/chat/orchestrator.py backend/tests/test_chat_orchestrator.py
git commit -m "fix(chat): ask for the email on a Book outcome"
```

---

### Task 4: Terminal turns survive the redirect guard and reply matches the action

**Files:**
- Modify: `backend/app/chat/orchestrator.py`
- Test: `backend/tests/test_chat_orchestrator.py`

Root cause: (a) the redirect guard returns early for every non-escalate outcome, bouncing short booking replies; (b) on a terminal action with an email, the reply is raw `sage.answer` and can contradict the action. Restructure so email extraction happens first, only **non-terminal** redirects bounce, and a fired terminal action returns a confirmation reply. This restructures the block from Task 3 while keeping its test green (it reuses `BOOK_EMAIL_PROMPT`).

- [ ] **Step 1: Write the failing tests**

Add to `backend/tests/test_chat_orchestrator.py`:

```python
def test_book_redirected_with_email_is_not_bounced_and_books():
    # Short booking confirmation ("ok book it, me@acme.com") retrieves no KB content so
    # Sage redirects - but it's a real Book and must NOT be swallowed by the off-topic
    # guard. (This is the live-reported context-loss/dropped-email bug.)
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "book", "email": "me@acme.com",
                          "signals": {"authority": "VP CS", "company_scale": "200+"}})
    turn = handle_turn(_state(), "ok book it, me@acme.com", llm=StubLLM(payload),
                       retriever=StubRetriever(0.10),  # below threshold -> redirected
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.booked is True
    assert turn.reply != REDIRECT_MESSAGE
    assert any(c[0] == "deal" for c in hubspot.calls)


def test_terminal_reply_confirms_and_does_not_contradict_action():
    # When a deal is actually written, the reply confirms the handoff instead of
    # claiming it cannot capture emails.
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "escalate", "email": "ciso@bigco.com"})
    turn = handle_turn(_state(), "we need a security review, ciso@bigco.com",
                       llm=StubLLM(payload), retriever=StubRetriever(0.55),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is True
    low = turn.reply.lower()
    assert "cannot" not in low and "can't" not in low
    assert "team" in low  # confirms the handoff happened
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_orchestrator.py -q -k "redirected_with_email or confirms_and_does_not_contradict"`
Expected: both FAIL (book+redirect is bounced today; escalate reply is raw `sage.answer`).

- [ ] **Step 3: Add confirmation replies and restructure `handle_turn`**

In `orchestrator.py`, after `BOOK_EMAIL_PROMPT`, add:

```python
# Confirmation lead-ins used once a terminal outcome fires WITH an email in hand, so
# the visitor-facing reply matches what the runtime actually did (no "I can't capture
# emails" contradictions).
_CONFIRMATION_REPLIES = {
    "book": "Perfect - I've shared your details with our team and they'll reach out "
            "shortly to set up your demo.",
    "escalate": "Thanks - I've passed your details and this conversation to our team, "
                "and a rep will follow up with you directly.",
    "disqualify": "Thanks for sharing - I've noted your details for our team. "
                  "Appreciate you taking the time.",
}


def _confirmation_reply(outcome: str) -> str:
    return _CONFIRMATION_REPLIES.get(outcome, ESCALATION_REDIRECT_REPLY)
```

Replace the entire block in `handle_turn` from the redirect guard comment (the `# Off-topic / low retrieval confidence ...` comment above `if sage.redirected and decision.outcome != "escalate":`) down to and including the `return ChatTurn(...)` at the end of the function — **but not** the `_terminal_action` / `get_demo_stage` defs below it — with:

```python
    # Email + signals are resolved on EVERY turn (even a redirected one) so a terminal
    # action is never dropped. Email presence is decided in code (regex), classifier
    # field as fallback.
    state.signals.update(decision.signals)
    email = extract_email(message) or decision.email
    if email and not state.email:
        state.email = email

    terminal = decision.outcome in ("book", "escalate", "disqualify")

    # An off-topic / low-confidence redirect only stands on a NON-terminal turn. A real
    # book/escalate/disqualify retrieves no KB content (so Sage redirects) but must
    # survive instead of being bounced with the off-topic message.
    if sage.redirected and not terminal:
        state.outcome = "continue"
        state.add("assistant", _assistant_utterance(sage.answer, None))
        return ChatTurn(session_id=state.session_id, reply=sage.answer,
                        question=None, outcome="continue", escalated=False,
                        booked=False, sources=[])

    state.outcome = decision.outcome

    # Base reply: a redirected terminal turn produced only the off-topic message, so
    # swap in a handoff lead-in; otherwise use Sage's grounded answer.
    reply = ESCALATION_REDIRECT_REPLY if sage.redirected else sage.answer
    # The qualifying question is owned by the router and is always None on a terminal
    # outcome, so it can never contradict a book/escalate/disqualify close. Dropped on
    # a redirect (we're steering the visitor, not qualifying them).
    question = None if (sage.redirected or terminal) else decision.next_question
    sources = [] if sage.redirected else sage.sources

    booked = decision.outcome == "book" and state.email is not None
    escalated = decision.outcome == "escalate" and state.email is not None

    if terminal and state.email:
        # Everything needed is in hand: confirm the handoff (so the reply matches the
        # action) and run the CRM pipeline off the reply path.
        reply = _confirmation_reply(decision.outcome)
        sources = []
        schedule(_terminal_action(state, decision, llm=llm, apollo=apollo,
                                  tavily=tavily, hubspot=hubspot))
    elif decision.outcome == "book":
        # Qualified to book but no email yet: ask for it so the Book pipeline can run.
        reply = reply.rstrip() + BOOK_EMAIL_PROMPT
    elif decision.outcome == "escalate":
        # No email yet: ask for one so a rep can follow up (no fake live handoff).
        reply = reply.rstrip() + ESCALATION_EMAIL_PROMPT
    # disqualify without an email: warm close, no email ask (SDD: don't push for it).

    state.add("assistant", _assistant_utterance(reply, question))
    return ChatTurn(session_id=state.session_id, reply=reply, question=question,
                    outcome=state.outcome, escalated=escalated, booked=booked,
                    sources=sources)
```

Note: this removes the now-duplicated `if decision.outcome == "book" and not state.email:` block added in Task 3 and the old `wants_escalation` block — they are folded into the if/elif above. Delete any leftover copies so the book/escalate ask exists only once.

- [ ] **Step 4: Run the full orchestrator suite**

Run: `cd backend && .venv/Scripts/python.exe -m pytest tests/test_chat_orchestrator.py -q`
Expected: PASS — all new tests plus the existing 18 (escalate-without-email still appends the ask; escalate/book/disqualify-with-email still write CRM and defer to the scheduler; off-topic redirect still bounces with no CRM; `test_book_with_email_runs_pipeline_and_attaches_transcript` still books and attaches the transcript).

- [ ] **Step 5: Commit**

```bash
git add backend/app/chat/orchestrator.py backend/tests/test_chat_orchestrator.py
git commit -m "fix(chat): survive redirect on terminal turns; reconcile reply with action"
```

---

### Task 5: Live end-to-end verification (no stubbing)

**Files:** none (verification only). The unit tests mock the LLM, so they cannot prove Tasks 1–2 changed live behaviour. Verify against the running backend.

- [ ] **Step 1: Run the full suite once more**

Run: `cd backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all tests PASS.

- [ ] **Step 2: Restart the backend so it loads the new code**

Run (PowerShell, from `backend/`): stop any running uvicorn, then
`.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000`
(Run in a background terminal; wait until it logs "Application startup complete".)

- [ ] **Step 3: Verify the cold informational turn now asks a qualifying question (Task 1)**

```bash
curl -s -m 120 -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"What does Sentio do?","page":"/pricing"}'
```
Expected: `outcome` = `continue` and `question` is a non-null binary qualifying question (not `null`).

- [ ] **Step 4: Verify a cold "book a demo" no longer escalates (Task 2)**

```bash
curl -s -m 120 -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"Can you book a demo for me?","page":"/pricing"}'
```
Expected: `outcome` is `continue` (qualifying) or `book` — **not** `escalate`. The reply should not contain the escalation-only phrasing "sales rep to follow up on" unless `outcome` is `book`/`escalate`.

- [ ] **Step 5: Verify the Book path asks for the email (Task 3) then books (Task 4)**

Turn A (no email):
```bash
curl -s -m 120 -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"I am VP of Customer Success at a 250-person B2B SaaS, CSMs each manage 90 accounts, surprise churn, evaluating this quarter - I want a demo.","page":"/pricing"}'
```
Expected: `outcome` = `book`, `booked` = false, and the reply asks for a **work email**. Capture the returned `session_id`.

Turn B (give the email, reuse the session_id):
```bash
curl -s -m 120 -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"sure, daniel.foster@rocketlane.com","page":"/pricing","session_id":"<SESSION_ID_FROM_TURN_A>"}'
```
Expected: `booked` = true, reply confirms the handoff (no "I cannot capture emails"), and a HubSpot deal in the demo-requested stage with a transcript note is created (check HubSpot). **Clean up the test deal afterward.**

- [ ] **Step 6: Final commit (docs/verification notes, if any)**

```bash
git add -A
git commit -m "test(chat): live-verify Sage qualify->book flow end to end" --allow-empty
```

---

## Self-Review

- **Spec coverage:** Root cause 1 → Task 1; root cause 2 → Task 2; root cause 3 → Task 3; root cause 4 → Task 4; live proof → Task 5. All four covered.
- **Out of scope (noted):** disqualify-without-email still writes no CRM record (SDD wants a record "either way", but `sync_to_crm` keys on email; deferred — needs a HubSpot keying strategy). Latency (~95–190s `/demo`, ~5–50s chat) is a separate performance track, not part of these flow fixes.
- **Type/name consistency:** `BOOK_EMAIL_PROMPT`, `ESCALATION_EMAIL_PROMPT`, `ESCALATION_REDIRECT_REPLY`, `_CONFIRMATION_REPLIES`/`_confirmation_reply`, `_FALLBACK_QUESTIONS`/`_fallback_question`, `terminal`, `_terminal_action` are used consistently across tasks. Task 4 explicitly folds in and de-duplicates the Task 3 ask.
- **Existing tests traced:** all 18 current `test_chat_orchestrator.py` tests and all `test_chat_outcome.py` tests remain green under the new code paths (only `test_classify_blank_next_question_is_none` intentionally changes behaviour and is replaced in Task 1).
