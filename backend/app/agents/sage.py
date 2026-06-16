from __future__ import annotations

from dataclasses import dataclass

from app.agents.research import _extract_json
from app.clients.anthropic_client import load_prompt

# Off-topic / low-retrieval-confidence reply. Not an escalation: Sage stays in the
# conversation and steers the visitor back to Sentio topics (see sage_agent.md).
REDIRECT_MESSAGE = (
    "I'm Sentio's assistant, so I can only really help with questions about "
    "Sentio - how we score account health, predict churn, what's in each plan, "
    "and whether we're a fit for your team. Is there anything along those lines "
    "I can help with?"
)
# Calibrated empirically for the all-MiniLM-L6-v2 embedder against the real KB:
# on-topic queries score ~0.52-0.55, off-topic ~0.12-0.22 cosine similarity, so
# 0.35 sits in the gap. (The prompt's nominal 0.75 assumed a different embedder.)
CONFIDENCE_THRESHOLD = 0.35


@dataclass(frozen=True)
class SageResponse:
    answer: str
    question: str | None
    redirected: bool
    sources: list[str]


def answer(message: str, page: str, llm, retriever,
           threshold: float = CONFIDENCE_THRESHOLD, k: int = 4) -> SageResponse:
    """Grounded chat turn: retrieve KB context, redirect off-topic when the top
    cosine score is below threshold (or nothing retrieved), otherwise answer via
    the Sage prompt and parse the structured {answer, question} JSON."""
    chunks = retriever.retrieve(message, k=k)
    top_score = chunks[0].score if chunks else 0.0
    if not chunks or top_score < threshold:
        return SageResponse(answer=REDIRECT_MESSAGE, question=None,
                            redirected=True, sources=[])

    context = "\n\n".join(f"[{c.source}] {c.text}" for c in chunks)
    system = load_prompt("sage_agent.md").replace("{context}", context).replace("{page}", page)
    raw = llm.complete(system, message, max_tokens=400)

    data = _extract_json(raw)
    answer_text = data.get("answer")
    if not isinstance(answer_text, str) or not answer_text.strip():
        # Model did not return the structured object - fall back to the raw text
        # so the visitor still gets a reply, with no separate question.
        answer_text = raw.strip()
        question = None
    else:
        answer_text = answer_text.strip()
        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            question = None
        else:
            question = question.strip()

    return SageResponse(answer=answer_text, question=question, redirected=False,
                        sources=[c.source for c in chunks])
