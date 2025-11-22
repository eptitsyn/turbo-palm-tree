# app/schemas/review.py
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ReviewRunRead(BaseModel):
    id: int
    project_id: str
    mr_iid: str
    last_commit_sha: str | None
    project_path: str | None
    status: str
    summary: str | None
    findings: list[dict[str, Any]] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
