import os

os.environ["DATABASE_URL"] = "sqlite:///./test_ai_jira.db"
os.environ["APP_ENV"] = "development"

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.database.session import Base, engine


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
