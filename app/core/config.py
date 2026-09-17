from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
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

    verification_min_coverage: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
    )

    max_targeted_queries: int = Field(
        default=3,
        ge=1,
        le=5,
    )

    max_tool_calls: int = Field(
        default=15,
        ge=1,
    )

    graph_recursion_limit: int = Field(
        default=25,
        ge=5,
    )

    postgres_uri: str = (
        "postgresql://research:research@localhost:5433/research_agent?sslmode=disable"
    )

    redis_url: str = "redis://localhost:6380/0"

    redis_cache_ttl_seconds: int = 900

    langfuse_enabled: bool = False
    langfuse_public_key: SecretStr | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"
    langfuse_tracing_environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
