from __future__ import annotations

from app.scoring.fit import score_fit
from app.scoring.intent import score_intent
from app.scoring.models import Lead, ScoreResult

# ICP upper headcount boundary above which B-grade leads are flagged for SDR review.
_ICP_HEADCOUNT_CEILING = 800


def _disqualification_reason(breakdown: dict[str, int], score: int) -> str:
    parts = ", ".join(f"{dim}={pts}" for dim, pts in breakdown.items())
    weak = [dim for dim, pts in breakdown.items() if pts == 0]
    weak_note = f" Weak dimensions: {', '.join(weak)}." if weak else ""
    return f"ICP fit C (score {score}). Breakdown: {parts}.{weak_note}"


def _edge_fit_note(headcount: int) -> str:
    return (
        f"Edge ICP fit — headcount {headcount} is above the 100–800 employee sweet spot. "
        "Research and email generated for SDR review; verify a strong champion exists before outreach."
    )


def score_lead(lead: Lead) -> ScoreResult:
    """Run the deterministic pipeline: fit + intent + routing/exit gate.

    C-grade leads are routed to disqualified; A-grade are qualified; B-grade leads
    with headcount above the ICP ceiling are routed to edge_fit for SDR review.
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

    if fit.grade == "B" and lead.headcount and lead.headcount > _ICP_HEADCOUNT_CEILING:
        return ScoreResult(
            fit=fit,
            intent=intent,
            route="edge_fit",
            disqualification_reason=_edge_fit_note(lead.headcount),
        )

    return ScoreResult(fit=fit, intent=intent, route="qualified", disqualification_reason=None)
