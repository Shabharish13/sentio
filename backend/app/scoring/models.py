from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lead:
    """Normalized scoring input (decoupled from Apollo's raw response shape)."""

    headcount: int | None = None
    industry: str | None = None
    title: str | None = None
    country: str | None = None
    technologies: list[str] = field(default_factory=list)
    is_b2b: bool = False
    # form-path intent inputs
    problem_stated: str = ""
    how_heard: str | None = None


@dataclass(frozen=True)
class FitResult:
    score: int
    grade: str  # "A" | "B" | "C"
    stakeholder: str  # champion | economic_buyer | technical | end_user | combined | other
    breakdown: dict[str, int]


@dataclass(frozen=True)
class IntentResult:
    score: int
    band: str  # high | medium | low
    known: bool


@dataclass(frozen=True)
class ScoreResult:
    fit: FitResult
    intent: IntentResult
    route: str  # qualified | disqualified
    disqualification_reason: str | None
