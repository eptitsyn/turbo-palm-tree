# app/workers/celery_app.py
from celery import Celery

from app.config import settings


celery_app = Celery(
    "ai_code_review",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Optional: namespace config from env, etc.
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
