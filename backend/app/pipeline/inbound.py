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


def _handoff_note(score, research, email_body: str) -> str:
    return (
        f"SDR hand-off — persona: {score.fit.stakeholder}; "
        f"ICP: {score.fit.grade}/{score.fit.score}; "
        f"intent: {score.intent.score} ({score.intent.band}); "
        f"why-now: {research.top_signal or 'none'} ({research.signal_type}); "
        f"source: {research.source_url or 'n/a'}.\n\nDraft email (for SDR review):\n{email_body}"
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
    props = contact_props(form)
    org_fields = org.get("organization") or {}
    person_fields = person.get("person") or {}
    full_name = f"{form.get('first_name', '')} {form.get('last_name', '')}".strip()
    display = dict(
        contact_name=full_name,
        contact_title=form.get("job_title") or person_fields.get("title") or "",
        contact_email=email,
        company_name=form.get("company_name") or "",
        headcount=lead.headcount,
        industry=org_fields.get("industry"),
        revenue=org_fields.get("annual_revenue") or org_fields.get("organization_revenue"),
        enriched=bool(org_fields),
    )

    if score.route == "disqualified":
        crm = sync_to_crm(email=email, contact_props=props, deal_name=name,
                          route="disqualified", note_body=score.disqualification_reason, hubspot=hubspot)
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
    note = _handoff_note(score, research, email_body)
    crm = sync_to_crm(email=email, contact_props=props, deal_name=name,
                      route="qualified", note_body=note, hubspot=hubspot)
    return PipelineResult(
        route="qualified", fit_grade=score.fit.grade, fit_score=score.fit.score,
        stakeholder=score.fit.stakeholder, intent_score=score.intent.score,
        signal_type=research.signal_type, top_signal=research.top_signal,
        email_draft=email_body, disqualification_reason=None, crm=crm,
        source_url=research.source_url, **display,
    )
