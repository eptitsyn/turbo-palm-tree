# app/workers/tasks/review_tasks.py
from __future__ import annotations

from typing import Any

from app.crew.crew_factory import run_file_diff_review
from app.crew.gitlab_notes import post_progress_note
from app.crew.tools.gitlab_tool import (
    fetch_merge_request_changes,
    fetch_merge_request_details,
)
from app.db.session import init_db
from app.services.review_store import record_review_run
from app.workers.celery_app import celery_app


def _guess_language(path: str | None) -> str:
    if not path:
        return "unknown"
    lower = path.lower()
    if lower.endswith(".py"):
        return "python"
    if lower.endswith(".js") or lower.endswith(".jsx"):
        return "javascript"
    if lower.endswith(".ts") or lower.endswith(".tsx"):
        return "typescript"
    if lower.endswith(".rs"):
        return "rust"
    if lower.endswith(".go"):
        return "go"
    if lower.endswith(".java"):
        return "java"
    if lower.endswith(".kt"):
        return "kotlin"
    if lower.endswith(".rb"):
        return "ruby"
    if lower.endswith(".php"):
        return "php"
    if lower.endswith(".cs"):
        return "csharp"
    if lower.endswith(".cpp") or lower.endswith(".cc") or lower.endswith(".cxx"):
        return "cpp"
    if lower.endswith(".c"):
        return "c"
    if lower.endswith(".md"):
        return "markdown"
    return "unknown"


def _build_diff_context(
    change: dict[str, Any],
    project_id: int,
    mr_iid: int,
    project_path: str | None = None,
) -> dict[str, Any]:
    file_path = change.get("new_path") or change.get("old_path") or change.get("file_path") or ""
    return {
        "file_path": file_path,
        "language": _guess_language(file_path),
        "diff": change.get("diff", ""),
        "old_code": change.get("old_path_content", "") if change.get("old_path_content") else "",
        "new_code": change.get("new_path_content", "") if change.get("new_path_content") else "",
        "project_id": project_id,
        "mr_iid": mr_iid,
        "project_path": project_path,
    }


@celery_app.task(name="review_merge_request")
def review_merge_request(
    project_id: int,
    mr_iid: int,
    last_commit_sha: str | None,
    progress_note_id: str | int | None = None,
):
    """
    Реализация Celery-задачи для MR: тянет diff из GitLab и гоняет crew по каждому файлу.
    """
    # Ensure tables exist in worker context (dev-friendly; prefer Alembic in prod)
    init_db()

    # Update queued note to show active analysis
    post_progress_note(project_id=project_id, mr_iid=mr_iid, note_id=progress_note_id)

    project_path: str | None = None
    details_resp = fetch_merge_request_details(project_id=project_id, mr_iid=mr_iid)
    if details_resp.get("status") == "ok":
        mr_data = details_resp.get("mr") or {}
        references = mr_data.get("references") or {}
        full_ref = references.get("full") or ""
        if "!" in full_ref:
            project_path = full_ref.split("!", 1)[0]
        if not project_path:
            web_url = mr_data.get("web_url") or ""
            if "/-/" in web_url:
                try:
                    project_path = web_url.split("//", 1)[1].split("/-/", 1)[0].split("/", 1)[1]
                except Exception:
                    project_path = None

    changes_resp = fetch_merge_request_changes(project_id=project_id, mr_iid=mr_iid)
    if changes_resp.get("status") != "ok":
        result = {
            "status": "error",
            "project_id": project_id,
            "mr_iid": mr_iid,
            "last_commit_sha": last_commit_sha,
            "error": changes_resp,
        }
        record_review_run(
            project_id=project_id,
            mr_iid=mr_iid,
            last_commit_sha=last_commit_sha,
            project_path=project_path,
            status="error",
            findings=None,
        )
        return result

    diff_context = {
        "project_id": project_id,
        "mr_iid": mr_iid,
        "project_path": project_path,
        "last_commit_sha": last_commit_sha,
        "changes": changes_resp.get("changes", []),
        "progress_note_id": progress_note_id,
    }
    findings = run_file_diff_review(diff_context)

    result = {
        "status": "ok",
        "project_id": project_id,
        "mr_iid": mr_iid,
        "last_commit_sha": last_commit_sha,
        "files_reviewed": len(changes_resp.get("changes", [])),
        "results": findings,
    }
    record_review_run(
        project_id=project_id,
        mr_iid=mr_iid,
        last_commit_sha=last_commit_sha,
        project_path=project_path,
        status="ok",
        findings=findings,
    )
    return result
