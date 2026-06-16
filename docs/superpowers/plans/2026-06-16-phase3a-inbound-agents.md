# Phase 3A — Inbound Agents (Research, Copywriter, CRM) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the three inbound-path agents that the Phase 4 pipeline chains — Research (Apollo-first + Tavily loop → "why now" brief), Copywriter (brief → stakeholder-framed email), CRM (deterministic HubSpot upsert + notes) — each provider-agnostic via `get_llm()` and individually tested with stubs.

**Architecture:** New `app/agents/` package. Agents depend on Phase 1 clients (`get_llm()`, `TavilyClient`, `HubSpotClient`) and Phase 2 results (`FitResult`, `IntentResult`), all injected so tests never hit the network or an LLM. Prompts come from the repo `prompts/*.md` via the existing `load_prompt`.

**Tech Stack:** Python stdlib + existing deps. pytest. Runs from `backend/` via `.venv/Scripts/python.exe`.

**Key facts for the implementer:**
- `from app.clients.anthropic_client import load_prompt` — reads `prompts/<name>.md` (provider-agnostic helper).
- `from app.clients.llm import get_llm` → `get_llm().complete(system, user, max_tokens) -> str`. In tests, inject a stub object exposing `.complete(system, user, max_tokens) -> str`.
- `from app.clients.tavily_client import TavilyClient, TavilyBudgetError`. In tests inject a stub with `.search(query) -> dict`.
- `from app.clients.hubspot_client import HubSpotClient`. In tests inject a stub with `.upsert_contact`, `.upsert_deal`, `.create_note`.
- `from app.scoring.models import FitResult, IntentResult` (Phase 2): `FitResult(score, grade, stakeholder, breakdown)`, `IntentResult(score, band, known)`.
- The agents are pure functions taking injected collaborators — no globals, no network.

---

## File Structure

```
backend/app/agents/
  __init__.py
  models.py          # ResearchBrief, CrmResult dataclasses
  research.py        # run_research(record, llm, tavily) -> ResearchBrief
  copywriter.py      # STAKEHOLDER_FRAMES, build_brief(...), write_email(brief, llm) -> str
  crm.py             # sync_to_crm(...) -> CrmResult
backend/tests/
  test_agent_research.py
  test_agent_copywriter.py
  test_agent_crm.py
```

---

## Task 1: Research Agent

**Files:**
- Create: `backend/app/agents/__init__.py`, `backend/app/agents/models.py`, `backend/app/agents/research.py`
- Test: `backend/tests/test_agent_research.py`

- [ ] **Step 1: Create `backend/app/agents/__init__.py`** (single newline).

- [ ] **Step 2: Write the failing test** `backend/tests/test_agent_research.py`:

```python
import json

from app.agents.research import ResearchBrief, run_research


class StubLLM:
    """Returns canned responses in order; records the prompts it received."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._responses.pop(0)


class StubTavily:
    def __init__(self):
        self.queries = []

    def search(self, query, **kwargs):
        self.queries.append(query)
        return {"results": [{"url": "https://example.com/x", "title": "x"}]}


def test_returns_final_brief_without_search():
    llm = StubLLM([json.dumps({
        "action": "final",
        "top_signal": "Raised a $30M Series B in March 2026",
        "signal_type": "funding",
        "source_url": "https://news.example.com/series-b",
    })])
    tavily = StubTavily()
    brief = run_research({"company": {"name": "Meridian"}}, llm=llm, tavily=tavily)
    assert isinstance(brief, ResearchBrief)
    assert brief.signal_type == "funding"
    assert brief.top_signal.startswith("Raised")
    assert tavily.queries == []  # no search needed


def test_runs_search_then_final():
    llm = StubLLM([
        json.dumps({"action": "search", "query": "Meridian VP customer success hire"}),
        json.dumps({"action": "final", "top_signal": "Hired a VP of CS in May 2026",
                    "signal_type": "exec_hire", "source_url": "https://li.example/x"}),
    ])
    tavily = StubTavily()
    brief = run_research({"company": {"name": "Meridian"}}, llm=llm, tavily=tavily)
    assert tavily.queries == ["Meridian VP customer success hire"]
    assert brief.signal_type == "exec_hire"


def test_invalid_signal_type_coerced_to_none():
    llm = StubLLM([json.dumps({"action": "final", "top_signal": "x", "signal_type": "bogus"})])
    brief = run_research({}, llm=llm, tavily=StubTavily())
    assert brief.signal_type == "none"


def test_unparseable_response_returns_none_brief():
    llm = StubLLM(["this is not json at all"])
    brief = run_research({}, llm=llm, tavily=StubTavily())
    assert brief.signal_type == "none"
    assert brief.top_signal is None


def test_search_cap_forces_final():
    # All responses say "search"; after max_searches the loop must stop and return none.
    llm = StubLLM([json.dumps({"action": "search", "query": "q"})] * 5)
    tavily = StubTavily()
    brief = run_research({}, llm=llm, tavily=tavily, max_searches=3)
    assert len(tavily.queries) == 3  # capped
    assert brief.signal_type == "none"
```

