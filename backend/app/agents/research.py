from __future__ import annotations

import json

from app.agents.models import ResearchBrief
from app.clients.anthropic_client import load_prompt
from app.clients.tavily_client import TavilyBudgetError

VALID_SIGNALS = {
    "funding", "rapid_growth", "tech_fit", "competitor_displacement",
    "exec_hire", "job_posting", "retention_signal", "none",
}


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of an LLM response (tolerates code fences/prose)."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def _build_user(record: dict, searches: list[dict]) -> str:
    parts = ["[ENRICHED RECORD]", json.dumps(record, indent=2, default=str)]
    if searches:
        parts.append("\n[SEARCHES SO FAR]")
        parts.append(json.dumps(searches, default=str))
    parts.append("\nRespond with exactly one JSON object: a search action or the final object.")
    return "\n".join(parts)


def run_research(record: dict, llm, tavily, max_searches: int = 3) -> ResearchBrief:
    """Apollo-first 'why now' research: mine the record, optionally search (capped),
    then return the single strongest signal. The LLM drives the loop; we cap searches."""
    system = load_prompt("research_agent.md")
    searches: list[dict] = []
    for _ in range(max_searches + 1):
        raw = llm.complete(system, _build_user(record, searches), max_tokens=1024)
        action = _extract_json(raw)
        if action.get("action") == "search" and len(searches) < max_searches:
            query = action.get("query", "")
            try:
                results = tavily.search(query)
            except TavilyBudgetError:
                results = {"results": []}
            searches.append({"query": query, "results": results})
            continue
        signal_type = action.get("signal_type", "none")
        if signal_type not in VALID_SIGNALS:
            signal_type = "none"
        return ResearchBrief(
            top_signal=action.get("top_signal"),
            signal_type=signal_type,
            source_url=action.get("source_url"),
        )
    return ResearchBrief(top_signal=None, signal_type="none", source_url=None)
