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

# How many prior turns to feed back into retrieval and the prompt. Enough for
# continuity on a short widget chat, bounded so the reply stays fast and small.
HISTORY_TURNS = 6


@dataclass(frozen=True)
class SageResponse:
    answer: str
    redirected: bool
    sources: list[str]


def _retrieval_query(message: str, history: list[dict[str, str]]) -> str:
    """Anchor retrieval to the last thing Sage said. A short reply to Sage's own
    question ("asap", "yes, this quarter") carries no Sentio keywords, so retrieving
    on it alone scores as off-topic and trips the redirect - bouncing a visitor who
    is actually answering us. Prepending the last assistant turn keeps the follow-up
    in the context of the conversation it belongs to."""
    last_assistant = next(
        (m["content"] for m in reversed(history) if m["role"] == "assistant"), "")
    return f"{last_assistant}\n{message}".strip() if last_assistant else message


def _user_turn(message: str, history: list[dict[str, str]]) -> str:
    """The visitor message the model sees, prefixed with recent conversation so it can
    resolve follow-ups ("as soon as possible" -> active timeline) instead of reading
    each message in isolation. Bare message when there is no history (turn one)."""
    if not history:
        return message
    lines = [f"{m['role']}: {m['content']}" for m in history[-HISTORY_TURNS:]]
    lines.append(f"user: {message}")
    return "\n".join(lines)


def answer(message: str, page: str, llm, retriever, history: list[dict[str, str]] | None = None,
           threshold: float = CONFIDENCE_THRESHOLD, k: int = 4) -> SageResponse:
    """Grounded chat turn: retrieve KB context, redirect off-topic when the top
    cosine score is below threshold (or nothing retrieved), otherwise answer via the
    Sage prompt and parse the structured {answer, off_topic} JSON. Sage only answers -
    the next qualifying question is owned by the router (see app/chat/outcome.py), so it
    can never contradict the outcome. `history` is the prior turns (excluding this
    message); it anchors both retrieval and the model so a follow-up answering Sage's
    own question is not read in isolation."""
    history = history or []
    chunks = retriever.retrieve(_retrieval_query(message, history), k=k)
    top_score = chunks[0].score if chunks else 0.0
    if not chunks or top_score < threshold:
        return SageResponse(answer=REDIRECT_MESSAGE, redirected=True, sources=[])

    context = "\n\n".join(f"[{c.source}] {c.text}" for c in chunks)
    system = load_prompt("sage_agent.md").replace("{context}", context).replace("{page}", page)
    # Minimal reasoning: the reply is grounded recall on the visitor's critical path,
    # so depth of reasoning buys nothing but latency. Action-deciding calls (the
    # classifier, research, copywriter) keep the model default off the reply path.
    raw = llm.complete(system, _user_turn(message, history), max_tokens=400,
                       reasoning_effort="minimal")

    data = _extract_json(raw)
    # The retrieval gate above only catches clearly off-topic queries (low cosine).
    # Semantically-adjacent-but-out-of-scope asks ("write a poem about a CSM") clear
    # the threshold, so the LLM is the component that recognises them - it signals
    # that via off_topic, which we surface as a redirect (see sage_agent.md).
    off_topic = data.get("off_topic") is True
    answer_text = data.get("answer")
    if not isinstance(answer_text, str) or not answer_text.strip():
        # Model did not return the structured object - fall back to the raw text so the
        # visitor still gets a reply.
        answer_text = raw.strip()
    else:
        answer_text = answer_text.strip()

    return SageResponse(answer=answer_text, redirected=off_topic,
                        sources=[] if off_topic else [c.source for c in chunks])
