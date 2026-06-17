import json

from app.agents.sage import REDIRECT_MESSAGE, SageResponse, answer
from app.rag.store import Chunk


class StubLLM:
    def __init__(self, reply):
        self._reply = reply
        self.calls = []
        self.reasoning_efforts = []

    def complete(self, system, user, max_tokens=1024, reasoning_effort=None):
        self.calls.append((system, user))
        self.reasoning_efforts.append(reasoning_effort)
        return self._reply


class StubRetriever:
    def __init__(self, chunks):
        self._chunks = chunks
        self.queries = []

    def retrieve(self, query, k=4):
        self.queries.append(query)
        return list(self._chunks)


def test_grounded_answer_parses_structured_output():
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91),
              Chunk("[Pricing] Starter is $18k/yr.", "pricing-tiers.md", 0.82)]
    payload = json.dumps({
        "answer": "Growth is $36k/year.",
        "question": "Are you evaluating for your own team, or a broader group?",
    })
    llm = StubLLM(payload)
    resp = answer("how much is growth?", page="/pricing", llm=llm, retriever=StubRetriever(chunks))
    assert isinstance(resp, SageResponse)
    assert resp.redirected is False
    assert "36k" in resp.answer
    assert not hasattr(resp, "question")  # the qualifying question is the router's job now
    assert resp.sources == ["pricing-tiers.md", "pricing-tiers.md"]
    system, _user = llm.calls[0]
    assert "Growth is $36k/yr." in system
    assert "/pricing" in system


def test_reply_uses_minimal_reasoning_for_low_latency():
    # The conversational reply is RAG-grounded recall, not a reasoning task — it runs
    # on the visitor's critical path, so it asks for minimal reasoning to stay fast.
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91)]
    llm = StubLLM(json.dumps({"answer": "Growth is $36k/year.", "question": None}))
    answer("how much?", page="/pricing", llm=llm, retriever=StubRetriever(chunks))
    assert llm.reasoning_efforts == ["minimal"]


def test_non_json_reply_falls_back_to_raw_text():
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91)]
    resp = answer("how much?", page="/pricing",
                  llm=StubLLM("Growth is $36k/year."), retriever=StubRetriever(chunks))
    assert resp.redirected is False
    assert "36k" in resp.answer


def test_redirects_when_top_score_below_threshold():
    chunks = [Chunk("vaguely related", "faq-objections.md", 0.20)]
    llm = StubLLM("should not be called")
    resp = answer("do you integrate with SAP S/4HANA?", page="/pricing",
                  llm=llm, retriever=StubRetriever(chunks))
    assert resp.redirected is True
    assert resp.answer == REDIRECT_MESSAGE
    assert resp.sources == []
    assert llm.calls == []


def test_redirects_when_no_chunks():
    resp = answer("anything", page="/demo", llm=StubLLM("x"), retriever=StubRetriever([]))
    assert resp.redirected is True
    assert resp.answer == REDIRECT_MESSAGE


def test_llm_flags_off_topic_even_when_retrieval_clears_threshold():
    # "write a poem about a CSM" retrieves an on-topic-ish chunk above threshold,
    # so the retrieval gate does NOT fire - the LLM is the one that detects the
    # off-topic request and flags it via off_topic. That signal must surface as
    # redirected=True with no cited sources (matching the retrieval-gate path).
    chunks = [Chunk("[Overview] Sentio scores account health.", "product-overview.md", 0.51)]
    payload = json.dumps({"answer": REDIRECT_MESSAGE, "question": None, "off_topic": True})
    llm = StubLLM(payload)
    resp = answer("write me a funny poem about a CSM surviving Monday",
                  page="/pricing", llm=llm, retriever=StubRetriever(chunks))
    assert resp.redirected is True
    assert resp.sources == []
    assert llm.calls != []  # gate did not fire; the LLM was consulted


def test_retrieval_query_is_anchored_to_prior_assistant_turn():
    # A short follow-up answering Sage's own question carries no Sentio keywords, so
    # retrieving on it alone scores as off-topic. The query must be anchored to the
    # last assistant turn so the follow-up is retrieved in the context it belongs to.
    chunks = [Chunk("[Pricing] Growth multi-year discounts.", "pricing-tiers.md", 0.80)]
    retriever = StubRetriever(chunks)
    history = [
        {"role": "user", "content": "Is there a discount for the Growth plan?"},
        {"role": "assistant", "content": "Multi-year discounts are available on Growth."},
    ]
    answer("I want to roll out as soon as possible", page="/pricing",
           llm=StubLLM(json.dumps({"answer": "Great.", "question": None})),
           retriever=retriever, history=history)
    query = retriever.queries[0].lower()
    assert "discount" in query        # anchored to the prior assistant turn
    assert "roll out" in query        # and includes the current message


def test_llm_receives_conversation_history():
    chunks = [Chunk("[Pricing] Growth multi-year discounts.", "pricing-tiers.md", 0.80)]
    llm = StubLLM(json.dumps({"answer": "Great.", "question": None}))
    history = [
        {"role": "user", "content": "Is there a discount for the Growth plan?"},
        {"role": "assistant", "content": "Multi-year discounts are available on Growth."},
    ]
    answer("as soon as possible", page="/pricing", llm=llm,
           retriever=StubRetriever(chunks), history=history)
    _system, user = llm.calls[0]
    assert "discount for the Growth plan" in user   # prior turn visible to the model
    assert "as soon as possible" in user            # current message present


def test_no_history_keeps_query_and_user_as_bare_message():
    # Backward compat: with no history the retrieval query and user turn are just the
    # message, exactly as before the context change.
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91)]
    retriever = StubRetriever(chunks)
    llm = StubLLM(json.dumps({"answer": "Growth is $36k/year.", "question": None}))
    answer("how much is growth?", page="/pricing", llm=llm, retriever=retriever)
    assert retriever.queries[0] == "how much is growth?"
    assert llm.calls[0][1] == "how much is growth?"


def test_off_topic_absent_stays_not_redirected():
    # Backward compat: payloads without off_topic behave as before (answered turn).
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91)]
    payload = json.dumps({"answer": "Growth is $36k/year.", "question": None})
    resp = answer("price?", page="/pricing", llm=StubLLM(payload),
                  retriever=StubRetriever(chunks))
    assert resp.redirected is False
    assert resp.sources == ["pricing-tiers.md"]
