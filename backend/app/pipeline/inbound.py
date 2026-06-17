from __future__ import annotations

from app.agents.copywriter import build_brief, write_email
from app.agents.crm import sync_to_crm
from app.agents.research import run_research
from app.pipeline.adapter import (
    build_lead,
    build_record,
    contact_props,
    deal_name,
    email_domain,
)
from app.pipeline.models import PipelineResult
from app.scoring.engine import score_lead


def _format_revenue(value) -> str | None:
    """Apollo returns annual_revenue as a number; the brief shows a readable
    string. Format to $X.XB / $X.XM; pass through any non-numeric value as-is."""
    if value is None or value == "":
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    return f"${amount:,.0f}"


def _deal_priority(grade: str) -> str:
    if grade == "A":
        return "HIGH"
    if grade == "B":
        return "MEDIUM"
    return "LOW"


def _handoff_note(score, research, email_body: str, display: dict) -> str:
    company   = display.get("company_name") or "Unknown"
    industry  = display.get("industry") or "n/a"
    headcount = display.get("headcount") or "n/a"
    revenue   = display.get("revenue") or "n/a"
    c_name    = display.get("contact_name") or "Unknown"
    c_title   = display.get("contact_title") or "n/a"

    score_detail = "  ".join(
        f"{k.replace('_', ' ').title()} {v}pts"
        for k, v in score.fit.breakdown.items()
    )

    if research.top_signal:
        signal_block = (
            f"\nWHY NOW - {research.signal_type.upper()}\n"
            f"  {research.top_signal}\n"
            f"  Source: {research.source_url or 'n/a'}"
        )
    else:
        signal_block = "\nWHY NOW - no signal found (lead with company stage and vertical)"

    edge_block = (
        "\n*** EDGE FIT - headcount above ICP sweet spot. "
        "Confirm a strong CS champion before outreach. ***"
        if score.route == "edge_fit" else ""
    )

    return (
        f"=== SDR HAND-OFF ===\n"
        f"\nCOMPANY\n"
        f"  {company}  |  {industry}  |  {headcount} employees  |  ARR {revenue}\n"
        f"\nCONTACT\n"
        f"  {c_name}  -  {c_title}\n"
        f"  Buyer type: {score.fit.stakeholder}\n"
        f"\nICP SCORE: {score.fit.grade}  ({score.fit.score}/100)  |  "
        f"Intent: {score.intent.score} ({score.intent.band})\n"
        f"  {score_detail}"
        f"{edge_block}"
        f"{signal_block}\n"
        f"\nDRAFT EMAIL - review before sending\n"
        f"{'-' * 40}\n"
        f"{email_body}\n"
        f"{'-' * 40}"
    )


def run_inbound_pipeline(form: dict, *, apollo, llm, tavily, hubspot) -> PipelineResult:
    """Inbound pipeline: exit check -> enrich -> score -> route -> (research ->
    copywriter -> CRM) for A/B, or straight to a disqualified deal for C."""
    email = (form.get("work_email") or "").strip()
    if not email or "@" not in email:
        raise ValueError("exit check: a valid work_email is required")

    domain = email_domain(email)
    org = apollo.enrich_organization(domain) if domain else {"organization": {}}
    person = apollo.enrich_person(email, first_name=form.get("first_name"),
                                  last_name=form.get("last_name"), domain=domain)

    lead = build_lead(form, org, person)
    score = score_lead(lead)

    name = deal_name(form)
    props = contact_props(form, org)
    org_fields = org.get("organization") or {}
    person_fields = person.get("person") or {}
    annual_revenue = org_fields.get("annual_revenue") or org_fields.get("organization_revenue")
    full_name = f"{form.get('first_name', '')} {form.get('last_name', '')}".strip()
    display = dict(
        contact_name=full_name,
        contact_title=form.get("job_title") or person_fields.get("title") or "",
        contact_email=email,
        company_name=form.get("company_name") or "",
        headcount=lead.headcount,
        industry=org_fields.get("industry"),
        revenue=_format_revenue(org_fields.get("annual_revenue") or org_fields.get("organization_revenue")),
        enriched=bool(org_fields),
    )

    if score.route == "disqualified":
        crm = sync_to_crm(email=email, contact_props=props, deal_name=name,
                          route="disqualified", note_body=score.disqualification_reason,
                          deal_priority="LOW", annual_revenue=annual_revenue, hubspot=hubspot)
        return PipelineResult(
            route="disqualified", fit_grade=score.fit.grade, fit_score=score.fit.score,
            stakeholder=score.fit.stakeholder, intent_score=score.intent.score,
            signal_type="none", top_signal=None, email_draft=None,
            disqualification_reason=score.disqualification_reason, crm=crm, **display,
        )

    record = build_record(form, org, person)
    research = run_research(record, llm=llm, tavily=tavily)
    brief = build_brief(
        contact=record["contact"], company=record["company"],
        fit=score.fit, intent=score.intent, research=research,
        problem_stated=form.get("problem_stated") or "",
    )
    email_body = write_email(brief, llm=llm)
    note = _handoff_note(score, research, email_body, display)

    crm = sync_to_crm(email=email, contact_props=props, deal_name=name,
                      route=score.route, note_body=note,
                      deal_priority=_deal_priority(score.fit.grade),
                      annual_revenue=annual_revenue, hubspot=hubspot)
    return PipelineResult(
        route=score.route, fit_grade=score.fit.grade, fit_score=score.fit.score,
        stakeholder=score.fit.stakeholder, intent_score=score.intent.score,
        signal_type=research.signal_type, top_signal=research.top_signal,
        email_draft=email_body, disqualification_reason=score.disqualification_reason,
        crm=crm, source_url=research.source_url, **display,
    )
