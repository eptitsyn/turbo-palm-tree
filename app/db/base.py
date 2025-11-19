# app/db/base.py
from sqlalchemy.orm import declarative_base


Base = declarative_base()

# later: import models here so Alembic can see them, e.g.
# from app.models.project import Project
