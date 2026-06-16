# Phase 1 — Backend Foundation & API Integrations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the FastAPI backend skeleton and four typed, tested API-client wrappers (Anthropic, Apollo with JSON caching, Tavily with a call budget, HubSpot CRM) that the agents in later phases call.

**Architecture:** A `backend/` Python package. `app/config.py` loads secrets from the existing `api-tests/.env` via pydantic-settings and exposes path constants. `app/clients/` holds one wrapper per provider, each with an injectable HTTP/SDK client so tests never hit the network. `app/main.py` is a minimal FastAPI app with a `/health` route to prove the app boots. Tests use `respx` to mock httpx (the Anthropic SDK is httpx-based, so the same mock layer covers all four).

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, httpx (sync), the official `anthropic` SDK, pydantic-settings, pytest, respx. **LLM model is `claude-sonnet-4-6`** — the project explicitly pins this in CLAUDE.md and `.env`; do NOT substitute a different model.

---

## File Structure

```
backend/
  requirements.txt          # runtime + dev deps
  pytest.ini                # pytest config (pythonpath=., markers)
  app/
    __init__.py
    config.py               # Settings + REPO_ROOT/ENV_FILE/PROMPTS_DIR constants
    main.py                 # FastAPI app + /health
    clients/
      __init__.py
      anthropic_client.py   # Claude wrapper + prompt loader
      apollo_client.py      # people/org enrich + JSON cache (cache-first)
      tavily_client.py      # search + 3-call budget
      hubspot_client.py     # contact upsert, deal upsert, note attach
  tests/
    __init__.py
    conftest.py             # shared fixtures (dummy settings env)
    test_config.py
    test_health.py
    test_anthropic_client.py
    test_apollo_client.py
    test_tavily_client.py
    test_hubspot_client.py
cache/apollo/               # created at runtime, gitignored
```

`config.py` owns all path math (`REPO_ROOT = parents[2]`); clients import the constants so no client does its own path walking.

---

## Task 0: Project scaffold + git

**Files:**
- Create: `backend/requirements.txt`, `backend/pytest.ini`, `backend/app/__init__.py`, `backend/app/clients/__init__.py`, `backend/tests/__init__.py`, `backend/tests/conftest.py`

- [ ] **Step 1: Initialize git (repo is not yet under version control)**

Run:
```bash
cd /c/Users/Arunkumar/Documents/Docket-assignment && git init && git add .gitignore && git commit -m "chore: init repo"
```
Expected: a repo with one commit. `.gitignore` already exists and ignores `.env`, `__pycache__/`, `.venv/`, `cache/`.

- [ ] **Step 2: Add `cache/` and venv ignores are present; append `.cache/` guard**

Edit `/.gitignore` — confirm it contains `cache/`. If `backend/.cache` is ever used it's covered; no change needed if `cache/` is present. (No-op if already there.)

- [ ] **Step 3: Write `backend/requirements.txt`**

```
fastapi==0.115.6
uvicorn==0.34.0
httpx==0.28.1
anthropic==0.69.0
pydantic-settings==2.7.1
pytest==8.3.4
respx==0.22.0
```

- [ ] **Step 4: Write `backend/pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
markers =
    live: hits real provider APIs; skipped unless keys are present
```

- [ ] **Step 5: Create empty package markers**

Create `backend/app/__init__.py`, `backend/app/clients/__init__.py`, `backend/tests/__init__.py` each containing a single newline.

- [ ] **Step 6: Write `backend/tests/conftest.py`** (forces clients to never read real keys in unit tests)

```python
import pytest


@pytest.fixture(autouse=True)
def _dummy_env(monkeypatch):
    """Unit tests must never read real keys or hit the network."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setenv("APOLLO_API_KEY", "test-apollo")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily")
    monkeypatch.setenv("HUBSPOT_TOKEN", "test-hubspot")
    # get_settings() is lru_cached — clear it so each test sees fresh env
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
```

- [ ] **Step 7: Create and activate a venv, install deps**

Run:
```bash
cd /c/Users/Arunkumar/Documents/Docket-assignment/backend && python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt
```
Expected: all packages install. (On Git Bash for Windows the interpreter is `.venv/Scripts/python.exe`.)

- [ ] **Step 8: Commit**

```bash
git add backend/ && git commit -m "chore: scaffold backend package, deps, pytest config"
```

---

## Task 1: Settings / config

**Files:**
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_config.py
from app.config import get_settings, REPO_ROOT, ENV_FILE, PROMPTS_DIR


