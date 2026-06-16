from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResearchBrief:
    top_signal: str | None
    signal_type: str  # funding|rapid_growth|tech_fit|competitor_displacement|exec_hire|job_posting|retention_signal|none
    source_url: str | None


@dataclass(frozen=True)
class CrmResult:
    contact_id: str
    deal_id: str
    stage: str
    note_id: str
