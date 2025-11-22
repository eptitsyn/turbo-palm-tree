# app/crew/tools/gitlab_tool.py
from __future__ import annotations

from typing import Any

import requests
from urllib.parse import quote_plus

from app.config import settings


def _api_base(base_url: str | None) -> str:
    base = (base_url or settings.GITLAB_BASE_URL).rstrip("/")
    if base.endswith("/api/v4"):
        return base
    return f"{base}/api/v4"


def fetch_merge_request_changes(
    project_id: int | str,
    mr_iid: int | str,
    *,
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Забирает изменения merge request через GitLab REST API.
    Возвращает структурированный словарь со статусом и данными/ошибкой.
    """
    api_base = _api_base(base_url)
    api_token = token or settings.GITLAB_TOKEN
    url = (
        f"{api_base}/projects/{quote_plus(str(project_id))}"
        f"/merge_requests/{quote_plus(str(mr_iid))}/changes"
    )
    headers = {"Private-Token": api_token}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return {
                "status": "error",
                "error": f"GitLab API вернул {resp.status_code}",
                "body": resp.text,
                "url": url,
            }
        data = resp.json()
        return {
            "status": "ok",
            "project_id": project_id,
            "mr_iid": mr_iid,
            "changes": data.get("changes", []),
            "raw": data,
            "url": url,
        }
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc), "url": url}


def fetch_merge_request_details(
    project_id: int | str,
    mr_iid: int | str,
    *,
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Забирает детали MR (для получения пути репозитория и метаданных).
    """
    api_base = _api_base(base_url)
    api_token = token or settings.GITLAB_TOKEN
    url = (
        f"{api_base}/projects/{quote_plus(str(project_id))}"
        f"/merge_requests/{quote_plus(str(mr_iid))}"
    )
    headers = {"Private-Token": api_token}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return {
                "status": "error",
                "error": f"GitLab API вернул {resp.status_code}",
                "body": resp.text,
                "url": url,
            }
        data = resp.json()
        return {"status": "ok", "mr": data, "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc), "url": url}


def fetch_merge_request_notes(
    project_id: int | str,
    mr_iid: int | str,
    *,
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Получить заметки (комментарии) MR.
    """
    api_base = _api_base(base_url)
    api_token = token or settings.GITLAB_TOKEN
    url = (
        f"{api_base}/projects/{quote_plus(str(project_id))}"
        f"/merge_requests/{quote_plus(str(mr_iid))}/notes"
    )
    headers = {"Private-Token": api_token}

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            return {
                "status": "error",
                "error": f"GitLab API вернул {resp.status_code}",
                "body": resp.text,
                "url": url,
            }
        return {"status": "ok", "notes": resp.json(), "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc), "url": url}


def update_merge_request_comment(
    project_id: int | str,
    mr_iid: int | str,
    note_id: int | str,
    body: str,
    *,
    base_url: str | None = None,
    token: str | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """
    Обновить существующую заметку MR.
    """
    api_base = _api_base(base_url)
    api_token = token or settings.GITLAB_TOKEN
    url = (
        f"{api_base}/projects/{quote_plus(str(project_id))}"
        f"/merge_requests/{quote_plus(str(mr_iid))}"
        f"/notes/{quote_plus(str(note_id))}"
    )
    headers = {"Private-Token": api_token}
    payload = {"body": body}

    try:
        resp = requests.put(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code not in (200, 201):
            return {
                "status": "error",
                "error": f"GitLab API вернул {resp.status_code}",
                "body": resp.text,
                "url": url,
            }
        return {"status": "ok", "note": resp.json(), "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc), "url": url}


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
    Отправить обычную MR-заметку.
    Возвращает структурированный статус для агентов.
    """
    api_base = _api_base(base_url)
    api_token = token or settings.GITLAB_TOKEN
    url = (
        f"{api_base}/projects/{quote_plus(str(project_id))}"
        f"/merge_requests/{quote_plus(str(mr_iid))}/notes"
    )
    headers = {"Private-Token": api_token}
    payload = {"body": body}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code not in (200, 201):
            return {
                "status": "error",
                "error": f"GitLab API вернул {resp.status_code}",
                "body": resp.text,
                "url": url,
            }
        return {"status": "ok", "note": resp.json(), "url": url}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc), "url": url}
