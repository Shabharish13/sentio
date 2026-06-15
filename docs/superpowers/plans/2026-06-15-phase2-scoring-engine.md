# Phase 2 — Deterministic Scoring Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A pure-Python, deterministic scoring engine that turns a normalized lead into an ICP fit score + A/B/C grade, a stakeholder classification, an intent score, and a qualified/disqualified routing decision — with all ICP weights read from CSV data files, never hardcoded.

**Architecture:** A new `app/scoring/` package. Weights live in `app/scoring/data/*.csv` (one CSV per dimension) and are loaded by `weights.py`. `fit.py` computes the five ICP dimensions + grade + stakeholder; `intent.py` computes a small form-path intent score; `engine.py` orchestrates fit + intent + routing into a `ScoreResult`. The engine consumes a normalized `Lead` dataclass (decoupled from Apollo's raw shape — a Phase 3/4 adapter will map Apollo → `Lead`). No LLM, no network, fully deterministic.

**Tech Stack:** Python 3 standard library only (`csv`, `dataclasses`, `functools`). pytest. Runs from `backend/` via `.venv/Scripts/python.exe`.

**Design notes / assumptions (carried from `Solution-Design-Document.md` + `sentio-company-profile.md`):**
- Fit weights are exactly the profile tables. Theoretical max sums to **95** (headcount 25 + industry 20 + title 20 + geography 15 + business 15); the profile says "90" — a minor inconsistency in the fictional data. We follow the per-row weights; grade thresholds (A≥60, B 30–59, C<30) are unaffected.
- The profile has **no intent table**. We define a small, honest form-path rubric (max 30, deliberately below fit since form intent is thin) from real demo-form fields only. This is a documented assumption, kept in code (the "weights from CSV" constraint targets ICP fit scoring).
- Stakeholder is classified from the title keyword that matched (champion/economic_buyer/technical/end_user/combined/other).

---

## File Structure

```
backend/app/scoring/
  __init__.py
  models.py          # Lead, FitResult, IntentResult, ScoreResult dataclasses
  weights.py         # CSV loaders (lru_cached)
  fit.py             # dimension scorers + grade_for + score_fit
  intent.py          # score_intent (form-path rubric)
  engine.py          # score_lead -> ScoreResult (fit + intent + routing)
  data/
    headcount.csv
    industry.csv
    title.csv
    geography.csv
    business_model.csv
backend/tests/
  test_scoring_weights.py
  test_scoring_fit.py
  test_scoring_intent.py
  test_scoring_engine.py
```

---

## Task 1: Models + data CSVs + weights loader

**Files:**
- Create: `backend/app/scoring/__init__.py`, `backend/app/scoring/models.py`, `backend/app/scoring/weights.py`, and the five CSVs under `backend/app/scoring/data/`.
- Test: `backend/tests/test_scoring_weights.py`

- [ ] **Step 1: Create `backend/app/scoring/__init__.py`** (single newline).

- [ ] **Step 2: Create the five data CSVs.**

`backend/app/scoring/data/headcount.csv`:
```csv
min,max,points
51,99,10
100,300,25
301,800,20
801,2000,5
```

`backend/app/scoring/data/industry.csv`:
```csv
industry,condition,points
computer software,,20
internet,,18
information technology and services,,15
human resources,,12
marketing and advertising,,12
telecommunications,,5
e-learning,,5
financial services,saas,15
financial services,nonsaas,5
```

`backend/app/scoring/data/title.csv` (keywords are `|`-separated; **no commas inside a field**; rows applied in priority order, first keyword substring match wins):
```csv
priority,keywords,points,stakeholder
1,vp of customer success|vp customer success|head of customer success,20,champion
2,director of customer success|director customer success|director of cs,18,champion
3,cs ops|customer success operations|customer success ops|cs operations,17,champion
4,chief revenue officer|cro,15,economic_buyer
5,chief financial officer|cfo|vp finance|vp of finance|vice president of finance,12,economic_buyer
6,chief technology officer|cto|vp engineering|vp of engineering|head of it,0,technical
7,founder|chief executive officer|ceo,0,combined
8,customer success manager|cs manager|cs lead|customer success lead,8,end_user
9,senior csm|sr csm|senior customer success,3,end_user
10,account executive|sdr|csm|sales development,3,end_user
```

`backend/app/scoring/data/geography.csv`:
```csv
country,points
united states,15
usa,15
united states of america,15
canada,12
united kingdom,12
uk,12
england,12
australia,10
new zealand,10
germany,7
france,7
netherlands,7
ireland,7
spain,7
italy,7
sweden,7
belgium,7
austria,7
switzerland,7
denmark,7
finland,7
norway,7
portugal,7
```

`backend/app/scoring/data/business_model.csv`:
```csv
signal,points
b2b,10
saas,5
```

- [ ] **Step 3: Write the failing test** `backend/tests/test_scoring_weights.py`:

```python
from app.scoring.weights import (
    load_business_model,
    load_geography,
    load_headcount_bands,
    load_industry,
    load_titles,
)


def test_headcount_bands_loaded():
    bands = load_headcount_bands()
    assert (100, 300, 25) in bands
    assert (51, 99, 10) in bands
    assert len(bands) == 4


def test_industry_map_loaded():
    table = load_industry()
    assert table[("computer software", "")] == 20
    assert table[("financial services", "saas")] == 15
    assert table[("financial services", "nonsaas")] == 5


def test_titles_sorted_by_priority_with_stakeholder():
    rows = load_titles()
    assert rows[0][0] == 1  # priority
    assert rows[0][2] == 20  # points
    assert rows[0][3] == "champion"  # stakeholder
    assert "vp of customer success" in rows[0][1]  # keywords list


def test_geography_and_business_model_loaded():
    assert load_geography()["united states"] == 15
    assert load_business_model()["b2b"] == 10
    assert load_business_model()["saas"] == 5
```

- [ ] **Step 4: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.scoring'`).

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest tests/test_scoring_weights.py -v`

- [ ] **Step 5: Write `backend/app/scoring/models.py`:**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lead:
    """Normalized scoring input (decoupled from Apollo's raw response shape)."""

    headcount: int | None = None
    industry: str | None = None
    title: str | None = None
    country: str | None = None
    technologies: list[str] = field(default_factory=list)
    is_b2b: bool = False
    # form-path intent inputs
    problem_stated: str = ""
    how_heard: str | None = None


@dataclass(frozen=True)
class FitResult:
    score: int
    grade: str  # "A" | "B" | "C"
    stakeholder: str  # champion | economic_buyer | technical | end_user | combined | other
    breakdown: dict[str, int]


@dataclass(frozen=True)
class IntentResult:
    score: int
    band: str  # high | medium | low
    known: bool


@dataclass(frozen=True)
class ScoreResult:
    fit: FitResult
    intent: IntentResult
    route: str  # qualified | disqualified
    disqualification_reason: str | None
```

- [ ] **Step 6: Write `backend/app/scoring/weights.py`:**

```python
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"


@lru_cache
def load_headcount_bands() -> list[tuple[int, int, int]]:
    with (DATA_DIR / "headcount.csv").open(encoding="utf-8") as f:
        return [(int(r["min"]), int(r["max"]), int(r["points"])) for r in csv.DictReader(f)]


@lru_cache
def load_industry() -> dict[tuple[str, str], int]:
    """Key: (industry_lower, condition). condition is "" normally, or
    "saas"/"nonsaas" for the Financial Services disambiguation rows."""
    out: dict[tuple[str, str], int] = {}
    with (DATA_DIR / "industry.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[(r["industry"].strip().lower(), r["condition"].strip().lower())] = int(r["points"])
    return out


@lru_cache
def load_titles() -> list[tuple[int, tuple[str, ...], int, str]]:
    rows: list[tuple[int, tuple[str, ...], int, str]] = []
    with (DATA_DIR / "title.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            kws = tuple(k.strip().lower() for k in r["keywords"].split("|") if k.strip())
            rows.append((int(r["priority"]), kws, int(r["points"]), r["stakeholder"].strip()))
    rows.sort(key=lambda x: x[0])
    return rows


@lru_cache
def load_geography() -> dict[str, int]:
    with (DATA_DIR / "geography.csv").open(encoding="utf-8") as f:
        return {r["country"].strip().lower(): int(r["points"]) for r in csv.DictReader(f)}


@lru_cache
def load_business_model() -> dict[str, int]:
    with (DATA_DIR / "business_model.csv").open(encoding="utf-8") as f:
        return {r["signal"].strip().lower(): int(r["points"]) for r in csv.DictReader(f)}
```

- [ ] **Step 7: Run, expect PASS (4 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_weights.py -v`

- [ ] **Step 8: Commit.**

```bash
git add backend/app/scoring/__init__.py backend/app/scoring/models.py backend/app/scoring/weights.py backend/app/scoring/data backend/tests/test_scoring_weights.py
git commit -m "feat(scoring): models + CSV weight data + loaders"
```

---

## Task 2: Fit scoring (`fit.py`)

**Files:**
- Create: `backend/app/scoring/fit.py`
- Test: `backend/tests/test_scoring_fit.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_scoring_fit.py`:

```python
from app.scoring.fit import (
    grade_for,
    score_business_model,
    score_fit,
    score_geography,
    score_headcount,
    score_industry,
    score_title,
)
from app.scoring.models import Lead


def test_headcount_bands():
    assert score_headcount(200) == 25
    assert score_headcount(500) == 20
    assert score_headcount(75) == 10
    assert score_headcount(1500) == 5
    assert score_headcount(30) == 0
    assert score_headcount(5000) == 0
    assert score_headcount(None) == 0


def test_industry_plain_and_financial_disambiguation():
    assert score_industry("Computer Software", []) == 20
    assert score_industry("Internet", []) == 18
    assert score_industry("Construction", []) == 0
    # Financial Services → SaaS keyword present → 15
    assert score_industry("Financial Services", ["API", "Stripe"]) == 15
    # Financial Services → no SaaS keywords → 5
    assert score_industry("Financial Services", ["Oracle", "SAP"]) == 5
    assert score_industry(None, []) == 0


def test_geography():
    assert score_geography("United States") == 15
    assert score_geography("Canada") == 12
    assert score_geography("Australia") == 10
    assert score_geography("Germany") == 7
    assert score_geography("India") == 0
    assert score_geography(None) == 0


def test_business_model():
    assert score_business_model(Lead(is_b2b=True, industry="Computer Software")) == 15
    assert score_business_model(Lead(is_b2b=True, technologies=["API"])) == 15
    assert score_business_model(Lead(is_b2b=True, industry="Telecommunications")) == 10
    assert score_business_model(Lead(is_b2b=False)) == 0


def test_title_points_and_stakeholder():
    assert score_title("VP of Customer Success") == (20, "champion")
    assert score_title("Director of Customer Success") == (18, "champion")
    assert score_title("Chief Revenue Officer") == (15, "economic_buyer")
    assert score_title("CFO") == (12, "economic_buyer")
    assert score_title("CTO") == (0, "technical")
    assert score_title("Founder") == (0, "combined")
    assert score_title("Customer Success Manager") == (8, "end_user")
    assert score_title("Office Manager") == (0, "other")
    assert score_title(None) == (0, "other")


def test_grade_thresholds():
    assert grade_for(60) == "A"
    assert grade_for(85) == "A"
    assert grade_for(59) == "B"
    assert grade_for(30) == "B"
    assert grade_for(29) == "C"
    assert grade_for(0) == "C"


def test_score_fit_grade_a():
    lead = Lead(
        headcount=200,
        industry="Computer Software",
        title="VP of Customer Success",
        country="United States",
        technologies=["HubSpot"],
        is_b2b=True,
    )
    fit = score_fit(lead)
    # 25 + 20 + 20 + 15 + 15 = 95
    assert fit.score == 95
    assert fit.grade == "A"
    assert fit.stakeholder == "champion"
    assert fit.breakdown["industry"] == 20


def test_score_fit_grade_b():
    lead = Lead(
        headcount=1000,
        industry="Telecommunications",
        title="Customer Success Manager",
        country="Canada",
        is_b2b=True,
    )
    fit = score_fit(lead)
    # 5 + 5 + 8 + 12 + 10 = 40
    assert fit.score == 40
    assert fit.grade == "B"
    assert fit.stakeholder == "end_user"


def test_score_fit_grade_c():
    lead = Lead(headcount=20, industry="Construction", title="Office Manager", country="India")
    fit = score_fit(lead)
    assert fit.score == 0
    assert fit.grade == "C"
    assert fit.stakeholder == "other"
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.scoring.fit'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_fit.py -v`

- [ ] **Step 3: Write `backend/app/scoring/fit.py`:**

```python
from __future__ import annotations

from app.scoring.models import FitResult, Lead
from app.scoring.weights import (
    load_business_model,
    load_geography,
    load_headcount_bands,
    load_industry,
    load_titles,
)

# Keywords that confirm a fintech-SaaS reading of an ambiguous "Financial Services" industry.
FINANCIAL_SAAS_KEYWORDS = {"saas", "api", "platform", "fintech", "payments", "subscription"}
# Tech-stack signals or industries that confirm the company is itself a SaaS business.
SAAS_TECH_SIGNALS = {"saas", "api", "platform", "subscription"}
SAAS_CONFIRM_INDUSTRIES = {"computer software", "internet", "information technology and services"}


def score_headcount(headcount: int | None) -> int:
    if headcount is None:
        return 0
    for lo, hi, pts in load_headcount_bands():
        if lo <= headcount <= hi:
            return pts
    return 0


def score_industry(industry: str | None, technologies: list[str]) -> int:
    if not industry:
        return 0
    key = industry.strip().lower()
    table = load_industry()
    if key == "financial services":
        techs = {t.strip().lower() for t in technologies}
        condition = "saas" if techs & FINANCIAL_SAAS_KEYWORDS else "nonsaas"
        return table.get((key, condition), 0)
    return table.get((key, ""), 0)


def score_geography(country: str | None) -> int:
    if not country:
        return 0
    return load_geography().get(country.strip().lower(), 0)


def score_business_model(lead: Lead) -> int:
    weights = load_business_model()
    points = 0
    if lead.is_b2b:
        points += weights.get("b2b", 0)
    techs = {t.strip().lower() for t in lead.technologies}
    industry = (lead.industry or "").strip().lower()
    if techs & SAAS_TECH_SIGNALS or industry in SAAS_CONFIRM_INDUSTRIES:
        points += weights.get("saas", 0)
    return points


def score_title(title: str | None) -> tuple[int, str]:
    if not title:
        return 0, "other"
    text = title.strip().lower()
    for _priority, keywords, points, stakeholder in load_titles():
        if any(kw in text for kw in keywords):
            return points, stakeholder
    return 0, "other"


def grade_for(score: int) -> str:
    if score >= 60:
        return "A"
    if score >= 30:
        return "B"
    return "C"


def score_fit(lead: Lead) -> FitResult:
    title_points, stakeholder = score_title(lead.title)
    breakdown = {
        "headcount": score_headcount(lead.headcount),
        "industry": score_industry(lead.industry, lead.technologies),
        "title": title_points,
        "geography": score_geography(lead.country),
        "business_model": score_business_model(lead),
    }
    score = sum(breakdown.values())
    return FitResult(
        score=score,
        grade=grade_for(score),
        stakeholder=stakeholder,
        breakdown=breakdown,
    )
```

- [ ] **Step 4: Run, expect PASS (9 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_fit.py -v`

- [ ] **Step 5: Commit.**

```bash
git add backend/app/scoring/fit.py backend/tests/test_scoring_fit.py
git commit -m "feat(scoring): deterministic ICP fit scoring + grade + stakeholder"
```

---

## Task 3: Intent scoring (`intent.py`)

**Files:**
- Create: `backend/app/scoring/intent.py`
- Test: `backend/tests/test_scoring_intent.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_scoring_intent.py`:

```python
from app.scoring.intent import score_intent
from app.scoring.models import Lead


def test_high_intent_problem_and_warm_source():
    lead = Lead(
        problem_stated="We keep losing accounts at renewal",
        how_heard="Referral / word of mouth",
    )
    result = score_intent(lead)
    assert result.score == 25  # 15 + 10
    assert result.band == "high"
    assert result.known is True


def test_low_intent_cold_source_no_problem():
    lead = Lead(problem_stated="", how_heard="Google search")
    result = score_intent(lead)
    assert result.score == 5
    assert result.band == "low"
    assert result.known is True


def test_unknown_intent_when_no_signals():
    result = score_intent(Lead())
    assert result.score == 0
    assert result.band == "low"
    assert result.known is False


def test_medium_band_boundary():
    # problem stated only → 15 → medium
    result = score_intent(Lead(problem_stated="surprise churn is hurting us"))
    assert result.score == 15
    assert result.band == "medium"
    assert result.known is True
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.scoring.intent'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_intent.py -v`

- [ ] **Step 3: Write `backend/app/scoring/intent.py`:**

```python
from __future__ import annotations

from app.scoring.models import IntentResult, Lead

# Form-path intent rubric (assumption — the profile has no intent table; kept small
# and honest because demo-form intent data is thin). Max 30.
PROBLEM_STATED_POINTS = 15
HOW_HEARD_POINTS = {
    "referral / word of mouth": 10,
    "referral": 10,
    "word of mouth": 10,
    "industry event": 10,
    "blog / content": 7,
    "blog": 7,
    "content": 7,
    "google search": 5,
    "google": 5,
    "linkedin": 5,
    "other": 0,
}


def _band(score: int) -> str:
    if score >= 20:
        return "high"
    if score >= 10:
        return "medium"
    return "low"


def score_intent(lead: Lead) -> IntentResult:
    score = 0
    known = False
    if lead.problem_stated and lead.problem_stated.strip():
        score += PROBLEM_STATED_POINTS
        known = True
    if lead.how_heard:
        known = True
        score += HOW_HEARD_POINTS.get(lead.how_heard.strip().lower(), 0)
    return IntentResult(score=score, band=_band(score), known=known)
```

- [ ] **Step 4: Run, expect PASS (4 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_intent.py -v`

- [ ] **Step 5: Commit.**

```bash
git add backend/app/scoring/intent.py backend/tests/test_scoring_intent.py
git commit -m "feat(scoring): form-path intent rubric"
```

---

## Task 4: Engine + routing (`engine.py`)

**Files:**
- Create: `backend/app/scoring/engine.py`
- Test: `backend/tests/test_scoring_engine.py`

- [ ] **Step 1: Write the failing test** `backend/tests/test_scoring_engine.py`:

```python
from app.scoring.engine import score_lead
from app.scoring.models import Lead


def test_qualified_a_grade_routes_qualified():
    lead = Lead(
        headcount=200,
        industry="Computer Software",
        title="VP of Customer Success",
        country="United States",
        technologies=["HubSpot"],
        is_b2b=True,
        problem_stated="surprise churn",
        how_heard="Referral",
    )
    result = score_lead(lead)
    assert result.fit.grade == "A"
    assert result.route == "qualified"
    assert result.disqualification_reason is None
    assert result.intent.score == 25


def test_b_grade_routes_qualified():
    lead = Lead(
        headcount=1000,
        industry="Telecommunications",
        title="Customer Success Manager",
        country="Canada",
        is_b2b=True,
    )
    result = score_lead(lead)
    assert result.fit.grade == "B"
    assert result.route == "qualified"
    assert result.disqualification_reason is None


def test_c_grade_routes_disqualified_with_reason():
    lead = Lead(headcount=20, industry="Construction", title="Office Manager", country="India")
    result = score_lead(lead)
    assert result.fit.grade == "C"
    assert result.route == "disqualified"
    assert result.disqualification_reason is not None
    assert "ICP fit C" in result.disqualification_reason
    assert "headcount" in result.disqualification_reason
```

- [ ] **Step 2: Run, expect FAIL** (`ModuleNotFoundError: No module named 'app.scoring.engine'`).

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_engine.py -v`

- [ ] **Step 3: Write `backend/app/scoring/engine.py`:**

```python
from __future__ import annotations

from app.scoring.fit import score_fit
from app.scoring.intent import score_intent
from app.scoring.models import Lead, ScoreResult


def _disqualification_reason(breakdown: dict[str, int], score: int) -> str:
    parts = ", ".join(f"{dim}={pts}" for dim, pts in breakdown.items())
    weak = [dim for dim, pts in breakdown.items() if pts == 0]
    weak_note = f" Weak dimensions: {', '.join(weak)}." if weak else ""
    return f"ICP fit C (score {score}). Breakdown: {parts}.{weak_note}"


def score_lead(lead: Lead) -> ScoreResult:
    """Run the deterministic pipeline: fit + intent + routing/exit gate.

    C-grade leads are routed to the disqualified path (skip Research/Copywriter)
    with a human-readable reason; A/B grades proceed (qualified).
    """
    fit = score_fit(lead)
    intent = score_intent(lead)
    if fit.grade == "C":
        return ScoreResult(
            fit=fit,
            intent=intent,
            route="disqualified",
            disqualification_reason=_disqualification_reason(fit.breakdown, fit.score),
        )
    return ScoreResult(fit=fit, intent=intent, route="qualified", disqualification_reason=None)
```

- [ ] **Step 4: Run, expect PASS (3 passed).**

Run: `.venv/Scripts/python.exe -m pytest tests/test_scoring_engine.py -v`

- [ ] **Step 5: Commit.**

```bash
git add backend/app/scoring/engine.py backend/tests/test_scoring_engine.py
git commit -m "feat(scoring): engine orchestration + routing/exit gate"
```

---

## Task 5: Full-suite verification + task-list update

**Files:** none (verification) + `TASKS.md`

- [ ] **Step 1: Run the whole suite.**

Run: `cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && .venv/Scripts/python.exe -m pytest -q`
Expected: all tests pass (21 from Phase 1 + LLM, plus weights 4, fit 9, intent 4, engine 3 = 41 passed). If anything fails, STOP and report BLOCKED.

- [ ] **Step 2: Mark Phase 2 done in `TASKS.md`.** Read the file, then flip every checkbox in the "Phase 2 — Deterministic scoring engine" section from `[ ]` to `[x]` (the ICP CSV, fit calculator, industry disambiguation, intent score, routing/exit gate, and the tests line). Do not touch other phases. Commit:
```bash
git add TASKS.md && git commit -m "chore: mark Phase 2 tasks complete"
```

---

## Self-Review

- **Spec coverage:** ICP CSV weights (Task 1) ✓; fit calculator across all five dimensions + A/B/C grade (Task 2) ✓; Financial-Services disambiguation via technologies (Task 2, `score_industry`) ✓; intent score from available signal (Task 3) ✓; routing/exit gate C→disqualified, A/B→qualified, with reason (Task 4) ✓; known-input fixtures → expected grade/score (every task, deterministic) ✓.
- **Type/name consistency:** `Lead`, `FitResult`, `IntentResult`, `ScoreResult` defined in Task 1 and used identically in 2–4. Function names (`score_headcount/industry/geography/business_model/title`, `grade_for`, `score_fit`, `score_intent`, `score_lead`) are referenced consistently between tests and impl. CSV loader return shapes match how `fit.py` consumes them (e.g., `load_industry()` keyed by `(industry, condition)`).
- **Placeholders:** none.
- **Deferred (out of scope here):** mapping Apollo's raw enrichment response → `Lead` (Phase 3/4 adapter); chat-path intent from Sage's conversational signals (Phase 3); wiring the engine into the inbound pipeline (Phase 4). This phase delivers the engine as a standalone, fully-tested unit.
- **Known data note:** theoretical fit max is 95, not the profile's stated 90 (business model 10+5); grade thresholds unaffected — documented above.