def test_settings_read_env(monkeypatch):
    monkeypatch.setenv("HUBSPOT_TOKEN", "pat-xyz")
    get_settings.cache_clear()
    s = get_settings()
    assert s.hubspot_token == "pat-xyz"
    assert s.claude_model == "claude-sonnet-4-6"
    assert s.hubspot_pipeline_id == "default"
    assert s.hubspot_stage_demo_requested == "3832955632"
    assert s.hubspot_stage_disqualified == "3840698071"


def test_path_constants_point_at_repo():
    assert (REPO_ROOT / "prompts").exists()
    assert ENV_FILE.name == ".env"
    assert PROMPTS_DIR.name == "prompts"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.config'`.

- [ ] **Step 3: Write `backend/app/config.py`**

```python
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / "api-tests" / ".env"
PROMPTS_DIR = REPO_ROOT / "prompts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    anthropic_api_key: str = ""
    apollo_api_key: str = ""
    tavily_api_key: str = ""
    hubspot_token: str = ""

    hubspot_pipeline_id: str = "default"
    hubspot_stage_demo_requested: str = "3832955632"
    hubspot_stage_disqualified: str = "3840698071"

    claude_model: str = "claude-sonnet-4-6"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_config.py -v`
Expected: PASS (2 passed). Real OS env vars take precedence over the `.env` file, so the conftest dummies win in tests.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py && git commit -m "feat: settings loader reading api-tests/.env"
```

---

## Task 2: FastAPI app + /health

**Files:**
- Create: `backend/app/main.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app


def test_health_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Write `backend/app/main.py`**

```python
from fastapi import FastAPI

app = FastAPI(title="Sentio Agent Backend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_health.py -v`
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/tests/test_health.py && git commit -m "feat: FastAPI app with /health"
```

---

## Task 3: Anthropic client + prompt loader

**Files:**
- Create: `backend/app/clients/anthropic_client.py`
- Test: `backend/tests/test_anthropic_client.py`

- [ ] **Step 1: Write the failing test** (respx mocks the Messages API; the real SDK parses the response)

```python
# backend/tests/test_anthropic_client.py
import anthropic
import respx
from httpx import Response

from app.clients.anthropic_client import AnthropicClient, load_prompt

MESSAGES_URL = "https://api.anthropic.com/v1/messages"


def _message_json(text: str) -> dict:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 5, "output_tokens": 2},
    }


@respx.mock
def test_complete_returns_text():
    route = respx.post(MESSAGES_URL).mock(
        return_value=Response(200, json=_message_json("ok"))
    )
    sdk = anthropic.Anthropic(api_key="test")
    client = AnthropicClient(client=sdk, model="claude-sonnet-4-6")
    out = client.complete(system="You are a test.", user="ping", max_tokens=16)
    assert out == "ok"
    assert route.called
    sent = route.calls.last.request
    assert b'"model":"claude-sonnet-4-6"' in sent.content.replace(b" ", b"")


def test_load_prompt_reads_repo_prompt():
    text = load_prompt("research_agent.md")
    assert "Research Agent" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anthropic_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.clients.anthropic_client'`.

- [ ] **Step 3: Write `backend/app/clients/anthropic_client.py`**

```python
from __future__ import annotations

import anthropic

from app.config import PROMPTS_DIR, get_settings


def load_prompt(name: str) -> str:
    """Read a system prompt markdown file from the repo `prompts/` dir."""
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


class AnthropicClient:
    """Thin wrapper over the official Anthropic SDK.

    The SDK client is injectable so tests can run against a mocked transport.
    Model defaults to the project-pinned claude-sonnet-4-6.
    """

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self._client = client or anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self._model = model or settings.claude_model

    def complete(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_anthropic_client.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/anthropic_client.py backend/tests/test_anthropic_client.py && git commit -m "feat: Anthropic client wrapper + prompt loader"
```

---

## Task 4: Apollo client + JSON cache (cache-first)

**Files:**
- Create: `backend/app/clients/apollo_client.py`
- Test: `backend/tests/test_apollo_client.py`

- [ ] **Step 1: Write the failing test** (verifies a second call is served from cache with no second HTTP request)

