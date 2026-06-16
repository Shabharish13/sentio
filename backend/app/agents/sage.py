from __future__ import annotations

from dataclasses import dataclass

from app.clients.anthropic_client import load_prompt

# Canned escalation line from sage_agent.md's confidence-threshold rule.
ESCALATION_MESSAGE = (
    "That's a great question — I want to make sure you get accurate information. "
    "Let me connect you with our team."
)
CONFIDENCE_THRESHOLD = 0.75


@dataclass(frozen=True)
class SageResponse:
    reply: str
    escalated: bool
    sources: list[str]


def answer(message: str, page: str, llm, retriever,
           threshold: float = CONFIDENCE_THRESHOLD, k: int = 4) -> SageResponse:
    """Grounded chat turn: retrieve KB context, escalate when the top cosine score
    is below threshold (or nothing retrieved), otherwise answer via the Sage prompt."""
    chunks = retriever.retrieve(message, k=k)
    top_score = chunks[0].score if chunks else 0.0
    if not chunks or top_score < threshold:
        return SageResponse(reply=ESCALATION_MESSAGE, escalated=True, sources=[])

    context = "\n\n".join(f"[{c.source}] {c.text}" for c in chunks)
    system = load_prompt("sage_agent.md").replace("{context}", context).replace("{page}", page)
    reply = llm.complete(system, message, max_tokens=400).strip()
    return SageResponse(reply=reply, escalated=False, sources=[c.source for c in chunks])
