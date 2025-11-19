# app/config.py
from functools import lru_cache

from pydantic import AnyHttpUrl, BaseSettings


class Settings(BaseSettings):
    # FastAPI
    APP_ENV: str = "dev"
    CORS_ALLOW_ORIGINS: list[AnyHttpUrl] | list[str] = ["*"]

    # DB
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_code_review"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # GitLab
    GITLAB_BASE_URL: str = "https://gitlab.example.com"
    GITLAB_TOKEN: str = "CHANGE_ME"
    GITLAB_WEBHOOK_SECRET: str = "CHANGE_ME"

    # LLM / crewAI
    LLM_MODEL_NAME: str = "local-llm"
    LLM_API_BASE: str = "http://localhost:8001"  # e.g. vLLM / TGI
    LLM_API_KEY: str = "dummy"  # for OpenAI-compatible interfaces

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
