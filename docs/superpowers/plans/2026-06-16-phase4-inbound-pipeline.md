# Phase 4 — Inbound Pipeline Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chain the deterministic steps (exit check → Apollo cache/enrich → score → route) and the agents (Research → Copywriter → CRM) into one inbound pipeline: A/B leads get researched, an email drafted, and a demo-requested deal; C leads short-circuit straight to a disqualified deal with a reason — proven end-to-end with A/B/C fixtures.

**Architecture:** New `app/pipeline/` package. An adapter maps the demo-form submission + Apollo enrichment into the Phase 2 `Lead` and the agents' input shapes; `run_inbound_pipeline(...)` orchestrates the chain with all collaborators (apollo, llm, tavily, hubspot) injected, so the end-to-end test runs on stubs (no network/LLM). Reuses Phase 2 scoring (`score_lead`) and Phase 3 agents (`run_research`, `build_brief`/`write_email`, `sync_to_crm`).

**Tech Stack:** Python stdlib + existing modules. pytest. Runs from `backend/` via `.venv/Scripts/python.exe`.

**Key facts for the implementer:**
- `from app.scoring.engine import score_lead` → `ScoreResult(fit, intent, route, disqualification_reason)`; `from app.scoring.models import Lead`.
- `from app.agents.research import run_research` → `ResearchBrief(top_signal, signal_type, source_url)`.
- `from app.agents.copywriter import build_brief, write_email`.
- `from app.agents.crm import sync_to_crm` → `CrmResult`; signature `sync_to_crm(*, email, contact_props, deal_name, route, note_body, hubspot)`.
- `from app.clients.apollo_client import ApolloClient` — `enrich_organization(domain) -> dict` (Apollo returns `{"organization": {...}}`), `enrich_person(email, **fields) -> dict` (`{"person": {...}}`). Cache-first.
- Demo-form fields (from `website-copy.md`): `first_name, last_name, work_email, company_name, job_title, company_size, problem_stated, how_heard`.

---

## File Structure

```
backend/app/pipeline/
  __init__.py
  models.py          # PipelineResult
  adapter.py         # email_domain, build_lead, build_record, contact_props, deal_name
  inbound.py         # run_inbound_pipeline(form, *, apollo, llm, tavily, hubspot) -> PipelineResult
backend/tests/
  test_pipeline_adapter.py
  test_pipeline_inbound.py
```

---

## Task 1: Adapter (form + Apollo → normalized shapes)

**Files:**
- Create: `backend/app/pipeline/__init__.py`, `backend/app/pipeline/adapter.py`
- Test: `backend/tests/test_pipeline_adapter.py`

- [ ] **Step 1: Create `backend/app/pipeline/__init__.py`** (single newline).

- [ ] **Step 2: Write the failing test** `backend/tests/test_pipeline_adapter.py`:

