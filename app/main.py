# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import gitlab_webhooks, health
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Code Review",
        version="0.1.0",
    )

    # CORS - can be tightened / disabled in private contour
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(gitlab_webhooks.router, prefix="/api/v1")

    return app


app = create_app()