- [ ] **Step 3: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.agents.research'`).

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest tests/test_agent_research.py -v`

- [ ] **Step 4: Write `backend/app/agents/models.py`:**

```python
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
```

- [ ] **Step 5: Write `backend/app/agents/research.py`:**

```python
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
```

- [ ] **Step 6: Run, expect PASS (5 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_research.py -v`

- [ ] **Step 7: Commit.**

```bash
git add backend/app/agents/__init__.py backend/app/agents/models.py backend/app/agents/research.py backend/tests/test_agent_research.py
git commit -m "feat(agents): Research agent — Apollo-first why-now signal with capped Tavily loop"
```

---

## Task 2: Copywriter Agent

**Files:**
- Create: `backend/app/agents/copywriter.py`
- Test: `backend/tests/test_agent_copywriter.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_agent_copywriter.py`:

```python
import json

from app.agents.copywriter import STAKEHOLDER_FRAMES, build_brief, write_email
from app.agents.models import ResearchBrief
from app.scoring.models import FitResult, IntentResult


class StubLLM:
    def __init__(self, reply):
        self._reply = reply
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._reply


def _fit(stakeholder="champion", grade="A"):
    return FitResult(score=95, grade=grade, stakeholder=stakeholder,
                     breakdown={"headcount": 25})


def test_build_brief_selects_frame_and_maps_research():
    brief = build_brief(
        contact={"first_name": "Jane", "name": "Jane Doe", "title": "VP CS"},
        company={"name": "Meridian", "headcount": 200, "industry": "Computer Software"},
        fit=_fit("economic_buyer"),
        intent=IntentResult(score=25, band="high", known=True),
        research=ResearchBrief("Raised Series B", "funding", "https://x"),
        problem_stated="surprise churn",
    )
    assert brief["stakeholder_type"] == "economic_buyer"
    assert brief["email_frame"] == STAKEHOLDER_FRAMES["economic_buyer"]
    assert brief["fit_grade"] == "A"
    assert brief["intent_score"] == 25
    assert brief["research"]["signal_type"] == "funding"
    assert brief["problem_stated"] == "surprise churn"


def test_unknown_stakeholder_uses_other_frame():
    brief = build_brief(contact={}, company={}, fit=_fit("mystery"),
                        intent=IntentResult(0, "low", False),
                        research=ResearchBrief(None, "none", None))
    assert brief["email_frame"] == STAKEHOLDER_FRAMES["other"]


def test_write_email_calls_llm_with_copywriter_prompt_and_returns_body():
    llm = StubLLM("Hi Jane,\n\nNoticed your Series B...\n\nBest,\nAlex")
    brief = {"contact": {"first_name": "Jane"}, "fit_grade": "A"}
    out = write_email(brief, llm=llm)
    assert out.startswith("Hi Jane")
    system, user = llm.calls[0]
    assert "outreach" in system.lower() or "copywriter" in system.lower()
    assert json.loads(user)["fit_grade"] == "A"  # brief passed as JSON
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.agents.copywriter'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_copywriter.py -v`