```python
from app.pipeline.adapter import (
    build_lead,
    build_record,
    contact_props,
    deal_name,
    email_domain,
)
from app.scoring.models import Lead

FORM = {
    "first_name": "Jane", "last_name": "Doe", "work_email": "jane@meridian.io",
    "company_name": "Meridian Analytics", "job_title": "VP of Customer Success",
    "company_size": "201-500", "problem_stated": "surprise churn at renewal",
    "how_heard": "Referral / word of mouth",
}
ORG = {"organization": {"estimated_num_employees": 210, "industry": "Computer Software",
                        "country": "United States",
                        "technology_names": ["HubSpot", "Segment"]}}
PERSON = {"person": {"title": "VP of Customer Success", "country": "United States"}}


def test_email_domain():
    assert email_domain("jane@meridian.io") == "meridian.io"
    assert email_domain("bad-email") == ""


def test_build_lead_from_apollo_and_form():
    lead = build_lead(FORM, ORG, PERSON)
    assert isinstance(lead, Lead)
    assert lead.headcount == 210
    assert lead.industry == "Computer Software"
    assert lead.title == "VP of Customer Success"
    assert lead.country == "United States"
    assert "HubSpot" in lead.technologies
    assert lead.is_b2b is True
    assert lead.problem_stated == "surprise churn at renewal"
    assert lead.how_heard == "Referral / word of mouth"


def test_build_lead_falls_back_to_form_company_size_when_no_apollo():
    lead = build_lead(FORM, {"organization": {}}, {"person": {}})
    # "201-500" band -> midpoint 350; title still from the form
    assert lead.headcount == 350
    assert lead.title == "VP of Customer Success"
    assert lead.is_b2b is False  # no org enrichment


def test_build_record_has_contact_and_company():
    rec = build_record(FORM, ORG, PERSON)
    assert rec["contact"]["name"] == "Jane Doe"
    assert rec["contact"]["title"] == "VP of Customer Success"
    assert rec["company"]["name"] == "Meridian Analytics"
    assert rec["company"]["headcount"] == 210
    assert rec["company"]["technologies"] == ["HubSpot", "Segment"]


def test_contact_props_and_deal_name():
    assert contact_props(FORM) == {"firstname": "Jane", "lastname": "Doe",
                                   "jobtitle": "VP of Customer Success"}
    assert deal_name(FORM) == "Meridian Analytics — inbound"
```

- [ ] **Step 3: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.pipeline.adapter'`).

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest tests/test_pipeline_adapter.py -v`

- [ ] **Step 4: Write `backend/app/pipeline/adapter.py`:**

```python
from __future__ import annotations

from app.scoring.models import Lead

# Demo-form company-size bands -> a representative headcount (midpoint-ish).
_SIZE_BAND_HEADCOUNT = {
    "1-10": 5, "11-50": 30, "51-200": 125, "201-500": 350, "500+": 800,
}


def email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].strip().lower()


def _org(org: dict) -> dict:
    return org.get("organization") or {}


def _person(person: dict) -> dict:
    return person.get("person") or {}


def build_lead(form: dict, org: dict, person: dict) -> Lead:
    o, p = _org(org), _person(person)
    headcount = o.get("estimated_num_employees")
    if not headcount:
        headcount = _SIZE_BAND_HEADCOUNT.get((form.get("company_size") or "").strip())
    technologies = list(o.get("technology_names") or o.get("current_technologies") or [])
    return Lead(
        headcount=headcount,
        industry=o.get("industry"),
        title=form.get("job_title") or p.get("title"),
        country=o.get("country") or p.get("country"),
        technologies=technologies,
        is_b2b=bool(o),  # an enriched org is treated as a B2B company
        problem_stated=form.get("problem_stated") or "",
        how_heard=form.get("how_heard"),
    )


def build_record(form: dict, org: dict, person: dict) -> dict:
    o, p = _org(org), _person(person)
    full_name = f"{form.get('first_name', '')} {form.get('last_name', '')}".strip()
    return {
        "contact": {
            "name": full_name,
            "title": form.get("job_title") or p.get("title"),
            "seniority": p.get("seniority"),
        },
        "company": {
            "name": form.get("company_name"),
            "domain": email_domain(form.get("work_email", "")),
            "industry": o.get("industry"),
            "headcount": o.get("estimated_num_employees"),
            "technologies": list(o.get("technology_names") or o.get("current_technologies") or []),
            "funding": o.get("funding") or o.get("latest_funding_stage"),
            "keywords": o.get("keywords") or [],
        },
    }


def contact_props(form: dict) -> dict:
    return {
        "firstname": form.get("first_name", ""),
        "lastname": form.get("last_name", ""),
        "jobtitle": form.get("job_title", ""),
    }


def deal_name(form: dict) -> str:
    return f"{form.get('company_name', 'Unknown')} — inbound"
```

- [ ] **Step 5: Run, expect PASS (5 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_adapter.py -v`

- [ ] **Step 6: Commit.**

```bash
git add backend/app/pipeline/__init__.py backend/app/pipeline/adapter.py backend/tests/test_pipeline_adapter.py
git commit -m "feat(pipeline): adapter mapping demo form + Apollo enrichment to Lead/record"
```

