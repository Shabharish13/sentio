from __future__ import annotations

import logging

from app.agents.crm import sync_to_crm
from app.agents.models import CrmResult
from app.agents.sage import answer as sage_answer
from app.chat.models import ChatTurn, QualificationState
from app.chat.outcome import classify
from app.pipeline.adapter import email_domain
from app.pipeline.inbound import run_inbound_pipeline

logger = logging.getLogger(__name__)


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


def handle_turn(state: QualificationState, message: str, *,
                llm, retriever, apollo, tavily, hubspot) -> ChatTurn:
    """One chat turn: ground via Sage, classify the outcome, and fire any terminal
    CRM action. CRM/enrichment failures degrade gracefully — the reply is always
    returned so the conversation never dies on an integration error."""
    state.add("user", message)

    sage = sage_answer(message, page=state.page, llm=llm, retriever=retriever)
    state.add("assistant", sage.reply)

    if sage.escalated:
        state.outcome = "escalate"
        return ChatTurn(session_id=state.session_id, reply=sage.reply, outcome="escalate",
                        escalated=True, booked=False, sources=[])

    decision = classify(state.history, state.signals, llm)
    state.signals.update(decision.signals)
    if decision.email and not state.email:
        state.email = decision.email
    state.outcome = decision.outcome

    booked = False
    try:
        if decision.outcome == "book" and state.email:
            state.crm = _book(state, apollo=apollo, llm=llm, tavily=tavily, hubspot=hubspot)
            booked = state.crm.stage == get_demo_stage()
        elif decision.outcome == "disqualify" and state.email:
            state.crm = _disqualify(state, decision.reason, hubspot=hubspot)
    except Exception:  # noqa: BLE001 — never let a CRM error break the chat reply
        logger.exception("chat CRM action failed for session %s", state.session_id)

    return ChatTurn(session_id=state.session_id, reply=sage.reply, outcome=state.outcome,
                    escalated=False, booked=booked, sources=sage.sources)


def get_demo_stage() -> str:
    from app.config import get_settings
    return get_settings().hubspot_stage_demo_requested
