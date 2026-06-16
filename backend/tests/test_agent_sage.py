import json

from app.agents.sage import REDIRECT_MESSAGE, SageResponse, answer
from app.rag.store import Chunk


class StubLLM:
    def __init__(self, reply):
        self._reply = reply
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._reply


class StubRetriever:
    def __init__(self, chunks):
        self._chunks = chunks

    def retrieve(self, query, k=4):
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
    assert resp.question == "Are you evaluating for your own team, or a broader group?"
    assert resp.sources == ["pricing-tiers.md", "pricing-tiers.md"]
    system, _user = llm.calls[0]
    assert "Growth is $36k/yr." in system
    assert "/pricing" in system


def test_terminal_turn_has_null_question():
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91)]
    payload = json.dumps({"answer": "Sounds like a fit - what's your work email?",
                          "question": None})
    resp = answer("ready to go", page="/pricing", llm=StubLLM(payload),
                  retriever=StubRetriever(chunks))
    assert resp.question is None
    assert "work email" in resp.answer


def test_non_json_reply_falls_back_to_raw_text():
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91)]
    resp = answer("how much?", page="/pricing",
                  llm=StubLLM("Growth is $36k/year."), retriever=StubRetriever(chunks))
    assert resp.redirected is False
    assert "36k" in resp.answer
    assert resp.question is None


def test_redirects_when_top_score_below_threshold():
    chunks = [Chunk("vaguely related", "faq-objections.md", 0.20)]
    llm = StubLLM("should not be called")
    resp = answer("do you integrate with SAP S/4HANA?", page="/pricing",
                  llm=llm, retriever=StubRetriever(chunks))
    assert resp.redirected is True
    assert resp.answer == REDIRECT_MESSAGE
    assert resp.question is None
    assert resp.sources == []
    assert llm.calls == []


def test_redirects_when_no_chunks():
    resp = answer("anything", page="/demo", llm=StubLLM("x"), retriever=StubRetriever([]))
    assert resp.redirected is True
    assert resp.answer == REDIRECT_MESSAGE