---

## Task 2: Inbound pipeline orchestration

**Files:**
- Create: `backend/app/pipeline/models.py`, `backend/app/pipeline/inbound.py`
- Test: `backend/tests/test_pipeline_inbound.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_pipeline_inbound.py`:

```python
import json

import pytest

from app.pipeline.inbound import run_inbound_pipeline
from app.pipeline.models import PipelineResult


class StubApollo:
    def __init__(self, org, person):
        self._org, self._person = org, person
        self.org_calls, self.person_calls = [], []

    def enrich_organization(self, domain):
        self.org_calls.append(domain)
        return self._org

    def enrich_person(self, email, **fields):
        self.person_calls.append(email)
        return self._person


class StubLLM:
    """First call -> research final JSON; second call -> email body."""

    def __init__(self):
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        if "Research" in system or "why now" in system.lower():
            return json.dumps({"action": "final", "top_signal": "Raised a Series B",
                               "signal_type": "funding", "source_url": "https://x"})
        return "Hi Jane,\n\nNoticed your Series B...\n\nBest,\nAlex"


class StubTavily:
    def search(self, query, **kwargs):
        return {"results": []}


class StubHubSpot:
    def __init__(self):
        self.calls = []

    def upsert_contact(self, email, properties):
        self.calls.append(("contact", email)); return "c1"

    def upsert_deal(self, name, stage, contact_id):
        self.calls.append(("deal", name, stage)); return "d1"

    def create_note(self, body, deal_id):
        self.calls.append(("note", body)); return "n1"


A_FORM = {
    "first_name": "Jane", "last_name": "Doe", "work_email": "jane@meridian.io",
    "company_name": "Meridian Analytics", "job_title": "VP of Customer Success",
    "company_size": "201-500", "problem_stated": "surprise churn", "how_heard": "Referral",
}
A_ORG = {"organization": {"estimated_num_employees": 210, "industry": "Computer Software",
                          "country": "United States", "technology_names": ["HubSpot"]}}
A_PERSON = {"person": {"title": "VP of Customer Success", "country": "United States"}}


def test_qualified_lead_runs_research_email_and_demo_requested_deal():
    apollo = StubApollo(A_ORG, A_PERSON)
    llm = StubLLM()
    hubspot = StubHubSpot()
    result = run_inbound_pipeline(A_FORM, apollo=apollo, llm=llm, tavily=StubTavily(), hubspot=hubspot)

    assert isinstance(result, PipelineResult)
    assert result.fit_grade == "A"
    assert result.route == "qualified"
    assert result.signal_type == "funding"
    assert result.email_draft.startswith("Hi Jane")
    assert result.crm.stage == "3832955632"  # demo-requested
    # research + copywriter both used the LLM (2 calls)
    assert len(llm.calls) == 2
    # the note carries the hand-off (persona + why-now + the draft email)
    note_call = [c for c in hubspot.calls if c[0] == "note"][0]
    assert "Series B" in note_call[1] and "Hi Jane" in note_call[1]
    assert apollo.org_calls == ["meridian.io"]


def test_disqualified_lead_skips_research_and_writes_disqualified_deal():
    c_form = {
        "first_name": "Bob", "last_name": "Lee", "work_email": "bob@tinyco.io",
        "company_name": "TinyCo", "job_title": "Office Manager",
        "company_size": "1-10", "problem_stated": "", "how_heard": "Other",
    }
    c_org = {"organization": {"estimated_num_employees": 6, "industry": "Construction",
                              "country": "India", "technology_names": []}}
    apollo = StubApollo(c_org, {"person": {}})
    llm = StubLLM()
    hubspot = StubHubSpot()
    result = run_inbound_pipeline(c_form, apollo=apollo, llm=llm, tavily=StubTavily(), hubspot=hubspot)

    assert result.fit_grade == "C"
    assert result.route == "disqualified"
    assert result.email_draft is None          # no email for disqualified
    assert llm.calls == []                       # research/copywriter skipped
    assert result.crm.stage == "3840698071"      # disqualified
    note_call = [c for c in hubspot.calls if c[0] == "note"][0]
    assert "ICP fit C" in note_call[1]           # disqualification reason note


def test_exit_check_rejects_missing_email():
    with pytest.raises(ValueError):
        run_inbound_pipeline({"company_name": "X"}, apollo=StubApollo({}, {}),
                             llm=StubLLM(), tavily=StubTavily(), hubspot=StubHubSpot())
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.pipeline.inbound'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_inbound.py -v`

