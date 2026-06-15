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
