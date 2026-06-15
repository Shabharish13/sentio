from app.config import get_settings, REPO_ROOT, ENV_FILE, PROMPTS_DIR


def test_settings_read_env(monkeypatch):
    monkeypatch.setenv("HUBSPOT_TOKEN", "pat-xyz")
    get_settings.cache_clear()
    s = get_settings()
    assert s.hubspot_token == "pat-xyz"
    assert s.claude_model == "claude-sonnet-4-6"
    assert s.hubspot_pipeline_id == "default"
    assert s.hubspot_stage_demo_requested == "3832955632"
    assert s.hubspot_stage_disqualified == "3840698071"


def test_path_constants_point_at_repo():
    assert (REPO_ROOT / "prompts").exists()
    assert ENV_FILE.name == ".env"
    assert PROMPTS_DIR.name == "prompts"
