# app/db/session.py
import os
from pathlib import Path
from typing import Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


def _resolve_database_url() -> Tuple[str, dict[str, object]]:
    """
    Pick a DSN based on environment:
    - DATABASE_URL (or settings.DATABASE_URL) wins
    - TESTING=1 → in-memory SQLite
    - Fallback → Postgres DSN from settings
    """
    testing = os.getenv("TESTING") == "1"
    env_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL

    if env_url:
        url = env_url
    elif testing:
        url = "sqlite+pysqlite:///:memory:"
    else:
        url = (
            f"postgresql+psycopg2://{settings.POSTGRES_USER}:"
            f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
            f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )

    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # Ensure the directory exists for file-based SQLite
        if ":///" in url and ":memory:" not in url:
            db_path = url.split(":///", 1)[1]
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    return url, connect_args


DATABASE_URL, connect_args = _resolve_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Import models and create tables (for dev/test); prefer Alembic in prod."""
    from app.db.base import Base  # noqa: WPS433
    from app import models  # noqa: F401, WPS433

    Base.metadata.create_all(bind=engine)
