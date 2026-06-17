from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.agents.crm import sync_to_crm
from app.agents.models import CrmResult
from app.agents.sage import answer as sage_answer
from app.chat.email_extract import extract_email
from app.chat.models import ChatTurn, QualificationState
from app.chat.outcome import classify
from app.pipeline.adapter import email_domain
from app.pipeline.inbound import run_inbound_pipeline

logger = logging.getLogger(__name__)

# Asked for when the classifier escalates and we still need the visitor's email.
ESCALATION_EMAIL_PROMPT = (
    " To get this in front of the right person, what's the best work email for a "
    "sales rep to follow up on?"
)

# Lead-in used when the classifier detects a handoff but Sage had no KB answer (so it
# returned the off-topic redirect). We route the visitor to a human instead of
# bouncing them; the email prompt above is appended when no email is on file yet.
ESCALATION_REDIRECT_REPLY = "That's something our team can help you with directly."

# Asked for on a Book outcome when we don't yet have the visitor's email — the Book
# pipeline (enrich -> score -> research -> CRM) needs it to run.
BOOK_EMAIL_PROMPT = (
    " Happy to set that up - what's the best work email for our team to send the "
    "demo details to?"
)


def _assistant_utterance(reply: str, question: str | None) -> str:
    """What the visitor actually saw this turn: the answer plus its qualifying question
    (shown as a separate bubble in the UI). Stored as one history entry so the next
    turn's retrieval and the classifier have the question the visitor is answering."""
    return reply if not question else f"{reply}\n{question}"


def _company_name(state: QualificationState) -> str:
    """Best-effort company label for the CRM record (no enrichment in chat)."""
    if state.signals.get("company"):
        return state.signals["company"]
    domain = email_domain(state.email or "")
    if domain:
        return domain.split(".")[0].replace("-", " ").title()
    return "Website chat lead"


def _scale_to_band(scale: str | None) -> str:
    """Map the free-text company-scale signal to a demo-form size band.

    Only a fallback — when Apollo enriches the domain, real headcount wins.
    Book is already gated on scale >= ~50, so default above the C threshold.
    """
    text = (scale or "").lower()
    if any(t in text for t in ("500", "thousand", "enterprise")):
        return "500+"
    if any(t in text for t in ("200", "300", "hundred", "larger", "bigger")):
        return "201-500"
    return "51-200"


def _chat_note(state: QualificationState) -> str:
    signals = ", ".join(f"{k}: {v}" for k, v in state.signals.items()) or "none recorded"
    return (
        f"Sage chat lead (page {state.page}).\n"
        f"Collected signals: {signals}\n\n"
        f"Transcript:\n{state.transcript()}"
    )


def _book(state: QualificationState, *, apollo, llm, tavily, hubspot) -> CrmResult:
    """Book outcome: run the same enrich -> score -> research -> CRM pipeline the
    form path uses, then attach the chat transcript as a second deal note."""
    form = {
        "first_name": "",
        "last_name": "",
        "work_email": state.email,
        "company_name": _company_name(state),
        "job_title": state.signals.get("authority") or state.signals.get("team_context") or "",
        "company_size": _scale_to_band(state.signals.get("company_scale")),
        "problem_stated": state.signals.get("use_case") or "",
        "how_heard": "Website chat (Sage)",
    }
    result = run_inbound_pipeline(form, apollo=apollo, llm=llm, tavily=tavily, hubspot=hubspot)
    hubspot.create_note(_chat_note(state), deal_id=result.crm.deal_id)
    return result.crm


def _disqualify(state: QualificationState, reason: str | None, *, hubspot) -> CrmResult:
    """Disqualify outcome: upsert a disqualified-stage deal with a mandatory
    reason note, for human review. Requires a captured email (HubSpot key)."""
    reason = reason or "outside Sentio's target market (chat-qualified)"
    note = f"Disqualified via chat. Reason: {reason}\n\n{_chat_note(state)}"
    props = {"firstname": "", "lastname": "", "jobtitle": state.signals.get("authority", "")}
    return sync_to_crm(
        email=state.email,
        contact_props=props,
        deal_name=f"{_company_name(state)} — chat inbound",
        route="disqualified",
        note_body=note,
        hubspot=hubspot,
    )


def _escalate(state: QualificationState, *, hubspot) -> CrmResult:
    """Escalate outcome with a captured email: upsert a contact and attach an
    escalation note so a sales rep has full context. Mirrors _disqualify; the
    deal lands in the demo-requested pipeline since this is a hot, hand-raised lead."""
    note = (
        "Escalated via chat - visitor raised an enterprise/security/human-handoff "
        f"request that needs a sales rep.\n\n{_chat_note(state)}"
    )
    props = {"firstname": "", "lastname": "", "jobtitle": state.signals.get("authority", "")}
    return sync_to_crm(
        email=state.email,
        contact_props=props,
        deal_name=f"{_company_name(state)} - chat escalation",
        route="qualified",
        note_body=note,
        hubspot=hubspot,
    )