```python
# backend/tests/test_apollo_client.py
import httpx
import respx
from httpx import Response

from app.clients.apollo_client import ApolloClient

PEOPLE_URL = "https://api.apollo.io/api/v1/people/match"
ORG_URL = "https://api.apollo.io/api/v1/organizations/enrich"


@respx.mock
def test_enrich_person_caches(tmp_path):
    route = respx.post(PEOPLE_URL).mock(
        return_value=Response(200, json={"person": {"name": "Jane"}})
    )
    client = ApolloClient(http=httpx.Client(), cache_dir=tmp_path)

    first = client.enrich_person("jane@meridian.io", first_name="Jane")
    second = client.enrich_person("jane@meridian.io", first_name="Jane")

    assert first == second == {"person": {"name": "Jane"}}
    assert route.call_count == 1  # second call served from cache
    assert (tmp_path / "person_jane_at_meridian.io.json").exists()


@respx.mock
def test_enrich_person_sends_api_key_header(tmp_path):
    route = respx.post(PEOPLE_URL).mock(return_value=Response(200, json={}))
    client = ApolloClient(http=httpx.Client(), cache_dir=tmp_path)
    client.enrich_person("a@b.com")
    assert route.calls.last.request.headers["X-Api-Key"] == "test-apollo"


@respx.mock
def test_enrich_organization_caches(tmp_path):
    route = respx.get(ORG_URL).mock(
        return_value=Response(200, json={"organization": {"name": "Meridian"}})
    )
    client = ApolloClient(http=httpx.Client(), cache_dir=tmp_path)
    client.enrich_organization("meridian.io")
    client.enrich_organization("meridian.io")
    assert route.call_count == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_apollo_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.clients.apollo_client'`.

- [ ] **Step 3: Write `backend/app/clients/apollo_client.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

import httpx

from app.config import REPO_ROOT, get_settings

DEFAULT_CACHE_DIR = REPO_ROOT / "cache" / "apollo"


class ApolloClient:
    """Apollo enrichment with cache-first lookup.

    Responses are cached to local JSON keyed by email (people) or domain (org);
    a cache hit skips the API call entirely to protect the free-tier credit limit.
    """

    BASE = "https://api.apollo.io/api/v1"

    def __init__(
        self,
        http: httpx.Client | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        self._key = get_settings().apollo_api_key
        self._http = http or httpx.Client(timeout=30)
        self._cache = cache_dir or DEFAULT_CACHE_DIR
        self._cache.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, kind: str, key: str) -> Path:
        safe = key.lower().replace("/", "_").replace("@", "_at_")
        return self._cache / f"{kind}_{safe}.json"

    def _read_cache(self, path: Path) -> dict | None:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def _write_cache(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data), encoding="utf-8")

    def enrich_person(self, email: str, **fields: str) -> dict:
        path = self._cache_path("person", email)
        cached = self._read_cache(path)
        if cached is not None:
            return cached
        resp = self._http.post(
            f"{self.BASE}/people/match",
            headers={"X-Api-Key": self._key, "Content-Type": "application/json"},
            json={"email": email, **fields},
        )
        resp.raise_for_status()
        data = resp.json()
        self._write_cache(path, data)
        return data

    def enrich_organization(self, domain: str) -> dict:
        path = self._cache_path("org", domain)
        cached = self._read_cache(path)
        if cached is not None:
            return cached
        resp = self._http.get(
            f"{self.BASE}/organizations/enrich",
            params={"domain": domain},
            headers={"X-Api-Key": self._key, "Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        self._write_cache(path, data)
        return data
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_apollo_client.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/apollo_client.py backend/tests/test_apollo_client.py && git commit -m "feat: Apollo client with cache-first JSON caching"
```

---

## Task 5: Tavily client + call budget

**Files:**
- Create: `backend/app/clients/tavily_client.py`
- Test: `backend/tests/test_tavily_client.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_tavily_client.py
import httpx
import pytest
import respx
from httpx import Response

from app.clients.tavily_client import TavilyBudgetError, TavilyClient

SEARCH_URL = "https://api.tavily.com/search"


@respx.mock
def test_search_returns_json_and_sends_bearer():
    route = respx.post(SEARCH_URL).mock(
        return_value=Response(200, json={"results": [{"url": "x"}]})
    )
    client = TavilyClient(http=httpx.Client(), max_calls=3)
    out = client.search("vp customer success hire")
    assert out == {"results": [{"url": "x"}]}
    assert route.calls.last.request.headers["Authorization"] == "Bearer test-tavily"


@respx.mock
def test_budget_enforced():
    respx.post(SEARCH_URL).mock(return_value=Response(200, json={}))
    client = TavilyClient(http=httpx.Client(), max_calls=2)
    client.search("a")
    client.search("b")
    with pytest.raises(TavilyBudgetError):
        client.search("c")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_tavily_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.clients.tavily_client'`.

- [ ] **Step 3: Write `backend/app/clients/tavily_client.py`**

