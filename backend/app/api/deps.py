from __future__ import annotations

from functools import lru_cache

from app.chat.session import get_store
from app.clients.apollo_client import ApolloClient
from app.clients.hubspot_client import HubSpotClient
from app.clients.llm import get_llm
from app.clients.tavily_client import TavilyClient
from app.rag.store import get_retriever

"""Dependency providers for the API layer.

Each is a thin factory so tests can override them via app.dependency_overrides
with stubs — no network, no LLM, no real CRM writes in the unit suite.
"""


def provide_llm():
    return get_llm()


@lru_cache
def provide_retriever():
    # Loading the Chroma index is expensive; reuse one retriever per process.
    return get_retriever()


def provide_apollo():
    return ApolloClient()


def provide_tavily():
    return TavilyClient(max_calls=3)


def provide_hubspot():
    return HubSpotClient()


def provide_store():
    return get_store()
