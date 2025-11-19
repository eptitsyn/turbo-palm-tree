# app/db/session.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Decide which DB to use
connect_args: dict[str, object]

if os.getenv("TESTING") == "1":
    # Use lightweight SQLite for tests, no psycopg2 import
    DATABASE_URL = "sqlite+pysqlite:///:memory:"
    connect_args = {"check_same_thread": False}
else:
    # Use Postgres in normal mode
    DATABASE_URL = (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
        f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    connect_args = {}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