```python
from __future__ import annotations

import httpx

from app.config import get_settings


class TavilyBudgetError(RuntimeError):
    """Raised when the per-run Tavily call budget is exhausted."""


class TavilyClient:
    """Tavily search with a per-instance call budget.

    The research loop creates one client per lead and is capped at `max_calls`
    searches so a single run cannot blow the free-tier quota.
    """

    URL = "https://api.tavily.com/search"

    def __init__(self, http: httpx.Client | None = None, max_calls: int = 3) -> None:
        self._key = get_settings().tavily_api_key
        self._http = http or httpx.Client(timeout=30)
        self._max_calls = max_calls
        self._calls = 0

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        time_range: str | None = None,
    ) -> dict:
        if self._calls >= self._max_calls:
            raise TavilyBudgetError(
                f"Tavily call budget ({self._max_calls}) exhausted"
            )
        self._calls += 1
        payload: dict = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": False,
        }
        if time_range:
            payload["time_range"] = time_range
        resp = self._http.post(
            self.URL,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_tavily_client.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/tavily_client.py backend/tests/test_tavily_client.py && git commit -m "feat: Tavily client with per-run call budget"
```

---

## Task 6: HubSpot client — contact upsert, deal upsert, note

**Files:**
- Create: `backend/app/clients/hubspot_client.py`
- Test: `backend/tests/test_hubspot_client.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_hubspot_client.py
import httpx
import respx
from httpx import Response

from app.clients.hubspot_client import HubSpotClient

BASE = "https://api.hubapi.com"


def _client() -> HubSpotClient:
    return HubSpotClient(http=httpx.Client())


@respx.mock
def test_upsert_contact_returns_id_and_sends_bearer():
    route = respx.post(f"{BASE}/crm/v3/objects/contacts/batch/upsert").mock(
        return_value=Response(200, json={"results": [{"id": "501"}]})
    )
    cid = _client().upsert_contact("jane@meridian.io", {"firstname": "Jane"})
    assert cid == "501"
    req = route.calls.last.request
    assert req.headers["Authorization"] == "Bearer test-hubspot"
    assert b'"idProperty":"email"' in req.content.replace(b" ", b"")


@respx.mock
def test_upsert_deal_creates_when_none_found():
    respx.post(f"{BASE}/crm/v3/objects/deals/search").mock(
        return_value=Response(200, json={"results": []})
    )
    create = respx.post(f"{BASE}/crm/v3/objects/deals").mock(
        return_value=Response(201, json={"id": "900"})
    )
    did = _client().upsert_deal(
        name="Meridian — inbound", stage="3832955632", contact_id="501"
    )
    assert did == "900"
    body = create.calls.last.request.content.replace(b" ", b"")
    assert b'"dealstage":"3832955632"' in body
    assert b'"pipeline":"default"' in body
    assert b'"associationTypeId":3' in body


@respx.mock
def test_upsert_deal_updates_when_found():
    respx.post(f"{BASE}/crm/v3/objects/deals/search").mock(
        return_value=Response(200, json={"results": [{"id": "777"}]})
    )
    patch = respx.patch(f"{BASE}/crm/v3/objects/deals/777").mock(
        return_value=Response(200, json={"id": "777"})
    )
    did = _client().upsert_deal(
        name="Meridian — inbound", stage="3840698071", contact_id="501"
    )
    assert did == "777"
    assert b'"dealstage":"3840698071"' in patch.calls.last.request.content.replace(b" ", b"")


@respx.mock
def test_create_note_associates_to_deal():
    note = respx.post(f"{BASE}/crm/v3/objects/notes").mock(
        return_value=Response(201, json={"id": "n1"})
    )
    nid = _client().create_note("hand-off notes", deal_id="900")
    assert nid == "n1"
    body = note.calls.last.request.content.replace(b" ", b"")
    assert b'"associationTypeId":214' in body
    assert b'"hs_note_body"' in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_hubspot_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.clients.hubspot_client'`.

