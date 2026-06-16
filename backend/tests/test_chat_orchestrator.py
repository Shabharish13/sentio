import json

from app.chat.models import QualificationState
from app.chat.orchestrator import handle_turn
from app.rag.store import Chunk


class StubRetriever:
    def __init__(self, score):
        self._score = score

    def retrieve(self, query, k=4):
        return [Chunk(text="Sentio scores account health.", source="product-overview.md", score=self._score)]


class StubLLM:
    """Routes by prompt markers: classifier JSON / Sage reply / research / email."""

    def __init__(self, outcome_payload):
        self._outcome = outcome_payload
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append(system)
        if "qualification router" in system:
            return self._outcome
        if "[CONTEXT]" in system:
            return "Sentio gives a 60–90 day churn warning. Are you on a CS team or RevOps?"
        if "[ENRICHED RECORD]" in user:
            return json.dumps({"action": "final", "top_signal": "Raised a Series B",
                               "signal_type": "funding", "source_url": "https://x"})
        return "Hi there,\n\nNoticed your growth...\n\nBest,\nAlex"


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
    def __init__(self, fail=False):
        self.calls = []
        self._fail = fail

    def upsert_contact(self, email, properties):
        if self._fail:
            raise RuntimeError("hubspot down")
        self.calls.append(("contact", email)); return "c1"

    def upsert_deal(self, name, stage, contact_id):
        self.calls.append(("deal", name, stage)); return "d1"

    def create_note(self, body, deal_id):
        self.calls.append(("note", body)); return "n1"


def _state(page="/pricing"):
    return QualificationState(session_id="s1", page=page)


def test_low_confidence_escalates_without_classifying_or_crm():
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "continue"}))
    turn = handle_turn(_state(), "tell me a poem", llm=llm, retriever=StubRetriever(0.10),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is True
    assert turn.outcome == "escalate"
    assert hubspot.calls == []
    # classifier (qualification router) never invoked
    assert not any("qualification router" in s for s in llm.calls)


def test_continue_turn_answers_and_writes_no_crm():
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "continue", "signals": {"team_context": "CS team"}}))
    state = _state()
    turn = handle_turn(state, "what does sentio do?", llm=llm, retriever=StubRetriever(0.55),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is False
    assert turn.outcome == "continue"
    assert turn.booked is False
    assert hubspot.calls == []
    assert state.signals["team_context"] == "CS team"
    assert len(state.history) == 2


def test_book_with_email_runs_pipeline_and_attaches_transcript():
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "book", "email": "jane@meridian.io",
                          "signals": {"authority": "VP of Customer Success",
                                      "timeline": "this quarter", "company_scale": "200+"}})
    llm = StubLLM(payload)
    state = _state()
    state.add("user", "earlier context")
    turn = handle_turn(state, "yes here is my email jane@meridian.io",
                       llm=llm, retriever=StubRetriever(0.55),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.booked is True
    assert state.crm.stage == "3832955632"
    notes = [c for c in hubspot.calls if c[0] == "note"]
    assert any("Transcript:" in n[1] for n in notes)  # chat transcript note attached
    assert state.email == "jane@meridian.io"


def test_disqualify_with_email_writes_disqualified_deal_with_reason():
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "disqualify", "email": "sam@hobby.dev",
                          "reason": "pre-revenue solo founder, no CS function"})
    llm = StubLLM(payload)
    state = _state()
    turn = handle_turn(state, "just me building a side project", llm=llm,
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "disqualify"
    deal = [c for c in hubspot.calls if c[0] == "deal"][0]
    assert deal[2] == "3840698071"
    note = [c for c in hubspot.calls if c[0] == "note"][0]
    assert "solo founder" in note[1]


def test_disqualify_without_email_closes_warmly_no_crm():
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "disqualify", "email": None, "reason": "student project"})
    llm = StubLLM(payload)
    turn = handle_turn(_state(), "i'm a student", llm=llm, retriever=StubRetriever(0.55),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "disqualify"
    assert turn.booked is False
    assert hubspot.calls == []


def test_crm_failure_is_swallowed_and_reply_still_returned():
    hubspot = StubHubSpot(fail=True)
    payload = json.dumps({"outcome": "book", "email": "jane@meridian.io",
                          "signals": {"authority": "VP CS", "company_scale": "200+"}})
    llm = StubLLM(payload)
    turn = handle_turn(_state(), "book me jane@meridian.io", llm=llm,
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.booked is False
    assert turn.reply  # conversation survives the integration failure
