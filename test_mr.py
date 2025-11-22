"""Эмуляция входящего GitLab webhook и запуск пайплайна агентов.

Обходит HTTP и вызывает задачу Celery (по умолчанию inline) с константными данными MR.
Запуск: `uv run python test_mr.py` или `python test_mr.py`
"""

from __future__ import annotations

import os

from app.workers.tasks.review_task import review_merge_request

# --- Настрой при необходимости ---
# Используй реальный проект/MR, чтобы отправилась заметка в GitLab.
PROJECT_ID = os.getenv("TEST_PROJECT_ID", "tst_grp/test")
MR_IID = int(os.getenv("TEST_MR_IID", "1"))
LAST_COMMIT_SHA = os.getenv(
    "TEST_LAST_COMMIT_SHA", "e1c5440402c152455be2323d2937c2bb06150c8f"
)
RUN_INLINE = os.getenv("RUN_INLINE", "true").lower() == "true"


def main() -> None:
    print("Launching review task...")
    print(f"project_id={PROJECT_ID}, mr_iid={MR_IID}, last_commit_sha={LAST_COMMIT_SHA}")

    if RUN_INLINE:
        result = review_merge_request(
            project_id=PROJECT_ID, mr_iid=MR_IID, last_commit_sha=LAST_COMMIT_SHA
        )
        print("\nРезультат inline:")
        print(result)
    else:
        async_result = review_merge_request.delay(
            project_id=PROJECT_ID, mr_iid=MR_IID, last_commit_sha=LAST_COMMIT_SHA
        )
        print("\nОтправлена задача Celery.")
        print(f"task_id={async_result.id}")
        print("Проверь результаты Celery, чтобы увидеть находки.")


if __name__ == "__main__":
    main()
