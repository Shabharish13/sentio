from __future__ import annotations

from dataclasses import dataclass

from app.agents.models import CrmResult


@dataclass(frozen=True)
class PipelineResult:
    route: str
    fit_grade: str
    fit_score: int
    stakeholder: str
    intent_score: int
    signal_type: str
    top_signal: str | None
    email_draft: str | None
    disqualification_reason: str | None
    crm: CrmResult