- [ ] **Step 3: Write `backend/app/agents/copywriter.py`:**

```python
from __future__ import annotations

import json

from app.clients.anthropic_client import load_prompt

# Persona email frames (from sentio-company-profile.md). The Copywriter prompt
# expects a pre-selected `email_frame` sentence keyed off the stakeholder type.
STAKEHOLDER_FRAMES = {
    "champion": "Efficiency, playbook consistency, CSM capacity — your CSMs shouldn't learn about churn risk from the customer.",
    "economic_buyer": "ROI and NRR in dollar terms — every point of NRR at $10M ARR is six figures in retained revenue.",
    "technical": "Integrations, SOC 2, no-code setup — connects to your existing stack in under a day, no custom ETL.",
    "end_user": "Day-to-day workflow and time saved — know which accounts to call today without an hour of digging.",
    "combined": "Business outcome plus simplicity — a CS intelligence layer you can stand up before your second CSM.",
    "other": "Company stage and vertical — why churn risk is acute at this stage.",
}


def build_brief(contact, company, fit, intent, research, problem_stated: str = "") -> dict:
    """Assemble the structured brief the Copywriter prompt consumes."""
    return {
        "contact": contact,
        "company": company,
        "fit_grade": fit.grade,
        "intent_score": intent.score,
        "stakeholder_type": fit.stakeholder,
        "email_frame": STAKEHOLDER_FRAMES.get(fit.stakeholder, STAKEHOLDER_FRAMES["other"]),
        "research": {
            "top_signal": research.top_signal,
            "signal_type": research.signal_type,
            "source_url": research.source_url,
        },
        "problem_stated": problem_stated,
    }


def write_email(brief: dict, llm) -> str:
    """Generate the SDR-review email body from the brief (sourced facts only)."""
    system = load_prompt("copywriter_agent.md")
    user = json.dumps(brief, indent=2, default=str)
    return llm.complete(system, user, max_tokens=600).strip()
```

