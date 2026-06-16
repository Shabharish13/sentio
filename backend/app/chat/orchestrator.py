from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.agents.crm import sync_to_crm
from app.agents.models import CrmResult
from app.agents.sage import answer as sage_answer
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
                llm, retriever, apollo, tavily, hubspot) -> ChatTurn:
    """One chat turn: ground via Sage and classify the outcome CONCURRENTLY, then
    fire any terminal CRM action. The classifier reads only the visitor transcript,
    so it does not depend on Sage's freshly generated answer - running both blocking
    LLM calls in parallel roughly halves turn latency. CRM/enrichment failures
    degrade gracefully: the reply is always returned so the conversation never dies
    on an integration error."""
    state.add("user", message)

    # Snapshot the transcript the classifier sees (visitor messages so far) before
    # appending Sage's reply, so the two LLM calls are truly independent.
    classifier_history = list(state.history)

    with ThreadPoolExecutor(max_workers=2) as pool:
        sage_future = pool.submit(sage_answer, message, page=state.page, llm=llm, retriever=retriever)
        decision_future = pool.submit(classify, classifier_history, state.signals, llm)
        sage = sage_future.result()
        decision = decision_future.result()

    state.add("assistant", sage.answer)

    # Off-topic / low retrieval confidence: stay in the conversation, do not run any
    # terminal CRM action, ignore the classifier's outcome for this turn.
    if sage.redirected:
        state.outcome = "continue"
        return ChatTurn(session_id=state.session_id, reply=sage.answer,
                        question=sage.question, outcome="continue", escalated=False,
                        booked=False, sources=[])

    state.signals.update(decision.signals)
    if decision.email and not state.email:
        state.email = decision.email
    state.outcome = decision.outcome

    reply = sage.answer
    escalated = decision.outcome == "escalate"
    if escalated and not state.email:
        # No email yet: ask for one so a rep can follow up (no fake live handoff).
        reply = sage.answer.rstrip() + ESCALATION_EMAIL_PROMPT

    booked = False
    try:
        if decision.outcome == "book" and state.email:
            state.crm = _book(state, apollo=apollo, llm=llm, tavily=tavily, hubspot=hubspot)
            booked = state.crm.stage == get_demo_stage()
        elif decision.outcome == "disqualify" and state.email:
            state.crm = _disqualify(state, decision.reason, hubspot=hubspot)
        elif decision.outcome == "escalate" and state.email:
            state.crm = _escalate(state, hubspot=hubspot)
    except Exception:  # noqa: BLE001 — never let a CRM error break the chat reply
        logger.exception("chat CRM action failed for session %s", state.session_id)

    return ChatTurn(session_id=state.session_id, reply=reply, question=sage.question,
                    outcome=state.outcome, escalated=escalated, booked=booked,
                    sources=sage.sources)


def get_demo_stage() -> str:
    from app.config import get_settings
    return get_settings().hubspot_stage_demo_requested
