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


def test_b_grade_within_icp_routes_qualified():
    """B-grade lead with headcount inside the 100–800 band → qualified."""
    lead = Lead(
        headcount=350,
        industry="Telecommunications",
        title="Customer Success Manager",
        country="Canada",
        is_b2b=True,
    )
    result = score_lead(lead)
    assert result.fit.grade == "B"
    assert result.route == "qualified"
    assert result.disqualification_reason is None


def test_oversized_b_grade_routes_edge_fit():
    """B-grade lead with headcount > 800 → edge_fit (not a clean qualified)."""
    lead = Lead(
        headcount=1100,
        industry="Computer Software",
        title="VP of Revenue Operations",
        country="United States",
        is_b2b=True,
    )
    result = score_lead(lead)
    assert result.route == "edge_fit"
    assert result.disqualification_reason is not None
    assert "1100" in result.disqualification_reason
    assert "800" in result.disqualification_reason


def test_a_grade_oversized_still_routes_qualified():
    """An A-grade lead above 800 employees is still qualified — edge_fit only applies to B."""
    lead = Lead(
        headcount=900,
        industry="Computer Software",
        title="VP of Customer Success",
        country="United States",
        technologies=["HubSpot"],
        is_b2b=True,
        problem_stated="surprise churn",
    )
    result = score_lead(lead)
    assert result.fit.grade == "A"
    assert result.route == "qualified"


def test_c_grade_routes_disqualified_with_reason():
    lead = Lead(headcount=20, industry="Construction", title="Office Manager", country="India")
    result = score_lead(lead)
    assert result.fit.grade == "C"
    assert result.route == "disqualified"
    assert result.disqualification_reason is not None
    assert "ICP fit C" in result.disqualification_reason
    assert "headcount" in result.disqualification_reason