- [ ] **Step 3: Write `backend/app/clients/hubspot_client.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.config import get_settings

# HubSpot-defined default association type IDs
ASSOC_DEAL_TO_CONTACT = 3
ASSOC_NOTE_TO_DEAL = 214


class HubSpotClient:
    """HubSpot CRM v3: contact/deal upsert and note attachment.

    Idempotent by email/name so repeat bookings refresh records instead of
    duplicating them. Stage is set by the caller's routing outcome.
    """

    BASE = "https://api.hubapi.com"

    def __init__(self, http: httpx.Client | None = None) -> None:
        s = get_settings()
        self._token = s.hubspot_token
        self._pipeline = s.hubspot_pipeline_id
        self._http = http or httpx.Client(timeout=30)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def upsert_contact(self, email: str, properties: dict) -> str:
        body = {
            "inputs": [
                {
                    "idProperty": "email",
                    "id": email,
                    "properties": {"email": email, **properties},
                }
            ]
        }
        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/contacts/batch/upsert",
            headers=self._headers(),
            json=body,
        )
        resp.raise_for_status()
        return resp.json()["results"][0]["id"]

    def _find_deal_id(self, name: str) -> str | None:
        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/deals/search",
            headers=self._headers(),
            json={
                "filterGroups": [
                    {
                        "filters": [
                            {"propertyName": "dealname", "operator": "EQ", "value": name}
                        ]
                    }
                ]
            },
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0]["id"] if results else None

    def upsert_deal(self, name: str, stage: str, contact_id: str) -> str:
        existing = self._find_deal_id(name)
        if existing:
            resp = self._http.patch(
                f"{self.BASE}/crm/v3/objects/deals/{existing}",
                headers=self._headers(),
                json={"properties": {"dealstage": stage, "pipeline": self._pipeline}},
            )
            resp.raise_for_status()
            return existing

        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/deals",
            headers=self._headers(),
            json={
                "properties": {
                    "dealname": name,
                    "pipeline": self._pipeline,
                    "dealstage": stage,
                },
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": ASSOC_DEAL_TO_CONTACT,
                            }
                        ],
                    }
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def create_note(self, body: str, deal_id: str) -> str:
        resp = self._http.post(
            f"{self.BASE}/crm/v3/objects/notes",
            headers=self._headers(),
            json={
                "properties": {
                    "hs_timestamp": datetime.now(timezone.utc).isoformat(),
                    "hs_note_body": body,
                },
                "associations": [
                    {
                        "to": {"id": deal_id},
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": ASSOC_NOTE_TO_DEAL,
                            }
                        ],
                    }
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["id"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_hubspot_client.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/hubspot_client.py backend/tests/test_hubspot_client.py && git commit -m "feat: HubSpot client — contact/deal upsert + note attach"
```

---

## Task 7: Full suite green + app boots

**Files:** none (verification task)

- [ ] **Step 1: Run the whole test suite**

Run: `.venv/Scripts/python.exe -m pytest -v`
Expected: all tests pass (config 2, health 1, anthropic 2, apollo 3, tavily 2, hubspot 4 = 14 passed).

- [ ] **Step 2: Boot the app to confirm it serves**

Run:
```bash
.venv/Scripts/python.exe -c "from fastapi.testclient import TestClient; from app.main import app; print(TestClient(app).get('/health').json())"
```
Expected: `{'status': 'ok'}`.

- [ ] **Step 3: Commit a short Phase-1 README**

Create `backend/README.md`:
```markdown
# Sentio Agent Backend

Phase 1: foundation + API clients. Run from `backend/`:

    python -m venv .venv
    .venv/Scripts/python.exe -m pip install -r requirements.txt
    .venv/Scripts/python.exe -m pytest          # unit tests (no network)
    .venv/Scripts/python.exe -m uvicorn app.main:app --reload   # serve /health

Secrets load from `../api-tests/.env`. LLM model is pinned to `claude-sonnet-4-6`.
Clients: `app/clients/{anthropic,apollo,tavily,hubspot}_client.py`.
```

```bash
git add backend/README.md && git commit -m "docs: Phase 1 backend README"
```

- [ ] **Step 4: Update the root task list**

In `TASKS.md`, change the Phase 1 checkboxes (FastAPI scaffold, the four integrations, tests) from `[ ]` to `[x]`. Commit:
```bash
git add TASKS.md && git commit -m "chore: mark Phase 1 tasks complete"
```

---

## Self-Review

- **Spec coverage:** FastAPI scaffold (Task 0, 2) ✓; config/secrets (Task 1) ✓; Anthropic client + prompt loader (Task 3) ✓; Apollo enrich + cache-first (Task 4) ✓; Tavily + 3-call cap (Task 5) ✓; HubSpot upsert + notes with correct pipeline/stages (Task 6) ✓; per-integration mocked tests (every task) ✓. Live smoke per provider already exists as `api-tests/smoke-test.sh` — not duplicated in pytest.
- **Type/name consistency:** `get_settings()` field names match `.env` keys; `AnthropicClient.complete`, `ApolloClient.enrich_person/enrich_organization`, `TavilyClient.search`, `HubSpotClient.upsert_contact/upsert_deal/create_note` are referenced identically in tests and impl. Pipeline `default`, stages `3832955632`/`3840698071` match the corrected HubSpot config.
- **Placeholders:** none.
- **Deferred to later phases (out of scope here):** business endpoints `/demo` and `/chat` (Phase 5), the scoring engine (Phase 2), and the agents themselves (Phase 3) — this phase only builds the clients they will call.
