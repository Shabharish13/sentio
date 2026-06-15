from app.clients.anthropic_client import AnthropicClient
from app.clients.cli_backend import ClaudeCliBackend
from app.clients.llm import LLM, get_llm
from app.config import get_settings


def test_get_llm_uses_sdk_when_key_present(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-present")
    get_settings.cache_clear()
    llm = get_llm()
    assert isinstance(llm._backend, AnthropicClient)


def test_get_llm_uses_cli_when_key_absent(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    llm = get_llm()
    assert isinstance(llm._backend, ClaudeCliBackend)


def test_llm_delegates_to_backend():
    class StubBackend:
        def complete(self, system, user, max_tokens=1024):
            return f"{system}|{user}|{max_tokens}"

    llm = LLM(StubBackend())
    assert llm.complete("S", "U", 50) == "S|U|50"
