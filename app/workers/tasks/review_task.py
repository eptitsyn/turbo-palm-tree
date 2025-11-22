# app/workers/tasks/review_tasks.py
from __future__ import annotations

from typing import Any

from app.crew.crew_factory import run_file_diff_review
from app.crew.tools.gitlab_tool import fetch_merge_request_changes
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
    change: dict[str, Any], project_id: int, mr_iid: int
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
    }


@celery_app.task(name="review_merge_request")
def review_merge_request(project_id: int, mr_iid: int, last_commit_sha: str | None):
    """
    Реализация Celery‑задачи для MR: тянет diff из GitLab и гоняет crew по каждому файлу.
    """
    changes_resp = fetch_merge_request_changes(project_id=project_id, mr_iid=mr_iid)
    if changes_resp.get("status") != "ok":
        return {
            "status": "error",
            "project_id": project_id,
            "mr_iid": mr_iid,
            "last_commit_sha": last_commit_sha,
            "error": changes_resp,
        }

    findings_by_file: list[dict[str, Any]] = []
    for change in changes_resp.get("changes", []):
        diff_ctx = _build_diff_context(change, project_id=project_id, mr_iid=mr_iid)
        findings = run_file_diff_review(diff_ctx)
        findings_by_file.append(
            {
                "file_path": diff_ctx.get("file_path", ""),
                "language": diff_ctx.get("language", "unknown"),
                "findings": findings,
            }
        )

    return {
        "status": "ok",
        "project_id": project_id,
        "mr_iid": mr_iid,
        "last_commit_sha": last_commit_sha,
        "files_reviewed": len(findings_by_file),
        "results": findings_by_file,
    }
