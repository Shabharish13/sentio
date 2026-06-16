import json

from app.agents.research import ResearchBrief, run_research


class StubLLM:
    """Returns canned responses in order; records the prompts it received."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def complete(self, system, user, max_tokens=1024):
        self.calls.append((system, user))
        return self._responses.pop(0)


class StubTavily:
    def __init__(self):
        self.queries = []

    def search(self, query, **kwargs):
        self.queries.append(query)
        return {"results": [{"url": "https://example.com/x", "title": "x"}]}


def test_tavily_budget_exhausted_degrades_gracefully():
    from app.clients.tavily_client import TavilyBudgetError

    class BudgetExhaustedTavily:
        def search(self, query, **kwargs):
            raise TavilyBudgetError("exhausted")

    llm = StubLLM([
        json.dumps({"action": "search", "query": "q"}),
        json.dumps({"action": "final", "top_signal": None, "signal_type": "none"}),
    ])
    # Budget error must be swallowed (empty results) and the loop reach a final brief.
    brief = run_research({}, llm=llm, tavily=BudgetExhaustedTavily())
    assert brief.signal_type == "none"


def test_tavily_http_error_degrades_gracefully():
    import httpx

    class FlakyTavily:
        def search(self, query, **kwargs):
            raise httpx.ConnectError("network down")

    llm = StubLLM([
        json.dumps({"action": "search", "query": "q"}),
        json.dumps({"action": "final", "top_signal": None, "signal_type": "none"}),
    ])
    brief = run_research({}, llm=llm, tavily=FlakyTavily())
    assert brief.signal_type == "none"


def test_returns_final_brief_without_search():
    llm = StubLLM([json.dumps({
        "action": "final",
        "top_signal": "Raised a $30M Series B in March 2026",
        "signal_type": "funding",
        "source_url": "https://news.example.com/series-b",
    })])
    tavily = StubTavily()
    brief = run_research({"company": {"name": "Meridian"}}, llm=llm, tavily=tavily)
    assert isinstance(brief, ResearchBrief)
    assert brief.signal_type == "funding"
    assert brief.top_signal.startswith("Raised")
    assert tavily.queries == []


def test_runs_search_then_final():
    llm = StubLLM([
        json.dumps({"action": "search", "query": "Meridian VP customer success hire"}),
        json.dumps({"action": "final", "top_signal": "Hired a VP of CS in May 2026",
                    "signal_type": "exec_hire", "source_url": "https://li.example/x"}),
    ])
    tavily = StubTavily()
    brief = run_research({"company": {"name": "Meridian"}}, llm=llm, tavily=tavily)
    assert tavily.queries == ["Meridian VP customer success hire"]
    assert brief.signal_type == "exec_hire"


def test_invalid_signal_type_coerced_to_none():
    llm = StubLLM([json.dumps({"action": "final", "top_signal": "x", "signal_type": "bogus"})])
    brief = run_research({}, llm=llm, tavily=StubTavily())
    assert brief.signal_type == "none"


def test_unparseable_response_returns_none_brief():
    llm = StubLLM(["this is not json at all"])
    brief = run_research({}, llm=llm, tavily=StubTavily())
    assert brief.signal_type == "none"
    assert brief.top_signal is None


def test_search_cap_forces_final():
    llm = StubLLM([json.dumps({"action": "search", "query": "q"})] * 5)
    tavily = StubTavily()
    brief = run_research({}, llm=llm, tavily=tavily, max_searches=3)
    assert len(tavily.queries) == 3
    assert brief.signal_type == "none"


def test_json_extracted_from_prose_wrapped_response():
    # LLM prose contains an earlier brace before the real JSON object.
    noisy = 'Based on {the record}, here is my answer: {"action": "final", "top_signal": "Raised Series B", "signal_type": "funding", "source_url": "https://x"} hope that helps!'
    llm = StubLLM([noisy])
    brief = run_research({}, llm=llm, tavily=StubTavily())
    assert brief.signal_type == "funding"
    assert brief.top_signal == "Raised Series B"
