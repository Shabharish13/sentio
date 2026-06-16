from app.agents.sage import ESCALATION_MESSAGE, SageResponse, answer
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


def test_grounded_answer_when_confident():
    chunks = [Chunk("[Pricing] Growth is $36k/yr.", "pricing-tiers.md", 0.91),
              Chunk("[Pricing] Starter is $18k/yr.", "pricing-tiers.md", 0.82)]
    llm = StubLLM("Growth is $36k/year. Are you evaluating for your own team, or a broader group?")
    resp = answer("how much is growth?", page="/pricing", llm=llm, retriever=StubRetriever(chunks))
    assert isinstance(resp, SageResponse)
    assert resp.escalated is False
    assert "36k" in resp.reply
    assert resp.sources == ["pricing-tiers.md", "pricing-tiers.md"]
    system, _user = llm.calls[0]
    assert "Growth is $36k/yr." in system
    assert "/pricing" in system


def test_escalates_when_top_score_below_threshold():
    chunks = [Chunk("vaguely related", "faq-objections.md", 0.20)]
    llm = StubLLM("should not be called")
    resp = answer("do you integrate with SAP S/4HANA?", page="/pricing",
                  llm=llm, retriever=StubRetriever(chunks))
    assert resp.escalated is True
    assert resp.reply == ESCALATION_MESSAGE
    assert resp.sources == []
    assert llm.calls == []


def test_escalates_when_no_chunks():
    resp = answer("anything", page="/demo", llm=StubLLM("x"), retriever=StubRetriever([]))
    assert resp.escalated is True
    assert resp.reply == ESCALATION_MESSAGE
