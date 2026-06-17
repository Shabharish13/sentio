import pytest

from app.clients.anthropic_client import AnthropicClient
from app.clients.cli_backend import ClaudeCliBackend, LLMError
from app.clients.llm import LLM, get_llm
from app.clients.openai_backend import OpenAIBackend
from app.config import get_settings


def test_get_llm_precedence_openai_first(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
    get_settings.cache_clear()
    backends = get_llm()._backends
    assert isinstance(backends[0], OpenAIBackend)
    assert isinstance(backends[1], AnthropicClient)
    assert isinstance(backends[-1], ClaudeCliBackend)


def test_get_llm_anthropic_then_cli_when_no_openai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
    get_settings.cache_clear()
    backends = get_llm()._backends
    assert isinstance(backends[0], AnthropicClient)
    assert isinstance(backends[-1], ClaudeCliBackend)
    assert not any(isinstance(b, OpenAIBackend) for b in backends)


def test_get_llm_cli_only_when_no_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    backends = get_llm()._backends
    assert len(backends) == 1
    assert isinstance(backends[0], ClaudeCliBackend)


def test_chain_falls_through_on_error():
    class Failing:
        def complete(self, system, user, max_tokens=1024):
            raise LLMError("boom")

    class Working:
        def complete(self, system, user, max_tokens=1024):
            return "ok"

    assert LLM([Failing(), Working()]).complete("s", "u") == "ok"


def test_chain_raises_when_all_fail():
    class Failing:
        def complete(self, system, user, max_tokens=1024):
            raise LLMError("boom")

    with pytest.raises(LLMError):
        LLM([Failing(), Failing()]).complete("s", "u")


def test_llm_delegates_first_backend():
    class StubBackend:
        def complete(self, system, user, max_tokens=1024):
            return f"{system}|{user}|{max_tokens}"

    assert LLM([StubBackend()]).complete("S", "U", 50) == "S|U|50"


def test_llm_forwards_reasoning_effort_to_backend():
    class StubBackend:
        def complete(self, system, user, max_tokens=1024, reasoning_effort=None):
            return f"{reasoning_effort}"

    assert LLM([StubBackend()]).complete("S", "U", reasoning_effort="minimal") == "minimal"
