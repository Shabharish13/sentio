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
