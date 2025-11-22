# app/db/base.py
from sqlalchemy.orm import declarative_base


Base = declarative_base()

# Import models so metadata is populated for migrations/create_all
from app.models.review import ReviewRun  # noqa: F401,E402
