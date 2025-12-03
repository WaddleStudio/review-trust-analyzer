from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import pytest
from app.main import app
from app.database import get_session

# Setup in-memory DB for testing
engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)

def create_test_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_test_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_test_session

client = TestClient(app)

@pytest.fixture(name="session")
def session_fixture():
    create_test_db_and_tables()
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_score_review(session: Session):
    # Ensure model is loaded or mocked. 
    # For integration test, we rely on the real model if it exists, or the fallback in inference.py
    
    payload = {
        "text": "This is a great place!",
        "rating": 5,
        "platform": "google",
        "user_id": "user123"
    }
    response = client.post("/reviews/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "trust_score" in data
    assert "is_suspicious" in data
    assert "reasons" in data