- [ ] **Step 3: Write `backend/app/pipeline/models.py`:**

```python
from __future__ import annotations

from dataclasses import dataclass

from app.agents.models import CrmResult


@dataclass(frozen=True)
class PipelineResult:
    route: str  # qualified | disqualified
    fit_grade: str
    fit_score: int
    stakeholder: str
    intent_score: int
    signal_type: str
    top_signal: str | None
    email_draft: str | None
    disqualification_reason: str | None
    crm: CrmResult
```

- [ ] **Step 4: Write `backend/app/pipeline/inbound.py`:**

```python
from __future__ import annotations

from app.agents.copywriter import build_brief, write_email
from app.agents.crm import sync_to_crm
from app.agents.research import run_research
from app.pipeline.adapter import (
    build_lead,
    build_record,
    contact_props,
    deal_name,
    email_domain,
)
from app.pipeline.models import PipelineResult
from app.scoring.engine import score_lead


def _handoff_note(lead, score, research, email_body: str) -> str:
    return (
        f"SDR hand-off — persona: {score.fit.stakeholder}; "
        f"ICP: {score.fit.grade}/{score.fit.score}; "
        f"intent: {score.intent.score} ({score.intent.band}); "
        f"why-now: {research.top_signal or 'none'} ({research.signal_type}); "
        f"source: {research.source_url or 'n/a'}.\n\nDraft email (for SDR review):\n{email_body}"
    )


def run_inbound_pipeline(form: dict, *, apollo, llm, tavily, hubspot) -> PipelineResult:
    """Inbound pipeline: exit check -> enrich -> score -> route -> (research ->
    copywriter -> CRM) for A/B, or straight to a disqualified deal for C."""
    email = (form.get("work_email") or "").strip()
    if not email or "@" not in email:
        raise ValueError("exit check: a valid work_email is required")

    domain = email_domain(email)
    org = apollo.enrich_organization(domain) if domain else {"organization": {}}
    person = apollo.enrich_person(email, first_name=form.get("first_name"),
                                  last_name=form.get("last_name"), domain=domain)

    lead = build_lead(form, org, person)
    score = score_lead(lead)

    name = deal_name(form)
    props = contact_props(form)

    if score.route == "disqualified":
        crm = sync_to_crm(email=email, contact_props=props, deal_name=name,
                          route="disqualified", note_body=score.disqualification_reason, hubspot=hubspot)
        return PipelineResult(
            route="disqualified", fit_grade=score.fit.grade, fit_score=score.fit.score,
            stakeholder=score.fit.stakeholder, intent_score=score.intent.score,
            signal_type="none", top_signal=None, email_draft=None,
            disqualification_reason=score.disqualification_reason, crm=crm,
        )

    record = build_record(form, org, person)
    research = run_research(record, llm=llm, tavily=tavily)
    brief = build_brief(
        contact=record["contact"], company=record["company"],
        fit=score.fit, intent=score.intent, research=research,
        problem_stated=form.get("problem_stated") or "",
    )
    email_body = write_email(brief, llm=llm)
    note = _handoff_note(lead, score, research, email_body)
    crm = sync_to_crm(email=email, contact_props=props, deal_name=name,
                      route="qualified", note_body=note, hubspot=hubspot)
    return PipelineResult(
        route="qualified", fit_grade=score.fit.grade, fit_score=score.fit.score,
        stakeholder=score.fit.stakeholder, intent_score=score.intent.score,
        signal_type=research.signal_type, top_signal=research.top_signal,
        email_draft=email_body, disqualification_reason=None, crm=crm,
    )
```

