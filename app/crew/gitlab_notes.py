# app/crew/gitlab_notes.py
from __future__ import annotations

import os
from typing import Any

from app.crew.tools.gitlab_tool import (
    post_merge_request_comment,
    update_merge_request_comment,
)

# Flags control whether GitLab comments are posted during review runs.
POST_GITLAB_NOTE = os.getenv("CREW_POST_GITLAB_NOTE", "true").lower() == "true"
POST_GITLAB_PROGRESS_NOTE = os.getenv(
    "CREW_POST_GITLAB_PROGRESS_NOTE", "true"
).lower() == "true"


def _summary_lines(
    findings: list[dict[str, Any]], heading: str, limit: int = 5
) -> list[str]:
    top = findings[:limit]
    lines = [heading]
    for item in top:
        sev = item.get("severity", "info")
        summary = (item.get("summary") or "").strip() or "<no summary>"
        lines.append(f"- [{sev}] {summary}")
    if len(findings) > len(top):
        lines.append(f"...и ещё {len(findings) - len(top)}.")
    return lines


def post_findings_note(
    project_id: Any,
    mr_iid: Any,
    findings: list[dict[str, Any]],
    *,
    note_id: Any = None,
) -> dict[str, Any] | None:
    """Post or update a summary MR note with findings."""
    if not POST_GITLAB_NOTE or not project_id or not mr_iid:
        return None

    body = "\n".join(_summary_lines(findings, "Итоги ревью (кратко):"))
    if note_id:
        return update_merge_request_comment(
            project_id=project_id,
            mr_iid=mr_iid,
            note_id=note_id,
            body=body,
        )
    return post_merge_request_comment(project_id=project_id, mr_iid=mr_iid, body=body)


def post_progress_note(project_id: Any, mr_iid: Any) -> dict[str, Any] | None:
    """Create a 'review started' note."""
    if not POST_GITLAB_PROGRESS_NOTE or not project_id or not mr_iid:
        return None

    body = "🤖 Ревью запущено… агенты анализируют изменения."
    return post_merge_request_comment(project_id=project_id, mr_iid=mr_iid, body=body)


def update_progress_note(
    project_id: Any,
    mr_iid: Any,
    note_id: Any,
    findings: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Update the initial progress note with final findings."""
    if not POST_GITLAB_PROGRESS_NOTE or not project_id or not mr_iid or not note_id:
        return None

    body = "\n".join(_summary_lines(findings, "🤖 Ревью завершено. Находки:"))
    return update_merge_request_comment(
        project_id=project_id,
        mr_iid=mr_iid,
        note_id=note_id,
        body=body,
    )
