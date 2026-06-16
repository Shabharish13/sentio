from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.models import CrmResult

# Outcomes Sage can reach (see prompts/sage_agent.md). "continue" means keep
# qualifying — no terminal action this turn.
OUTCOMES = {"continue", "book", "nurture", "escalate", "disqualify"}


@dataclass
class QualificationState:
    """Server-side state for one chat session, updated after every turn."""

    session_id: str
    page: str
    history: list[dict[str, str]] = field(default_factory=list)
    signals: dict[str, str] = field(default_factory=dict)
    outcome: str = "continue"
    email: str | None = None
    crm: CrmResult | None = None

    def add(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})

    def transcript(self) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in self.history)


@dataclass(frozen=True)
class ChatTurn:
    """Result of a single chat turn returned to the API layer."""

    session_id: str
    reply: str
    outcome: str
    escalated: bool
    booked: bool
    sources: list[str]
