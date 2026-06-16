from app.scoring.engine import score_lead
from app.scoring.models import Lead


def test_qualified_a_grade_routes_qualified():
    lead = Lead(
        headcount=200,
        industry="Computer Software",
        title="VP of Customer Success",
        country="United States",
        technologies=["HubSpot"],
        is_b2b=True,
        problem_stated="surprise churn",
        how_heard="Referral",
    )
    result = score_lead(lead)
    assert result.fit.grade == "A"
    assert result.route == "qualified"
    assert result.disqualification_reason is None
    assert result.intent.score == 25


def test_b_grade_routes_qualified():
    lead = Lead(
        headcount=1000,
        industry="Telecommunications",
        title="Customer Success Manager",
        country="Canada",
        is_b2b=True,
    )
    result = score_lead(lead)
    assert result.fit.grade == "B"
    assert result.route == "qualified"
    assert result.disqualification_reason is None


def test_c_grade_routes_disqualified_with_reason():
    lead = Lead(headcount=20, industry="Construction", title="Office Manager", country="India")
    result = score_lead(lead)
    assert result.fit.grade == "C"
    assert result.route == "disqualified"
    assert result.disqualification_reason is not None
    assert "ICP fit C" in result.disqualification_reason
    assert "headcount" in result.disqualification_reason
