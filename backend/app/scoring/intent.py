from __future__ import annotations

from app.scoring.models import IntentResult, Lead

# Form-path intent rubric (assumption — the profile has no intent table; kept small
# and honest because demo-form intent data is thin). Max 30.
PROBLEM_STATED_POINTS = 15
HOW_HEARD_POINTS = {
    "referral / word of mouth": 10,
    "referral": 10,
    "word of mouth": 10,
    "industry event": 10,
    "blog / content": 7,
    "blog": 7,
    "content": 7,
    "google search": 5,
    "google": 5,
    "linkedin": 5,
    "other": 0,
}


def _band(score: int) -> str:
    if score >= 20:
        return "high"
    if score >= 10:
        return "medium"
    return "low"


def score_intent(lead: Lead) -> IntentResult:
    score = 0
    known = False
    if lead.problem_stated and lead.problem_stated.strip():
        score += PROBLEM_STATED_POINTS
        known = True
    if lead.how_heard:
        known = True
        score += HOW_HEARD_POINTS.get(lead.how_heard.strip().lower(), 0)
    return IntentResult(score=score, band=_band(score), known=known)
