# app/config.py
from functools import lru_cache
from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # FastAPI
    APP_ENV: str = "dev"
    CORS_ALLOW_ORIGINS: list[str] = ["*"]

    # DB
    POSTGRES_USER: str = "postgres"
    # Defaults below are for local smoke tests only; override in real deployments.
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_code_review"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # GitLab
    GITLAB_BASE_URL: str = "https://gitlab.example.com"
    GITLAB_TOKEN: str = "dev-token"
    GITLAB_WEBHOOK_SECRET: str = "dev-secret"

    # LLM
    LLM_MODEL_NAME: str = "local-llm"
    LLM_API_BASE: str = "http://localhost:8001"
    LLM_API_KEY: str = "dev-llm-key"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # mypy is fine with this now; no ignore needed
    return Settings()


settings = get_settings()
