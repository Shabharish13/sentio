import json
import re

from app.agents.copywriter import STAKEHOLDER_FRAMES, build_brief, write_email
from app.agents.models import ResearchBrief
from app.scoring.models import FitResult, IntentResult


class StubLLM:
    def __init__(self, reply):
        self._reply = reply
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._reply


def _fit(stakeholder="champion", grade="A"):
    return FitResult(score=95, grade=grade, stakeholder=stakeholder,
                     breakdown={"headcount": 25})


def test_build_brief_selects_frame_and_maps_research():
    brief = build_brief(
        contact={"first_name": "Jane", "name": "Jane Doe", "title": "VP CS"},
        company={"name": "Meridian", "headcount": 200, "industry": "Computer Software"},
        fit=_fit("economic_buyer"),
        intent=IntentResult(score=25, band="high", known=True),
        research=ResearchBrief("Raised Series B", "funding", "https://x"),
        problem_stated="surprise churn",
    )
    assert brief["stakeholder_type"] == "economic_buyer"
    assert brief["email_frame"] == STAKEHOLDER_FRAMES["economic_buyer"]
    assert brief["fit_grade"] == "A"
    assert brief["intent_score"] == 25
    assert brief["research"]["signal_type"] == "funding"
    assert brief["problem_stated"] == "surprise churn"


def test_unknown_stakeholder_uses_other_frame():
    brief = build_brief(contact={}, company={}, fit=_fit("mystery"),
                        intent=IntentResult(0, "low", False),
                        research=ResearchBrief(None, "none", None))
    assert brief["email_frame"] == STAKEHOLDER_FRAMES["other"]


def test_write_email_calls_llm_with_copywriter_prompt_and_returns_body():
    llm = StubLLM("Hi Jane,\n\nNoticed your Series B...\n\nBest,\nAlex")
    brief = {"contact": {"first_name": "Jane"}, "fit_grade": "A"}
    out = write_email(brief, llm=llm)
    assert out.startswith("Hi Jane")
    system, user = llm.calls[0]
    assert "outreach" in system.lower() or "copywriter" in system.lower()
    assert json.loads(user)["fit_grade"] == "A"


def test_build_brief_includes_sender_name_and_booking_link():
    brief = build_brief(
        contact={"first_name": "Jane", "name": "Jane Doe", "title": "VP CS"},
        company={"name": "Meridian", "headcount": 200, "industry": "Computer Software"},
        fit=_fit("champion"),
        intent=IntentResult(score=20, band="high", known=True),
        research=ResearchBrief(None, "none", None),
    )
    assert "sender_name" in brief
    assert brief["sender_name"]  # non-empty
    assert "booking_link" in brief
    assert brief["booking_link"].startswith("http")


def test_write_email_strips_unfilled_placeholders():
    llm = StubLLM("Hi Jane,\n\nGood stuff.\n\nBest,\n[SDR first name]")
    brief = {"contact": {"first_name": "Jane"}, "fit_grade": "A",
             "sender_name": "Alex", "booking_link": "https://calendly.com/sentio/15min"}
    out = write_email(brief, llm=llm)
    assert not re.search(r'\[[A-Za-z ]+\]', out), f"placeholder not stripped: {out!r}"


def test_write_email_preserves_needs_verification_tag():
    """[NEEDS VERIFICATION] is intentional — must NOT be stripped."""
    llm = StubLLM(
        "Hi Jane,\n\nWe help companies like yours [NEEDS VERIFICATION].\n\nBest,\nAlex"
    )
    brief = {"contact": {"first_name": "Jane"}, "fit_grade": "A",
             "sender_name": "Alex", "booking_link": "https://calendly.com/sentio/15min"}
    out = write_email(brief, llm=llm)
    assert "[NEEDS VERIFICATION]" in out