def handle_turn(state: QualificationState, message: str, *,
                llm, retriever, apollo, tavily, hubspot, schedule=None) -> ChatTurn:
    """One chat turn: ground via Sage and classify the outcome CONCURRENTLY, then
    hand off any terminal CRM action to `schedule` so it runs OFF the reply path.

    The visitor's reply is on the critical path; the book/escalate/disqualify
    handoff (enrich -> research -> copywriter -> CRM, up to ~100s) is not — it is
    handed to `schedule` (the API passes FastAPI BackgroundTasks; the default runs
    it inline for tests/callers that want synchronous behaviour). Email presence is
    decided in code (deterministic regex), not by the classifier. CRM/enrichment
    failures degrade gracefully: they are swallowed inside the deferred action so the
    conversation never dies on an integration error, and `booked` is reported
    optimistically the moment the lead qualifies with an email in hand."""
    # Default: run the handoff inline (preserves synchronous behaviour for tests and
    # any caller that does not supply a background scheduler).
    schedule = schedule or (lambda action: action())
    state.add("user", message)

    # Snapshot the transcript the classifier sees (visitor messages so far) before
    # appending Sage's reply, so the two LLM calls are truly independent.
    classifier_history = list(state.history)
    # Prior turns (everything before this message) give Sage the context the visitor is
    # replying to, so retrieval and the reply are not read message-by-message in isolation.
    sage_history = state.history[:-1]

    with ThreadPoolExecutor(max_workers=2) as pool:
        sage_future = pool.submit(sage_answer, message, page=state.page, llm=llm,
                                  retriever=retriever, history=sage_history)
        decision_future = pool.submit(classify, classifier_history, state.signals, llm)
        sage = sage_future.result()
        decision = decision_future.result()

    # Off-topic / low retrieval confidence stays in the conversation with no terminal
    # action — UNLESS the classifier detected a genuine handoff intent ("talk to a
    # human", a security review). Such asks retrieve no KB content so Sage redirects,
    # but bouncing them with the off-topic message would drop a real escalation.
    if sage.redirected and decision.outcome != "escalate":
        state.outcome = "continue"
        # An off-topic redirect carries no qualifying question - the redirect message
        # already invites the visitor back to Sentio topics.
        state.add("assistant", _assistant_utterance(sage.answer, None))
        return ChatTurn(session_id=state.session_id, reply=sage.answer,
                        question=None, outcome="continue", escalated=False,
                        booked=False, sources=[])

    state.signals.update(decision.signals)
    # Deterministic email gate: a regex on the visitor's message decides whether we
    # have an email, falling back to the classifier's field only if code found none.
    email = extract_email(message) or decision.email
    if email and not state.email:
        state.email = email
    state.outcome = decision.outcome

    # On a redirect we're honoring as an escalation, Sage only produced the off-topic
    # message — replace it with a handoff lead-in and drop the (empty) KB citations.
    reply = ESCALATION_REDIRECT_REPLY if sage.redirected else sage.answer
    # The qualifying question is owned by the router, which already nulls it on every
    # terminal outcome - so it can never contradict a book/escalate/disqualify close.
    # Dropped on a redirect (we're steering the visitor, not qualifying them).
    question = None if sage.redirected else decision.next_question
    sources = [] if sage.redirected else sage.sources

    wants_escalation = decision.outcome == "escalate"
    if wants_escalation and not state.email:
        # No email yet: ask for one so a rep can follow up (no fake live handoff).
        reply = reply.rstrip() + ESCALATION_EMAIL_PROMPT
    if decision.outcome == "book" and not state.email:
        # Qualified to book but no email yet: ask for it so the Book pipeline can run.
        reply = reply.rstrip() + BOOK_EMAIL_PROMPT

    # Hand off the terminal CRM action off the reply path. It only fires once we have
    # the email (the deterministic gate above) — the chatbot has finished collecting.
    if decision.outcome in ("book", "disqualify", "escalate") and state.email:
        schedule(_terminal_action(state, decision, llm=llm, apollo=apollo,
                                  tavily=tavily, hubspot=hubspot))

    # booked/escalated report what ACTUALLY happened, so the UI badge never claims a
    # handoff that didn't occur: both require a captured email. The CRM write itself
    # runs off the reply path (optimistic — failures are logged, not surfaced).
    booked = decision.outcome == "book" and state.email is not None
    escalated = wants_escalation and state.email is not None

    state.add("assistant", _assistant_utterance(reply, question))
    return ChatTurn(session_id=state.session_id, reply=reply, question=question,
                    outcome=state.outcome, escalated=escalated, booked=booked,
                    sources=sources)


def _terminal_action(state: QualificationState, decision, *, llm, apollo, tavily, hubspot):
    """Build the deferred handoff closure for a terminal outcome. Runs the matching
    CRM pipeline and swallows any integration error (logged, never surfaced)."""
    def run() -> None:
        try:
            if decision.outcome == "book":
                state.crm = _book(state, apollo=apollo, llm=llm, tavily=tavily, hubspot=hubspot)
            elif decision.outcome == "disqualify":
                state.crm = _disqualify(state, decision.reason, hubspot=hubspot)
            elif decision.outcome == "escalate":
                state.crm = _escalate(state, hubspot=hubspot)
        except Exception:  # noqa: BLE001 — never let a CRM error break the chat
            logger.exception("chat CRM handoff failed for session %s", state.session_id)
    return run


def get_demo_stage() -> str:
    from app.config import get_settings
    return get_settings().hubspot_stage_demo_requested
