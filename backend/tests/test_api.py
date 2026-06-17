import json

import pytest
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app
from app.rag.store import Chunk


class StubLLM:
    def __init__(self, outcome="continue"):
        self._outcome = outcome

    def complete(self, system, user, max_tokens=1024, reasoning_effort=None):
        if "qualification router" in system:
            # The qualifying question is the router's output now, not Sage's.
            return json.dumps({"outcome": self._outcome,
                               "next_question": "Are you on a CS team or RevOps?"})
        if "[CONTEXT]" in system:
            return json.dumps({"answer": "Sentio scores account health.",
                               "off_topic": False})
        if "[ENRICHED RECORD]" in user:
            return json.dumps({"action": "final", "top_signal": "Raised a Series B",
                               "signal_type": "funding", "source_url": "https://x"})
        return "Hi Jane,\n\nNoticed your Series B...\n\nBest,\nAlex"


class StubApollo:
    def enrich_organization(self, domain):
        return {"organization": {"estimated_num_employees": 210, "industry": "Computer Software",
                                 "country": "United States", "technology_names": ["HubSpot"]}}

    def enrich_person(self, email, **fields):
        return {"person": {"title": "VP of Customer Success", "country": "United States"}}


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


class StubRetriever:
    def __init__(self, score=0.55):
        self._score = score

    def retrieve(self, query, k=4):
        return [Chunk(text="Sentio scores account health.", source="product-overview.md", score=self._score)]


@pytest.fixture
def client():
    app.dependency_overrides[deps.provide_llm] = lambda: StubLLM()
    app.dependency_overrides[deps.provide_apollo] = lambda: StubApollo()
    app.dependency_overrides[deps.provide_tavily] = lambda: StubTavily()
    app.dependency_overrides[deps.provide_hubspot] = lambda: StubHubSpot()
    app.dependency_overrides[deps.provide_retriever] = lambda: StubRetriever()
    yield TestClient(app)
    app.dependency_overrides.clear()


A_FORM = {
    "first_name": "Jane", "last_name": "Doe", "work_email": "jane@meridian.io",
    "company_name": "Meridian Analytics", "job_title": "VP of Customer Success",
    "company_size": "201-500", "problem_stated": "surprise churn", "how_heard": "Referral",
}


def test_demo_returns_lead_brief(client):
    resp = client.post("/demo", json=A_FORM)
    assert resp.status_code == 200
    body = resp.json()
    assert body["route"] == "qualified"
    assert body["fit_grade"] == "A"
    assert body["signal_type"] == "funding"
    assert body["email_draft"].startswith("Hi Jane")
    assert body["crm_stage"] == "3832955632"
    assert body["crm_ref"] == "d1"
    assert body["contact_name"] == "Jane Doe"
    assert body["company_name"] == "Meridian Analytics"
    assert body["enriched"] is True


def test_demo_bad_email_returns_400(client):
    resp = client.post("/demo", json={**A_FORM, "work_email": "not-an-email"})
    assert resp.status_code == 400


def test_chat_answer_turn(client):
    resp = client.post("/chat", json={"message": "what does sentio do?", "page": "/pricing"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["escalated"] is False
    assert body["answer"] == "Sentio scores account health."
    assert body["reply"] == body["answer"]  # backwards-compat alias
    assert body["question"] == "Are you on a CS team or RevOps?"
    assert body["session_id"]


def test_chat_session_continuity(client):
    first = client.post("/chat", json={"message": "hi", "page": "/pricing"}).json()
    sid = first["session_id"]
    second = client.post("/chat", json={"message": "tell me more", "page": "/pricing", "session_id": sid}).json()
    assert second["session_id"] == sid


def test_chat_low_confidence_redirects():
    app.dependency_overrides[deps.provide_llm] = lambda: StubLLM()
    app.dependency_overrides[deps.provide_apollo] = lambda: StubApollo()
    app.dependency_overrides[deps.provide_tavily] = lambda: StubTavily()
    app.dependency_overrides[deps.provide_hubspot] = lambda: StubHubSpot()
    app.dependency_overrides[deps.provide_retriever] = lambda: StubRetriever(score=0.10)
    try:
        c = TestClient(app)
        body = c.post("/chat", json={"message": "write me a poem", "page": "/"}).json()
        # Off-topic / low confidence is a redirect, not an escalation.
        assert body["escalated"] is False
        assert body["outcome"] == "continue"
        assert body["question"] is None
        assert "Sentio" in body["answer"]
    finally:
        app.dependency_overrides.clear()


def test_chat_empty_message_400(client):
    resp = client.post("/chat", json={"message": "   ", "page": "/"})
    assert resp.status_code == 400


def test_chat_route_passes_background_scheduler_to_handle_turn(client, monkeypatch):
    """The route must hand the orchestrator a FastAPI BackgroundTasks scheduler so
    the CRM handoff runs off the reply path, not inline during the request."""
    from starlette.background import BackgroundTasks
    from app.chat.models import ChatTurn

    captured = {}

    def fake_handle_turn(state, message, **kwargs):
        captured["schedule"] = kwargs.get("schedule")
        return ChatTurn(session_id=state.session_id, reply="hi", question=None,
                        outcome="continue", escalated=False, booked=False, sources=[])

    monkeypatch.setattr("app.api.routes.handle_turn", fake_handle_turn)
    client.post("/chat", json={"message": "hello", "page": "/"})
    schedule = captured["schedule"]
    assert callable(schedule)
    assert isinstance(getattr(schedule, "__self__", None), BackgroundTasks)


def test_chat_book_runs_crm_as_background_task():
    """A qualifying chat turn returns the reply immediately and the CRM handoff runs
    as a FastAPI background task (executed by TestClient after the response)."""
    hubspot = StubHubSpot()
    app.dependency_overrides[deps.provide_llm] = lambda: StubLLM(outcome="book")
    app.dependency_overrides[deps.provide_apollo] = lambda: StubApollo()
    app.dependency_overrides[deps.provide_tavily] = lambda: StubTavily()
    app.dependency_overrides[deps.provide_hubspot] = lambda: hubspot
    app.dependency_overrides[deps.provide_retriever] = lambda: StubRetriever()
    try:
        c = TestClient(app)
        body = c.post("/chat", json={"message": "book us, i'm dana@gitlab.com", "page": "/demo"}).json()
        assert body["booked"] is True
        assert body["answer"]
        # The deal write happened via the scheduled background task, not a fake.
        assert any(call[0] == "deal" for call in hubspot.calls)
    finally:
        app.dependency_overrides.clear()
