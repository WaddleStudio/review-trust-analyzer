import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from unittest.mock import patch, MagicMock
from app.main import app
from app.database import get_session
from app.models import LabelingTask

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

BORDERLINE_REVIEW = {
    "snippet": "這家餐廳不錯，服務也很好。",
    "rating": 4,
    "user": {"name": "TestUser"},
    "date": "2024-01-01",
}

PLACE_INFO = {"name": "Test Place", "address": "123 Test St", "rating": 4.0, "total_reviews": 1}


def _mock_serpapi(review_text="這家餐廳不錯，服務也很好。", rating=4):
    svc = MagicMock()
    svc.api_key = "test"
    svc.is_google_maps_url.return_value = False
    svc.search_places.return_value = [{"data_id": "test_id", "name": "Test Place"}]
    svc.fetch_reviews.return_value = (
        PLACE_INFO,
        [{"text": review_text, "rating": rating, "author": "TestUser", "date": "2024-01-01"}],
    )
    return svc


def test_borderline_review_queued_with_llm_verdict():
    """When LLM judge is called for a borderline review, a LabelingTask is created."""
    llm_result = {"verdict": "fake", "reasoning": "用詞模板化。"}

    with patch("app.api.endpoints.SerpAPIService", return_value=_mock_serpapi()), \
         patch("app.services.inference.llm_judge_service.judge", return_value=llm_result), \
         patch("app.services.inference.ModelService.predict",
               return_value=(0.50, True, ["Contains promotional keywords."], 0.50, 0.50, "fake", "用詞模板化。")):

        response = client.post("/places/analyze", json={"query": "Test Place"})

    assert response.status_code == 200

    with Session(engine) as session:
        tasks = session.exec(select(LabelingTask)).all()
        assert len(tasks) == 1
        task = tasks[0]
        assert task.pre_label == "fake"
        assert task.pre_confidence == pytest.approx(0.50, abs=0.01)
        assert task.status == "pending"
        assert "TestUser" in task.source_id or "test" in task.source_id.lower()


def test_clear_review_not_queued():
    """Reviews with trust_score outside 0.30–0.70 should NOT be queued."""
    with patch("app.api.endpoints.SerpAPIService", return_value=_mock_serpapi()), \
         patch("app.services.inference.ModelService.predict",
               return_value=(0.95, False, [], 0.95, 0.95, None, None)):

        response = client.post("/places/analyze", json={"query": "Test Place"})

    assert response.status_code == 200

    with Session(engine) as session:
        tasks = session.exec(select(LabelingTask)).all()
        assert len(tasks) == 0


def test_borderline_no_llm_verdict_not_queued():
    """Borderline review where Ollama is down (llm_verdict=None) should NOT be queued."""
    with patch("app.api.endpoints.SerpAPIService", return_value=_mock_serpapi()), \
         patch("app.services.inference.ModelService.predict",
               return_value=(0.50, True, ["Contains promotional keywords."], 0.50, 0.50, None, None)):

        response = client.post("/places/analyze", json={"query": "Test Place"})

    assert response.status_code == 200

    with Session(engine) as session:
        tasks = session.exec(select(LabelingTask)).all()
        assert len(tasks) == 0
