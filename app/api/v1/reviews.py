# app/api/v1/reviews.py
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.review import ReviewRun
from app.schemas.review import ReviewRunRead

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewRunRead])
def list_reviews(db: Session = Depends(get_db)):
    stmt = (
        select(ReviewRun)
        .order_by(ReviewRun.created_at.desc())
        .limit(100)  # avoid unbounded responses
    )
    results = db.execute(stmt).scalars().all()
    return results
