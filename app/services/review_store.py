# app/services/review_store.py
from __future__ import annotations

from typing import Any, Iterable

from loguru import logger
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.review import ReviewRun


def _safe_summary(findings: Iterable[dict[str, Any]] | None) -> str | None:
    if not findings:
        return None
    for item in findings:
        summary = (item or {}).get("summary")
        if summary:
            return str(summary)[:512]
    return None


def record_review_run(
    *,
    project_id: Any,
    mr_iid: Any,
    last_commit_sha: str | None,
    project_path: str | None,
    status: str,
    findings: list[dict[str, Any]] | None,
) -> ReviewRun | None:
    """
    Persist a review run; failures are logged but do not crash the caller.
    """
    try:
        with SessionLocal() as db:
            run = ReviewRun(
                project_id=str(project_id),
                mr_iid=str(mr_iid),
                last_commit_sha=last_commit_sha,
                project_path=project_path,
                status=status,
                findings=findings,
                summary=_safe_summary(findings),
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            return run
    except SQLAlchemyError as exc:  # pragma: no cover - defensive logging
        logger.warning("Could not persist review run: {}", exc)
    return None
