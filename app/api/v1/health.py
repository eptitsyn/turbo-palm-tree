# app/api/v1/health.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    # later: check DB, Celery, LLM, etc.
    return {"status": "ready"}
