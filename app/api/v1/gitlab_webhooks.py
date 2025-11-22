# app/api/v1/gitlab_webhooks.py
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.workers.tasks.review_task import review_merge_request


router = APIRouter(prefix="/gitlab", tags=["gitlab"])


@router.post("/webhook")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    # simple token check (you can do HMAC signatures if needed)
    if x_gitlab_token != settings.GITLAB_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    payload = await request.json()
    object_kind = payload.get("object_kind")

    # MVP: handle only merge_request events
    if object_kind == "merge_request":
        project = payload["project"]
        mr = payload["object_attributes"]

        project_id = project["id"]
        mr_iid = mr["iid"]
        last_commit_sha = mr.get("last_commit", {}).get("id") or mr.get("last_commit_id")

        # TODO: insert Project / MergeRequest / ReviewRequest into DB here
        # For now, call Celery with minimal info
        review_merge_request.delay(
            project_id=project_id,
            mr_iid=mr_iid,
            last_commit_sha=last_commit_sha,
        )
        return {"status": "queued", "project_id": project_id, "mr_iid": mr_iid}

    # ignore other events for now
    return {"status": "ignored", "kind": object_kind}
