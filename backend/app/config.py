from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / "api-tests" / ".env"
PROMPTS_DIR = REPO_ROOT / "prompts"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    apollo_api_key: str = ""
    tavily_api_key: str = ""
    hubspot_token: str = ""

    hubspot_pipeline_id: str = "default"
    hubspot_stage_demo_requested: str = "3832955632"
    hubspot_stage_disqualified: str = "3840698071"

    openai_model: str = "gpt-5"
    claude_model: str = "claude-sonnet-4-6"


@lru_cache
def get_settings() -> Settings:
    return Settings()
