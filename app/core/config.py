from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Production AI Research Agent"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    llm_provider: Literal["mock", "openai", "google"] = "mock"
    llm_model: str = "gpt-5.4-mini"

    openai_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None

    max_research_steps: int = 5
    max_iterations: int = 2

    tavily_api_key: SecretStr | None = None

    max_search_results: int = 4
    max_sources: int = 12
    search_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
