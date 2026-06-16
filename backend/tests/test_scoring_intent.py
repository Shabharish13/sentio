from app.scoring.intent import score_intent
from app.scoring.models import Lead


def test_high_intent_problem_and_warm_source():
    lead = Lead(
        problem_stated="We keep losing accounts at renewal",
        how_heard="Referral / word of mouth",
    )
    result = score_intent(lead)
    assert result.score == 25  # 15 + 10
    assert result.band == "high"
    assert result.known is True


def test_low_intent_cold_source_no_problem():
    lead = Lead(problem_stated="", how_heard="Google search")
    result = score_intent(lead)
    assert result.score == 5
    assert result.band == "low"
    assert result.known is True


def test_unknown_intent_when_no_signals():
    result = score_intent(Lead())
    assert result.score == 0
    assert result.band == "low"
    assert result.known is False


def test_medium_band_boundary():
    result = score_intent(Lead(problem_stated="surprise churn is hurting us"))
    assert result.score == 15
    assert result.band == "medium"
    assert result.known is True
