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
- "book": company scale >= ~50 people AND a champion/decision-maker role
  (CS leader, RevOps, C-suite) AND an active/this-quarter timeline. Requires the
  visitor's work email — set "email" when they have shared one.
- "disqualify": clearly outside the market — tiny/pre-revenue (<20, solo founder),
  non-commercial (student, personal project), or no CS function and no path to a
  buyer. Set "reason" to the specific disqualifier.
- "escalate": a GENUINE sales-handoff trigger only - the visitor explicitly asks
  to talk to a human/sales, OR raises custom/enterprise/volume pricing, OR raises
  security review / legal / procurement / DPA / data migration / custom
  integrations. Off-topic chatter, jokes, or unrelated questions are NOT an
  escalation - those are just "continue" (the assistant redirects them).
- "nurture": genuine interest but timeline is exploratory or company is below the
  Book threshold.
- "continue": none of the above yet (including off-topic messages) - keep
  qualifying or redirect.

Respond with exactly one JSON object and nothing else:
{"signals": {"use_case": "...", "timeline": "..."}, "outcome": "book",
 "email": "jane@acme.com", "reason": null}
Include only the signal keys you actually have. Use null for email/reason when absent.
"""


@dataclass
class OutcomeDecision:
    outcome: str = "continue"
    signals: dict[str, str] = field(default_factory=dict)
    email: str | None = None
    reason: str | None = None


def classify(history: list[dict[str, str]], signals: dict[str, str], llm) -> OutcomeDecision:
    """One structured LLM call over the transcript → routing decision."""
    user = json.dumps(
        {"transcript": history, "signals_so_far": signals},
        indent=2,
        default=str,
    )
    raw = llm.complete(CLASSIFIER_PROMPT, user, max_tokens=300)
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

    return OutcomeDecision(outcome=outcome, signals=merged, email=email, reason=reason)
