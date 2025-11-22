# app/crew/tools/gitlab_tool.py
from __future__ import annotations

from typing import Any

import requests

from app.config import settings


def fetch_merge_request_changes(
    project_id: int | str,
    mr_iid: int | str,
    *,
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Fetches merge request changes from GitLab REST API.
    Returns a structured dict with status and data/error for agent consumption.
    """
    api_base = base_url or settings.GITLAB_BASE_URL
    api_token = token or settings.GITLAB_TOKEN
    url = f"{api_base}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/changes"
    headers = {"Private-Token": api_token}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return {
                "status": "error",
                "error": f"GitLab API returned {resp.status_code}",
                "body": resp.text,
            }
        data = resp.json()
        return {
            "status": "ok",
            "project_id": project_id,
            "mr_iid": mr_iid,
            "changes": data.get("changes", []),
            "raw": data,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


def post_merge_request_comment(
    project_id: int | str,
    mr_iid: int | str,
    body: str,
    *,
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Post a top-level merge request comment (note).
    Returns structured status for agent consumption.
    """
    api_base = base_url or settings.GITLAB_BASE_URL
    api_token = token or settings.GITLAB_TOKEN
    url = f"{api_base}/api/v4/projects/{project_id}/merge_requests/{mr_iid}/notes"
    headers = {"Private-Token": api_token}
    payload = {"body": body}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code not in (200, 201):
            return {
                "status": "error",
                "error": f"GitLab API returned {resp.status_code}",
                "body": resp.text,
            }
        return {"status": "ok", "note": resp.json()}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}