- [ ] **Step 5: Run, expect PASS (3 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_pipeline_inbound.py -v`

- [ ] **Step 6: Commit.**

```bash
git add backend/app/pipeline/models.py backend/app/pipeline/inbound.py backend/tests/test_pipeline_inbound.py
git commit -m "feat(pipeline): inbound orchestration — enrich -> score -> route -> research/copywriter/CRM"
```

---

## Task 3: Full-suite verification + iteration log + task-list

**Files:**
- Create: `ITERATION-LOG.md` (repo root)
- Modify: `TASKS.md`

- [ ] **Step 1: Run the whole suite.**

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all prior tests (68) + adapter 5 + inbound 3 = **76 passed**. If anything fails, STOP and report BLOCKED.

- [ ] **Step 2: Write `ITERATION-LOG.md`** at the repo root documenting the real fixes found by testing (the brief scores iteration discipline):

```markdown
# Iteration Log — what broke and how it was fixed

Evidence of testing → finding real issues → fixing them, across the build.

- **HubSpot pipeline ID was the portal ID.** Docs recorded pipeline `246500414`; the
  live `GET /crm/v3/pipelines/deals` showed that is the *portal* id — the real pipeline
  is `default`, with the disqualified stage `3840698071`. Corrected everywhere.
- **Research agent dropped prose-wrapped JSON.** First-brace/last-brace extraction failed
  when the LLM added preamble containing a `{`. Switched to a `raw_decode` scan for the
  first valid JSON object; added a regression test.
- **Sage escalated everything.** The prompt's 0.75 cosine threshold assumed a different
  embedder; all-MiniLM-L6-v2 scores relevant KB matches ~0.52 and off-topic ~0.2.
  Recalibrated the runtime threshold to 0.35 (validated live: on-topic answers, off-topic
  escalates) and updated the prompt.
- **OpenAI key had no quota.** The provided key authenticates but 429s on completions, so
  the LLM facade was made an ordered fallback chain (OpenAI → Anthropic → claude CLI) that
  catches provider errors and falls through — proven live (OpenAI 429 → CLI answered).
- **Apollo cache-first.** Verified the second enrichment of the same email serves from the
  local JSON cache with no API call, protecting the 50-credit free tier.
```

- [ ] **Step 3: Mark Phase 4 done in `TASKS.md`.** Read the file, flip every checkbox in the "Phase 4 — Inbound pipeline orchestration" section from `[ ]` to `[x]` (the chain, the C-grade short-circuit, the end-to-end A/B/C test, and the iteration log). Do not touch other phases.

- [ ] **Step 4: Commit.**

```bash
git add ITERATION-LOG.md TASKS.md
git commit -m "docs: iteration log + mark Phase 4 (inbound pipeline) complete"
```

---

## Self-Review

- **Spec coverage:** chain exit→enrich→score→route→research→copywriter→CRM (Task 2 `run_inbound_pipeline`) ✓; C-grade short-circuit to disqualified, skipping research/copywriter (Task 2, disqualified branch + test) ✓; end-to-end A/B/C fixtures (Task 2 tests: A qualified, C disqualified, exit) ✓; iteration log (Task 3) ✓. (A "B" grade also routes qualified through the same A/B branch; the A fixture exercises that path.)
- **Type/name consistency:** `build_lead/build_record/contact_props/deal_name/email_domain` defined in Task 1 and called in Task 2. `PipelineResult` fields used consistently. `sync_to_crm(*, email, contact_props, deal_name, route, note_body, hubspot)`, `score_lead`, `run_research`, `build_brief`/`write_email` match Phases 2–3 signatures. Stub collaborators mirror the real client methods.
- **Placeholders:** none.
- **Deferred:** the chat-path orchestration (Sage outcomes → CRM) and the FastAPI `/demo` + `/chat` endpoints (Phase 5) — this plan delivers the inbound pipeline as a tested, callable unit the endpoint will wrap.
