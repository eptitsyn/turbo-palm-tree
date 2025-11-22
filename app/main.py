# app/main.py
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.api.v1 import gitlab_webhooks, health, reviews
from app.db.session import init_db


def create_app() -> FastAPI:
    if settings.LOG_TO_CONSOLE:
        logger.remove()
        logger.add(sys.stderr, level=settings.LOG_LEVEL.upper(), enqueue=True)

    app = FastAPI(
        title="AI Code Review",
        version="0.1.0",
    )

    # Now mypy knows it's list[str]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include versioned API routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(gitlab_webhooks.router, prefix="/api/v1")
    app.include_router(reviews.router, prefix="/api/v1")

    @app.on_event("startup")
    def _startup() -> None:
        # Dev-friendly: ensure tables exist; prefer Alembic migrations in prod.
        init_db()

    return app


app = create_app()
