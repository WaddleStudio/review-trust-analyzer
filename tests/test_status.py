import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch, MagicMock
from app.main import app
from app.database import get_session

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def get_test_session():
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    app.dependency_overrides[get_session] = get_test_session
    yield
    SQLModel.metadata.drop_all(engine)
    app.dependency_overrides.pop(get_session, None)


client = TestClient(app)


def test_status_returns_expected_fields():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "qwen3:14b"}]}

    with patch("httpx.get", return_value=mock_resp):
        response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["server"] == "ok"
    assert data["ollama"] == "ok"
    assert data["ollama_model"] == "qwen3:14b"
    assert "labeling_pending" in data
    assert "serpapi_credits" in data


def test_status_ollama_unavailable():
    with patch("httpx.get", side_effect=Exception("connection refused")):
        response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["server"] == "ok"
    assert data["ollama"] == "unavailable"
