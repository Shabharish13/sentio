from app.scoring.fit import (
    grade_for,
    score_business_model,
    score_fit,
    score_geography,
    score_headcount,
    score_industry,
    score_title,
)
from app.scoring.models import Lead


def test_headcount_bands():
    assert score_headcount(200) == 25
    assert score_headcount(500) == 20
    assert score_headcount(75) == 10
    assert score_headcount(1500) == 5
    assert score_headcount(30) == 0
    assert score_headcount(5000) == 0
    assert score_headcount(None) == 0


def test_industry_plain_and_financial_disambiguation():
    assert score_industry("Computer Software", []) == 20
    assert score_industry("Internet", []) == 18
    assert score_industry("Construction", []) == 0
    assert score_industry("Financial Services", ["API", "Stripe"]) == 15
    assert score_industry("Financial Services", ["Oracle", "SAP"]) == 5
    assert score_industry(None, []) == 0


def test_geography():
    assert score_geography("United States") == 15
    assert score_geography("Canada") == 12
    assert score_geography("Australia") == 10
    assert score_geography("Germany") == 7
    assert score_geography("India") == 0
    assert score_geography(None) == 0


def test_business_model():
    assert score_business_model(Lead(is_b2b=True, industry="Computer Software")) == 15
    assert score_business_model(Lead(is_b2b=True, technologies=["API"])) == 15
    assert score_business_model(Lead(is_b2b=True, industry="Telecommunications")) == 10
    assert score_business_model(Lead(is_b2b=False)) == 0


def test_title_points_and_stakeholder():
    assert score_title("VP of Customer Success") == (20, "champion")
    assert score_title("Director of Customer Success") == (18, "champion")
    assert score_title("Chief Revenue Officer") == (15, "economic_buyer")
    assert score_title("CFO") == (12, "economic_buyer")
    assert score_title("CTO") == (0, "technical")
    assert score_title("Founder") == (0, "combined")
    assert score_title("Customer Success Manager") == (8, "end_user")
    assert score_title("Office Manager") == (0, "other")
    assert score_title(None) == (0, "other")


def test_grade_thresholds():
    assert grade_for(60) == "A"
    assert grade_for(85) == "A"
    assert grade_for(59) == "B"
    assert grade_for(30) == "B"
    assert grade_for(29) == "C"
    assert grade_for(0) == "C"


def test_score_fit_grade_a():
    lead = Lead(
        headcount=200,
        industry="Computer Software",
        title="VP of Customer Success",
        country="United States",
        technologies=["HubSpot"],
        is_b2b=True,
    )
    fit = score_fit(lead)
    assert fit.score == 95
    assert fit.grade == "A"
    assert fit.stakeholder == "champion"
    assert fit.breakdown["industry"] == 20


def test_score_fit_grade_b():
    lead = Lead(
        headcount=1000,
        industry="Telecommunications",
        title="Customer Success Manager",
        country="Canada",
        is_b2b=True,
    )
    fit = score_fit(lead)
    assert fit.score == 40
    assert fit.grade == "B"
    assert fit.stakeholder == "end_user"


def test_score_fit_grade_c():
    lead = Lead(headcount=20, industry="Construction", title="Office Manager", country="India")
    fit = score_fit(lead)
    assert fit.score == 0
    assert fit.grade == "C"
    assert fit.stakeholder == "other"


def test_title_no_false_positive_from_substring():
    # "cro" must not match inside "microservices"; "cto" must not match inside "director"
    assert score_title("Director of Microservices") == (0, "other")
    assert score_title("Director of Customer Operations") == (0, "other")