- [ ] **Step 4: Run, expect PASS (3 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_copywriter.py -v`

- [ ] **Step 5: Commit.**

```bash
git add backend/app/agents/copywriter.py backend/tests/test_agent_copywriter.py
git commit -m "feat(agents): Copywriter agent — stakeholder-framed email from research brief"
```

---

## Task 3: CRM Agent

**Files:**
- Create: `backend/app/agents/crm.py`
- Test: `backend/tests/test_agent_crm.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_agent_crm.py`:

```python
import pytest

from app.agents.crm import sync_to_crm
from app.agents.models import CrmResult


class StubHubSpot:
    def __init__(self):
        self.calls = []

    def upsert_contact(self, email, properties):
        self.calls.append(("contact", email, properties))
        return "c1"

    def upsert_deal(self, name, stage, contact_id):
        self.calls.append(("deal", name, stage, contact_id))
        return "d1"

    def create_note(self, body, deal_id):
        self.calls.append(("note", body, deal_id))
        return "n1"


def test_qualified_routes_to_demo_requested_stage(monkeypatch):
    monkeypatch.setenv("HUBSPOT_STAGE_DEMO_REQUESTED", "3832955632")
    monkeypatch.setenv("HUBSPOT_STAGE_DISQUALIFIED", "3840698071")
    from app.config import get_settings
    get_settings.cache_clear()
    hs = StubHubSpot()
    result = sync_to_crm(
        email="jane@meridian.io", contact_props={"firstname": "Jane"},
        deal_name="Meridian — inbound", route="qualified",
        note_body="SDR hand-off: persona=champion; why-now=Series B.", hubspot=hs,
    )
    assert isinstance(result, CrmResult)
    assert result.stage == "3832955632"
    assert result.contact_id == "c1" and result.deal_id == "d1" and result.note_id == "n1"
    # deal created with the demo-requested stage
    assert ("deal", "Meridian — inbound", "3832955632", "c1") in hs.calls


def test_disqualified_routes_to_disqualified_stage(monkeypatch):
    monkeypatch.setenv("HUBSPOT_STAGE_DEMO_REQUESTED", "3832955632")
    monkeypatch.setenv("HUBSPOT_STAGE_DISQUALIFIED", "3840698071")
    from app.config import get_settings
    get_settings.cache_clear()
    hs = StubHubSpot()
    result = sync_to_crm(
        email="bob@tinyco.io", contact_props={}, deal_name="TinyCo — inbound",
        route="disqualified", note_body="Disqualified: headcount out of ICP range.", hubspot=hs,
    )
    assert result.stage == "3840698071"


def test_empty_note_body_rejected():
    with pytest.raises(ValueError):
        sync_to_crm(email="x@y.io", contact_props={}, deal_name="X", route="qualified",
                    note_body="   ", hubspot=StubHubSpot())
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.agents.crm'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_crm.py -v`

- [ ] **Step 3: Write `backend/app/agents/crm.py`:**

```python
from __future__ import annotations

from app.agents.models import CrmResult
from app.config import get_settings


def sync_to_crm(*, email: str, contact_props: dict, deal_name: str, route: str,
                note_body: str, hubspot) -> CrmResult:
    """Upsert the contact + deal and attach a (mandatory) note.

    Stage is set by the routing outcome: qualified -> demo-requested, otherwise
    -> disqualified. A deal is never written without a note (design constraint).
    """
    if not note_body or not note_body.strip():
        raise ValueError("note_body is mandatory — a deal must never be written without a note")
    settings = get_settings()
    stage = (
        settings.hubspot_stage_demo_requested
        if route == "qualified"
        else settings.hubspot_stage_disqualified
    )
    contact_id = hubspot.upsert_contact(email, contact_props)
    deal_id = hubspot.upsert_deal(name=deal_name, stage=stage, contact_id=contact_id)
    note_id = hubspot.create_note(note_body, deal_id=deal_id)
    return CrmResult(contact_id=contact_id, deal_id=deal_id, stage=stage, note_id=note_id)
```

- [ ] **Step 4: Run, expect PASS (3 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_agent_crm.py -v`

- [ ] **Step 5: Commit.**

```bash
git add backend/app/agents/crm.py backend/tests/test_agent_crm.py
git commit -m "feat(agents): CRM agent — stage-by-outcome upsert with mandatory notes"
```

---

## Task 4: Full-suite verification

**Files:** none (verification)

- [ ] **Step 1: Run the whole suite.**

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all prior tests (49) plus research 5 + copywriter 3 + crm 3 = **60 passed**. If anything fails, STOP and report BLOCKED.

- [ ] **Step 2: Commit a note** (no TASKS.md flip yet — Phase 3 also needs 3B Sage/RAG). Nothing to commit if suite is green; proceed.

---

## Self-Review

- **Spec coverage:** Research Agent (Apollo-first + capped Tavily loop → brief) Task 1 ✓; Copywriter Agent (stakeholder-framed email, sourced-facts-only via prompt) Task 2 ✓; CRM Agent (stage-by-outcome upsert + mandatory notes) Task 3 ✓.
- **Type/name consistency:** `ResearchBrief(top_signal, signal_type, source_url)` and `CrmResult(contact_id, deal_id, stage, note_id)` defined in `models.py` (Task 1) and used in Tasks 2–3. `FitResult.stakeholder`/`.grade`, `IntentResult.score` match Phase 2. Stub collaborators match the real client method signatures (`complete`, `search`, `upsert_contact/upsert_deal/create_note`).
- **Placeholders:** none.
- **Deferred (later plans):** Sage + RAG (Phase 3B); the Apollo→record/Lead adapter and the orchestration that chains these three agents (Phase 4). This plan delivers the three inbound agents as independently-tested units.
- **Note on Sage (the fourth agent):** intentionally out of scope here — it's the chat path and is built in Phase 3B with the RAG stack.
