import json

from app.chat.models import QualificationState
from app.chat.orchestrator import handle_turn
from app.rag.store import Chunk

# Structured Sage reply (answer + qualifying question) used by the stub LLM.
SAGE_JSON = json.dumps({
    "answer": "Sentio gives a 60-90 day churn warning.",
    "question": "Are you on a CS team or RevOps?",
})


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
            return SAGE_JSON
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


def test_low_confidence_redirects_without_terminal_action():
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "escalate"}))  # classifier outcome ignored on redirect
    turn = handle_turn(_state(), "tell me a poem", llm=llm, retriever=StubRetriever(0.10),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is False
    assert turn.outcome == "continue"
    assert turn.question is None
    assert hubspot.calls == []  # no terminal CRM action on an off-topic redirect


def test_continue_turn_answers_with_question_and_writes_no_crm():
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "continue", "signals": {"team_context": "CS team"}}))
    state = _state()
    turn = handle_turn(state, "what does sentio do?", llm=llm, retriever=StubRetriever(0.55),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is False
    assert turn.outcome == "continue"
    assert turn.booked is False
    assert turn.question == "Are you on a CS team or RevOps?"
    assert "60-90 day" in turn.reply
    assert hubspot.calls == []
    assert state.signals["team_context"] == "CS team"
    assert len(state.history) == 2  # user + assistant answer


def test_classifier_sees_visitor_message_but_not_fresh_answer():
    """The two LLM calls run concurrently; the classifier reads the transcript up to
    the visitor's latest message, never Sage's freshly generated answer."""
    captured = {}

    class CaptureLLM(StubLLM):
        def complete(self, system, user, max_tokens=1024):
            if "qualification router" in system:
                captured["transcript"] = user
            return super().complete(system, user, max_tokens)

    llm = CaptureLLM(json.dumps({"outcome": "continue"}))
    handle_turn(_state(), "what does sentio do?", llm=llm, retriever=StubRetriever(0.55),
                apollo=StubApollo(), tavily=StubTavily(), hubspot=StubHubSpot())
    assert "what does sentio do?" in captured["transcript"]
    assert "60-90 day churn warning" not in captured["transcript"]


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


def test_escalate_without_email_asks_for_email_no_crm():
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "escalate"})
    llm = StubLLM(payload)
    turn = handle_turn(_state(), "we need a custom enterprise contract and SSO",
                       llm=llm, retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "escalate"
    assert turn.escalated is True
    assert "work email" in turn.reply  # email-capture ask appended
    assert "connect" not in turn.reply.lower()  # no fake live-handoff wording
    assert hubspot.calls == []  # no CRM record without an email


def test_escalate_with_email_writes_followup_record():
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "escalate", "email": "ciso@bigco.com"})
    llm = StubLLM(payload)
    state = _state()
    turn = handle_turn(state, "I need to talk to someone about our DPA, here's my email ciso@bigco.com",
                       llm=llm, retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "escalate"
    assert turn.escalated is True
    assert state.email == "ciso@bigco.com"
    assert ("contact", "ciso@bigco.com") in hubspot.calls
    note = [c for c in hubspot.calls if c[0] == "note"][0]
    assert "Escalated via chat" in note[1]


def test_escalate_crm_failure_is_swallowed_and_reply_returned():
    hubspot = StubHubSpot(fail=True)
    payload = json.dumps({"outcome": "escalate", "email": "ciso@bigco.com"})
    llm = StubLLM(payload)
    turn = handle_turn(_state(), "need legal review, ciso@bigco.com", llm=llm,
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is True
    assert turn.reply  # conversation survives the CRM failure


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
