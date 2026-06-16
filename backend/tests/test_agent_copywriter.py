import json

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
