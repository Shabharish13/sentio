import pytest


@pytest.fixture(autouse=True)
def _dummy_env(monkeypatch):
    """Unit tests must never read real keys or hit the network."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic")
    monkeypatch.setenv("APOLLO_API_KEY", "test-apollo")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily")
    monkeypatch.setenv("HUBSPOT_TOKEN", "test-hubspot")
    # get_settings() is lru_cached — clear it so each test sees fresh env
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
