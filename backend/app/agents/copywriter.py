from __future__ import annotations

import json
import re

from app.clients.anthropic_client import load_prompt
from app.config import get_settings

# Persona email frames (from sentio-company-profile.md). The Copywriter prompt
# expects a pre-selected `email_frame` sentence keyed off the stakeholder type.
STAKEHOLDER_FRAMES = {
    "champion": "Efficiency, playbook consistency, CSM capacity — your CSMs shouldn't learn about churn risk from the customer.",
    "economic_buyer": "ROI and NRR in dollar terms — every point of NRR at $10M ARR is six figures in retained revenue.",
    "technical": "Integrations, SOC 2, no-code setup — connects to your existing stack in under a day, no custom ETL.",
    "end_user": "Day-to-day workflow and time saved — know which accounts to call today without an hour of digging.",
    "combined": "Business outcome plus simplicity — a CS intelligence layer you can stand up before your second CSM.",
    "other": "Company stage and vertical — why churn risk is acute at this stage.",
}

# Matches unfilled merge-field placeholders like [SDR first name] or [Name],
# but not [NEEDS VERIFICATION] which is an intentional data-quality marker.
_PLACEHOLDER_RE = re.compile(r'\[(?!NEEDS VERIFICATION\b)[A-Za-z][A-Za-z ]{0,39}\]')


def build_brief(contact, company, fit, intent, research, problem_stated: str = "") -> dict:
    """Assemble the structured brief the Copywriter prompt consumes."""
    settings = get_settings()
    return {
        "contact": contact,
        "company": company,
        "fit_grade": fit.grade,
        "intent_score": intent.score,
        "stakeholder_type": fit.stakeholder,
        "email_frame": STAKEHOLDER_FRAMES.get(fit.stakeholder, STAKEHOLDER_FRAMES["other"]),
        "research": {
            "top_signal": research.top_signal,
            "signal_type": research.signal_type,
            "source_url": research.source_url,
        },
        "problem_stated": problem_stated,
        "sender_name": settings.sdr_sender_name,
        "booking_link": settings.sdr_booking_link,
    }


def write_email(brief: dict, llm) -> str:
    """Generate the SDR-review email body from the brief (sourced facts only)."""
    system = load_prompt("copywriter_agent.md")
    user = json.dumps(brief, indent=2, default=str)
    raw = llm.complete(system, user, max_tokens=600).strip()
    # Strip any unfilled merge-field placeholders the LLM may have emitted.
    return _PLACEHOLDER_RE.sub("", raw).strip()
