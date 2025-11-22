"""Отправить тестовую заметку в GitLab MR и прочитать заметки через API.

Настройка через переменные окружения:
- GITLAB_BASE_URL (например, http://localhost)
- GITLAB_TOKEN (private token с api scope)
- TEST_PROJECT_ID (например, "tst_grp/test" или числовой ID)
- TEST_MR_IID (по умолчанию: 1)
"""

from __future__ import annotations

import os
from datetime import datetime
from pprint import pprint

from app.crew.tools.gitlab_tool import (
    fetch_merge_request_notes,
    post_merge_request_comment,
)

BASE_URL = os.getenv("GITLAB_BASE_URL", "http://localhost")
TOKEN = os.getenv("GITLAB_TOKEN", "")
PROJECT_ID = os.getenv("TEST_PROJECT_ID", "tst_grp/test")
MR_IID = int(os.getenv("TEST_MR_IID", "1"))


def main() -> None:
    timestamp = datetime.utcnow().isoformat()
    body = f"[автотест] привет из test_gitlab_note.py в {timestamp}"

    print(f"Отправляем заметку project={PROJECT_ID}, mr={MR_IID}")
    post_result = post_merge_request_comment(
        project_id=PROJECT_ID,
        mr_iid=MR_IID,
        body=body,
        base_url=BASE_URL,
        token=TOKEN,
    )
    print("Результат отправки:")
    pprint(post_result)

    print("\nЧитаем заметки...")
    notes_result = fetch_merge_request_notes(
        project_id=PROJECT_ID,
        mr_iid=MR_IID,
        base_url=BASE_URL,
        token=TOKEN,
    )
    print("Результат чтения:")
    pprint(notes_result)


if __name__ == "__main__":
    main()
