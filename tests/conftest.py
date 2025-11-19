import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# -----------------------------------------------------------------------------
# Test database (in-memory SQLite for speed)
# -----------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def SessionTesting(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db(SessionTesting):
    """
    Provides a fresh database session per test.
    Rolls back changes after each test.
    """
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Dependency override: FastAPI uses test DB instead of real Postgres
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def override_get_db(db):
    def _get_db_override():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# FastAPI Test Client
# -----------------------------------------------------------------------------
@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
