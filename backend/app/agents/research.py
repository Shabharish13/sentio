from __future__ import annotations

import json

import httpx

from app.agents.models import ResearchBrief
from app.clients.anthropic_client import load_prompt
from app.clients.tavily_client import TavilyBudgetError

VALID_SIGNALS = {
    "funding", "rapid_growth", "tech_fit", "competitor_displacement",
    "exec_hire", "job_posting", "retention_signal", "none",
}


def _extract_json(text: str) -> dict:
    """Return the first valid JSON object found in an LLM response.

    Scans for each '{' and tries to decode a JSON object starting there, so the
    function tolerates code fences, leading prose, and trailing content.
    """
    decoder = json.JSONDecoder()
    text = text.strip()
    for index, char in enumerate(text):
        if char == "{":
            try:
                obj, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                return obj
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
            except (TavilyBudgetError, httpx.HTTPError):
                # Search failure must not abort research — degrade to no results
                # so the agent falls back to enrichment-only signal mining.
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
