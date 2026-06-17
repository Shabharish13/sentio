from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.agents.research import _extract_json
from app.chat.models import OUTCOMES

# Visible, editable classifier prompt. It runs *after* Sage has answered the
# visitor, reading the whole transcript to decide whether a terminal outcome
# (book / nurture / escalate / disqualify) has been reached. Thresholds mirror
# prompts/sage_agent.md so the conversational agent and the router agree.
CLASSIFIER_PROMPT = """\
You are the qualification router behind Sentio's website assistant, Sage. Sentio
is a customer-health-scoring / churn-prediction platform for B2B SaaS CS teams.

Read the conversation transcript and decide the current outcome. Use ONLY what the
visitor actually said — never invent signals.

Collect these self-reported signals when present (omit if not yet revealed):
use_case, team_context, authority, timeline, company_scale, email.

Outcomes (pick exactly one):
- "book": EITHER (a) the visitor EXPLICITLY asks for a demo, to book/schedule a
  meeting, to get started, or uses similar direct purchase intent — trigger "book"
  immediately without requiring other qualifying signals; OR (b) company scale >= ~50
  people AND a champion/decision-maker role (CS leader, RevOps, C-suite) AND an
  active/this-quarter timeline. Requires the visitor's work email — set "email" when
  they have shared one.
- "disqualify": clearly outside the market — tiny/pre-revenue (<20, solo founder),
  non-commercial (student, personal project), or no CS function and no path to a
  buyer. Set "reason" to the specific disqualifier.
- "escalate": a GENUINE sales/human-handoff trigger only. Pick this ONLY when the
  visitor (a) explicitly asks to talk to a human or sales, OR (b) raises
  custom/enterprise/volume pricing, OR (c) wants to *initiate a process* that needs
  a person - e.g. "we need to run a security review", "send us your DPA / security
  questionnaire", "our procurement/legal team needs to engage", a data migration or
  custom integration project.
  CRITICAL: merely *asking a factual question* about security, compliance,
  certifications (e.g. "are you SOC 2 certified?", "are you GDPR compliant?",
  "do you support SSO?"), pricing, or features is NOT an escalation - Sage answers
  those from its knowledge base, so they are "continue". Escalate needs intent to
  involve a human, not just mention of a sensitive topic. Off-topic chatter, jokes,
  or unrelated questions are also "continue" (the assistant redirects them).
  ALSO NOT an escalation: wanting a demo, asking to "book a demo", "schedule a demo",
  or "get started". These are explicit booking signals — trigger "book" immediately
  without further qualification. Only route to a human via escalate for the
  (a)/(b)/(c) triggers above.
- "nurture": genuine interest but timeline is exploratory or company is below the
  Book threshold.
- "continue": none of the above yet (including off-topic messages) - keep
  qualifying or redirect.

Also choose the SINGLE next qualifying question to ask, as "next_question":
- On "continue" or "nurture", pick ONE binary (A-or-B) question targeting a signal
  NOT already in signals_so_far, phrased to feel natural given what was said.
  Suggested phrasing by signal:
  - use_case: "Is the main thing you're solving surprise churn, or giving your CS team a consistent view of account health?"
  - team_context: "Are you on a customer success team, or more of a RevOps / operations role?"
  - authority: "Are you evaluating this for your own team, or is there a broader group - finance, IT - who'd be involved?"
  - timeline: "Is this something you're actively solving this quarter, or still in early research?"
  - company_scale: "Are you working with a CS team of roughly 10 or fewer, or larger than that?"
- Set "next_question" to null on "book", "escalate", and "disqualify" - never qualify
  on a terminal turn - and whenever no question fits or every signal is collected.
- Never repeat a question for a signal already in signals_so_far. Do not ask about
  exact budget, headcount numbers, tech-stack, or security-questionnaire items.

Respond with exactly one JSON object and nothing else:
{"signals": {"use_case": "...", "timeline": "..."}, "outcome": "book",
 "email": "jane@acme.com", "reason": null, "next_question": null}
Include only the signal keys you actually have. Use null for email/reason/next_question
when absent.
"""


# Ordered deterministic fallback questions, one per qualifying signal. Used when the
# LLM omits next_question on a non-terminal turn so qualification never silently
# stalls. Phrasing mirrors the suggestions in CLASSIFIER_PROMPT above.
_FALLBACK_QUESTIONS: list[tuple[str, str]] = [
    ("use_case", "Is the main thing you're solving surprise churn, or giving your CS team a consistent view of account health?"),
    ("team_context", "Are you on a customer success team, or more of a RevOps / operations role?"),
    ("authority", "Are you evaluating this for your own team, or is there a broader group - finance, IT - who'd be involved?"),
    ("timeline", "Is this something you're actively solving this quarter, or still in early research?"),
    ("company_scale", "Are you working with a CS team of roughly 10 or fewer, or larger than that?"),
]


def _fallback_question(known: dict[str, str]) -> str | None:
    """First qualifying question whose signal has not been collected yet."""
    for signal, question in _FALLBACK_QUESTIONS:
        if not known.get(signal):
            return question
    return None


@dataclass
class OutcomeDecision:
    outcome: str = "continue"
    signals: dict[str, str] = field(default_factory=dict)
    email: str | None = None
    reason: str | None = None
    # The single qualifying question to ask next, owned by the router (not Sage) so it
    # can never contradict the outcome. Always None on a terminal outcome.
    next_question: str | None = None


def classify(history: list[dict[str, str]], signals: dict[str, str], llm) -> OutcomeDecision:
    """One structured LLM call over the transcript → routing decision."""
    user = json.dumps(
        {"transcript": history, "signals_so_far": signals},
        indent=2,
        default=str,
    )
    raw = llm.complete(CLASSIFIER_PROMPT, user, max_tokens=500)
    data = _extract_json(raw)

    outcome = data.get("outcome", "continue")
    if outcome not in OUTCOMES:
        outcome = "continue"

    parsed = data.get("signals") or {}
    merged = {k: v for k, v in parsed.items() if isinstance(v, str) and v.strip()}

    email = data.get("email")
    if not isinstance(email, str) or "@" not in email:
        email = None

    reason = data.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = None

    next_question = data.get("next_question")
    if not isinstance(next_question, str) or not next_question.strip():
        next_question = None
    else:
        next_question = next_question.strip()
    # A terminal outcome never carries a qualifying question (clean close, even if the
    # model emits one). On a non-terminal turn, guarantee a question deterministically
    # when the model omitted it, so qualification always advances.
    if outcome in ("book", "escalate", "disqualify"):
        next_question = None
    elif next_question is None:
        next_question = _fallback_question({**signals, **merged})

    return OutcomeDecision(outcome=outcome, signals=merged, email=email, reason=reason,
                           next_question=next_question)
