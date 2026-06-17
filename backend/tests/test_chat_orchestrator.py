import json

from app.agents.sage import REDIRECT_MESSAGE
from app.chat.models import QualificationState
from app.chat.orchestrator import handle_turn
from app.rag.store import Chunk

# Structured Sage reply used by the stub LLM. Sage now returns only the answer (+
# off_topic); the qualifying question is owned by the classifier/router.
SAGE_JSON = json.dumps({
    "answer": "Sentio gives a 60-90 day churn warning.",
    "off_topic": False,
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

    def complete(self, system, user, max_tokens=1024, reasoning_effort=None):
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


class ContextAwareRetriever:
    """Scores by query content the way the real embedder does: a bare follow-up
    retrieves nothing (off-topic), but once the query is anchored to the prior
    'discount/Growth' turn it scores on-topic. The fixed-score stub above papers
    over exactly the context-blindness this reproduces."""

    def retrieve(self, query, k=4):
        q = query.lower()
        score = 0.55 if ("discount" in q or "growth" in q) else 0.10
        return [Chunk(text="Growth multi-year discounts.", source="pricing-tiers.md", score=score)]


def _state(page="/pricing"):
    return QualificationState(session_id="s1", page=page)


def test_followup_answering_sages_question_is_not_bounced_as_offtopic():
    # The CMO-reported bug: visitor answers Sage's own timeline question with a high-
    # intent reply that has no product keywords. Context-blind retrieval scored it
    # off-topic and bounced a hot lead. Anchored to the prior turn, Sage answers.
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "continue"}))
    state = _state()
    state.add("user", "Is there a discount for the Growth plan?")
    state.add("assistant", "Multi-year discounts are available on Growth.\nAre you rolling out this quarter?")
    turn = handle_turn(state, "I want to rollout as soon as possible", llm=llm,
                       retriever=ContextAwareRetriever(), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.reply != REDIRECT_MESSAGE      # not the off-topic brush-off
    assert "60-90 day" in turn.reply           # Sage actually answered (SAGE_JSON)


def test_assistant_question_is_recorded_in_history_for_next_turn():
    # The qualifying question is part of what the visitor saw, so it must be stored in
    # history - the next turn's retrieval and the classifier need the context the
    # visitor is replying to.
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "continue",
                              "next_question": "Are you on a CS team or RevOps?"}))
    state = _state()
    handle_turn(state, "what does sentio do?", llm=llm, retriever=StubRetriever(0.55),
                apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert "Are you on a CS team or RevOps?" in state.history[1]["content"]


def test_low_confidence_offtopic_redirects_without_terminal_action():
    # Genuinely off-topic chatter: the classifier agrees it's not a handoff, so the
    # redirect stands and no terminal action runs.
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "continue"}))
    turn = handle_turn(_state(), "tell me a poem", llm=llm, retriever=StubRetriever(0.10),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is False
    assert turn.outcome == "continue"
    assert turn.question is None
    assert hubspot.calls == []  # no terminal CRM action on an off-topic redirect


def test_redirect_with_escalation_intent_is_honored_and_asks_for_email():
    # "Can I talk to a human?" retrieves no KB content, so Sage redirects — but the
    # classifier flags a real handoff. The escalation must survive the redirect
    # instead of being bounced with the off-topic message.
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "escalate"}))
    turn = handle_turn(_state(), "can I talk to a human?", llm=llm, retriever=StubRetriever(0.10),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "escalate"      # not swallowed by the redirect
    assert turn.escalated is False         # no email captured yet
    assert "work email" in turn.reply      # routes to a human + asks for the email
    assert turn.reply != REDIRECT_MESSAGE  # not the off-topic brush-off
    assert hubspot.calls == []             # nothing written without an email


def test_redirect_with_escalation_intent_and_email_hands_off():
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "escalate"}))
    turn = handle_turn(_state(), "connect me to sales: buyer@acme.com", llm=llm,
                       retriever=StubRetriever(0.10), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "escalate"
    assert turn.escalated is True          # email present -> actual handoff
    assert any(c[0] == "deal" for c in hubspot.calls)  # escalation CRM record written


def test_continue_turn_answers_with_question_and_writes_no_crm():
    hubspot = StubHubSpot()
    # The qualifying question rides on the classifier payload now, not the Sage reply.
    llm = StubLLM(json.dumps({"outcome": "continue", "signals": {"team_context": "CS team"},
                              "next_question": "Are you on a CS team or RevOps?"}))
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
        def complete(self, system, user, max_tokens=1024, reasoning_effort=None):
            if "qualification router" in system:
                captured["transcript"] = user
            return super().complete(system, user, max_tokens, reasoning_effort)

    llm = CaptureLLM(json.dumps({"outcome": "continue"}))
    handle_turn(_state(), "what does sentio do?", llm=llm, retriever=StubRetriever(0.55),
                apollo=StubApollo(), tavily=StubTavily(), hubspot=StubHubSpot())
    assert "what does sentio do?" in captured["transcript"]
    assert "60-90 day churn warning" not in captured["transcript"]


def test_terminal_turn_surfaces_no_qualifying_question():
    # The CMO double-ask bug: on the close (escalate) the turn must not also ask a
    # qualifying question. Even if the classifier payload smuggles a next_question, the
    # router nulls it on terminal outcomes, so the visitor sees only the email ask.
    hubspot = StubHubSpot()
    llm = StubLLM(json.dumps({"outcome": "escalate",
                              "next_question": "Growth with a pilot, or Starter annual?"}))
    turn = handle_turn(_state(), "1 year contract, how do I move forward?", llm=llm,
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "escalate"
    assert turn.question is None              # no contradictory second ask
    assert "work email" in turn.reply         # the close: just the email ask


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
    # escalated reflects an ACTUAL handoff (email captured), not the raw intent. With
    # no email yet, nothing was shared — so the UI must not claim it was.
    assert turn.escalated is False
    assert "work email" in turn.reply  # email-capture ask appended instead
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
    # booked is reported optimistically (the lead qualified + gave an email); the CRM
    # write happens off the reply path and its failure is swallowed, not surfaced.
    assert turn.booked is True
    assert turn.reply  # conversation survives the integration failure


def test_terminal_handoff_is_deferred_to_scheduler_not_run_inline():
    """The heavy book/escalate/disqualify handoff (research -> copywriter -> CRM)
    must not run on the reply path: it is handed to the injected scheduler so the
    visitor gets their reply immediately."""
    hubspot = StubHubSpot()
    deferred = []
    payload = json.dumps({"outcome": "book", "email": "jane@meridian.io",
                          "signals": {"authority": "VP CS", "company_scale": "200+"}})
    turn = handle_turn(_state(), "book me jane@meridian.io", llm=StubLLM(payload),
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot, schedule=deferred.append)
    assert turn.booked is True            # reported optimistically, before the write
    assert hubspot.calls == []            # nothing written on the reply path
    assert len(deferred) == 1             # the handoff was scheduled, not executed
    deferred[0]()                         # running it now performs the CRM writes
    assert any(c[0] == "deal" for c in hubspot.calls)


def test_deterministic_email_from_message_triggers_handoff_without_classifier_email():
    """Email presence is decided by code (regex on the message), not the classifier:
    the lead is booked even when the classifier payload omits the email field."""
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "book",
                          "signals": {"authority": "VP CS", "company_scale": "200+"}})
    state = _state()
    turn = handle_turn(state, "great, reach me at dana@gitlab.com", llm=StubLLM(payload),
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert state.email == "dana@gitlab.com"
    assert turn.booked is True


def test_book_redirected_with_email_is_not_bounced_and_books():
    # The reported bug: a short booking confirmation ("ok book it, me@acme.com")
    # retrieves no KB content so Sage redirects - but it's a real Book and must NOT be
    # swallowed by the off-topic guard.
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "book", "email": "me@acme.com",
                          "signals": {"authority": "VP CS", "company_scale": "200+"}})
    turn = handle_turn(_state(), "ok book it, me@acme.com", llm=StubLLM(payload),
                       retriever=StubRetriever(0.10),  # below threshold -> redirected
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.booked is True
    assert turn.reply != REDIRECT_MESSAGE
    assert any(c[0] == "deal" for c in hubspot.calls)


def test_terminal_reply_confirms_and_does_not_contradict_action():
    # When a deal is actually written, the reply confirms the handoff instead of
    # claiming it cannot capture emails.
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "escalate", "email": "ciso@bigco.com"})
    turn = handle_turn(_state(), "we need a security review, ciso@bigco.com",
                       llm=StubLLM(payload), retriever=StubRetriever(0.55),
                       apollo=StubApollo(), tavily=StubTavily(), hubspot=hubspot)
    assert turn.escalated is True
    low = turn.reply.lower()
    assert "cannot" not in low and "can't" not in low
    assert "team" in low  # confirms the handoff happened


def test_book_without_email_asks_for_email_no_crm():
    # A qualified booker with no email yet must be ASKED for it (the Book pipeline
    # needs it). Previously the book branch said nothing and the lead dead-ended.
    hubspot = StubHubSpot()
    payload = json.dumps({"outcome": "book",
                          "signals": {"authority": "VP of Customer Success",
                                      "timeline": "this quarter", "company_scale": "200+"}})
    turn = handle_turn(_state(), "yes, I'd like to book a demo", llm=StubLLM(payload),
                       retriever=StubRetriever(0.55), apollo=StubApollo(),
                       tavily=StubTavily(), hubspot=hubspot)
    assert turn.outcome == "book"
    assert turn.booked is False           # no email captured yet
    assert "work email" in turn.reply     # email-capture ask appended
    assert turn.question is None          # terminal: no qualifying question
    assert hubspot.calls == []            # nothing written without an email
