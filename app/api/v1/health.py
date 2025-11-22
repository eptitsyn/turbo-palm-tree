# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: Session = Depends(get_db)):
    # Check DB connectivity (simple heartbeat)
    db.execute(text("SELECT 1"))
    return {"status": "ready"}
