# app/api/v1/__init__.py
from . import gitlab_webhooks, health  # noqa

__all__ = ["health", "gitlab_webhooks"]
