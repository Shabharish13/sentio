from __future__ import annotations

from app.scoring.fit import score_fit
from app.scoring.intent import score_intent
from app.scoring.models import Lead, ScoreResult


def _disqualification_reason(breakdown: dict[str, int], score: int) -> str:
    parts = ", ".join(f"{dim}={pts}" for dim, pts in breakdown.items())
    weak = [dim for dim, pts in breakdown.items() if pts == 0]
    weak_note = f" Weak dimensions: {', '.join(weak)}." if weak else ""
    return f"ICP fit C (score {score}). Breakdown: {parts}.{weak_note}"


def score_lead(lead: Lead) -> ScoreResult:
    """Run the deterministic pipeline: fit + intent + routing/exit gate.

    C-grade leads are routed to the disqualified path (skip Research/Copywriter)
    with a human-readable reason; A/B grades proceed (qualified).
    """
    fit = score_fit(lead)
    intent = score_intent(lead)
    if fit.grade == "C":
        return ScoreResult(
            fit=fit,
            intent=intent,
            route="disqualified",
            disqualification_reason=_disqualification_reason(fit.breakdown, fit.score),
        )
    return ScoreResult(fit=fit, intent=intent, route="qualified", disqualification_reason=None)
