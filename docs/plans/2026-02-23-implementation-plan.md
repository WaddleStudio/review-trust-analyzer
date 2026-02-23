# Feature Simplification & LLM Judge Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Remove Single Review + Batch Upload, redirect `/` to Place Analysis, integrate Qwen3-14B as an LLM judge for borderline cases (30–70% trust score), and add `/api/status` for OpenClaw monitoring.

**Architecture:** Hybrid scoring (Rules + ML) handles clear cases; Qwen3-14B via Ollama (WSL2 native) judges only borderline cases. `llm_judge.py` wraps the Ollama HTTP call and is mocked in tests. `inference.py` is extended to return two extra fields: `llm_verdict` and `llm_reasoning`.

**Tech Stack:** FastAPI, SQLModel, Pydantic, httpx (Ollama calls), pytest, uv

---

## Task 1: Remove dead frontend files

**Files:**
- Delete: `app/static/index.html`
- Delete: `app/static/script.js`

**Step 1: Delete the files**

```bash
rm app/static/index.html app/static/script.js
```

**Step 2: Verify they are gone**

```bash
ls app/static/
```
Expected output: `labeling.html  places.html  style.css`

**Step 3: Commit**

```bash
git add -A
git commit -m "chore: remove Single Review and Batch Upload frontend"
```

---

## Task 2: Update app/main.py — redirect root to /places

**Files:**
- Modify: `app/main.py`

**Step 1: Replace the root handler**

Current `app/main.py` line 20–22:
```python
@app.get("/")
async def read_root():
    return FileResponse('app/static/index.html')
```

Replace with:
```python
from fastapi.responses import RedirectResponse

@app.get("/")
async def read_root():
    return RedirectResponse(url="/places")
```

Also remove the unused `FileResponse` import if it's only used for root — keep it since `/places` and `/admin/labeling` still need it.

**Step 2: Verify imports at top of file are correct**

`app/main.py` should import both:
```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
```

**Step 3: Run the existing test to see it fail (expected)**

```bash
uv run pytest tests/test_api.py::test_read_root -v
```
Expected: FAIL — test expects 200 with `text/html`, now gets 307 redirect.

**Step 4: Commit**

```bash
git add app/main.py
git commit -m "feat: redirect / to /places"
```

---

## Task 3: Remove dead API endpoints and Pydantic models

**Files:**
- Modify: `app/api/endpoints.py`

**Step 1: Delete lines 24–152 from endpoints.py**

Remove these blocks entirely:
- `ReviewCreate` model (lines 24–29)
- `ReviewResponse` model (lines 31–39)
- `POST /reviews/score` handler (lines 40–101)
- `POST /reviews/batch` handler (lines 103–152)
- The `from fastapi import File, UploadFile` and `import csv, io` imports (lines 103–105)

The file after editing starts at the `# --- Place Analysis ---` comment.

Resulting `endpoints.py` top section should look like:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from app.database import get_session
from app.models import LabelingTask
from features.text_features import extract_text_features
from features.user_behavior_features import get_user_stats
from app.services.inference import model_service
from app.services.serpapi import SerpAPIService

router = APIRouter()

@router.get("/api/serpapi/usage")
def get_serpapi_usage():
    try:
        svc = SerpAPIService()
        return svc.get_account_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Place Analysis ---
```

Also remove unused imports: `ReviewRaw`, `ReviewFeatures`, `ReviewScore` from the models import line.

**Step 2: Commit**

```bash
git add app/api/endpoints.py
git commit -m "chore: remove /reviews/score and /reviews/batch endpoints"
```

---

## Task 4: Remove batch-analyze skill

**Files:**
- Delete: `.claude/skills/batch-analyze/` (entire directory)

**Step 1: Delete the skill directory**

```bash
rm -rf .claude/skills/batch-analyze
```

**Step 2: Commit**

```bash
git add -A
git commit -m "chore: remove batch-analyze skill"
```

---

## Task 5: Fix tests broken by removals

**Files:**
- Modify: `tests/test_api.py`

**Step 1: Update test_read_root to expect redirect**

Replace:
```python
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
```

With (TestClient follows redirects by default — disable to test the redirect itself, or just confirm final destination):
```python
def test_read_root_redirects_to_places():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/places"
```

**Step 2: Delete test_score_review**

Remove the entire `test_score_review` function (lines 38–53). The endpoint no longer exists.

**Step 3: Run tests**

```bash
uv run pytest tests/test_api.py -v
```
Expected: all remaining tests PASS.

**Step 4: Commit**

```bash
git add tests/test_api.py
git commit -m "test: update test_api.py for removed endpoints and redirect"
```

---

## Task 6: Add OLLAMA_URL to config and docker-compose

**Files:**
- Modify: `app/core/config.py`
- Modify: `docker-compose.yml`

**Step 1: Add OLLAMA_URL to Settings**

Edit `app/core/config.py`:
```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/review_trust_db"
    SERPAPI_KEY: str = ""
    OLLAMA_URL: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 2: Add OLLAMA_URL to docker-compose.yml app service**

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/review_trust_db
      - WATCHFILES_FORCE_POLLING=true
      - OLLAMA_URL=http://host.docker.internal:11434
    depends_on:
      db:
        condition: service_healthy
```

**Step 3: Commit**

```bash
git add app/core/config.py docker-compose.yml
git commit -m "feat: add OLLAMA_URL to config and docker-compose"
```

---

## Task 7: Create llm_judge.py with tests

**Files:**
- Create: `app/services/llm_judge.py`
- Create: `tests/test_llm_judge.py`

**Step 1: Write the failing tests first**

Create `tests/test_llm_judge.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.llm_judge import LLMJudgeService


def test_judge_returns_fake_verdict():
    """LLM responds with fake verdict and reasoning."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"verdict": "fake", "reasoning": "用詞模板化，缺乏具體細節。"}'
    }

    with patch("httpx.post", return_value=mock_response):
        result = service.judge("這家餐廳超棒！強烈推薦！", hybrid_score=0.52)

    assert result["verdict"] == "fake"
    assert "用詞模板化" in result["reasoning"]


def test_judge_returns_real_verdict():
    """LLM responds with real verdict."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": '{"verdict": "real", "reasoning": "描述具體、有細節，可信。"}'
    }

    with patch("httpx.post", return_value=mock_response):
        result = service.judge("點了牛肉麵，等了20分鐘，湯頭偏鹹但麵條Q彈。", hybrid_score=0.45)

    assert result["verdict"] == "real"


def test_judge_ollama_unavailable_returns_none():
    """When Ollama is down, judge returns None gracefully."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    with patch("httpx.post", side_effect=Exception("connection refused")):
        result = service.judge("任意評論", hybrid_score=0.50)

    assert result is None


def test_judge_malformed_json_returns_none():
    """When Ollama returns non-parseable output, returns None."""
    service = LLMJudgeService(base_url="http://localhost:11434")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"response": "我不確定這是什麼格式"}

    with patch("httpx.post", return_value=mock_response):
        result = service.judge("任意評論", hybrid_score=0.55)

    assert result is None
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_llm_judge.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.llm_judge'`

**Step 3: Add httpx dependency**

```bash
uv add httpx
```

**Step 4: Implement llm_judge.py**

Create `app/services/llm_judge.py`:
```python
import json
import httpx
from app.core.config import settings


JUDGE_PROMPT = """你是一個評論真實性分析師。請判斷以下評論是否為真實評論或假評論（業配/刷評論）。

評論內容：
{text}

系統初步評分：{hybrid_score:.0%}（越低越可疑）

請以 JSON 格式回覆，格式如下：
{{"verdict": "real" 或 "fake", "reasoning": "用繁體中文說明判斷理由，2-3句話"}}

只輸出 JSON，不要有其他文字。"""


class LLMJudgeService:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.OLLAMA_URL
        self.model = "qwen3:14b"

    def judge(self, text: str, hybrid_score: float) -> dict | None:
        """
        Ask Qwen3-14B to judge a borderline review.
        Returns {"verdict": "real"|"fake", "reasoning": str} or None on failure.
        """
        prompt = JUDGE_PROMPT.format(text=text, hybrid_score=hybrid_score)
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=30.0,
            )
            raw = response.json().get("response", "")
            parsed = json.loads(raw)
            if "verdict" in parsed and "reasoning" in parsed:
                return parsed
            return None
        except Exception:
            return None


llm_judge_service = LLMJudgeService()
```

**Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_llm_judge.py -v
```
Expected: 4 PASSED

**Step 6: Commit**

```bash
git add app/services/llm_judge.py tests/test_llm_judge.py uv.lock pyproject.toml
git commit -m "feat: add LLMJudgeService with Ollama/Qwen3-14B integration"
```

---

## Task 8: Extend inference.py to call LLM judge for borderline cases

**Files:**
- Modify: `app/services/inference.py`
- Modify: `tests/test_inference.py`

**Step 1: Update test_inference.py for new 7-value return tuple**

Update `tests/test_inference.py` — replace the two existing tests:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.inference import ModelService


def test_inference_rule_score_only():
    """Fallback to pure rule score when no ML model loaded."""
    service = ModelService()
    service.model = None

    features = {
        "text_length": 15,
        "sentiment_score": 0.9,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 6,
    }

    trust_prob, is_suspicious, reasons, rule_score, _, llm_verdict, llm_reasoning = \
        service.predict(features, text="Good free gift")

    assert trust_prob < 1.0
    assert rule_score <= 1.0
    assert "Contains promotional keywords." in reasons
    assert is_suspicious == (trust_prob < 0.5)


def test_llm_not_called_for_clear_cases():
    """LLM judge must NOT be called when score is clearly above 0.70 or below 0.30."""
    service = ModelService()
    service.model = None

    # High trust case (rule_score = 1.0 with no flags)
    features_clean = {
        "text_length": 80,
        "sentiment_score": 0.1,
        "has_promo_keywords": False,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.0,
    }

    with patch("app.services.inference.llm_judge_service.judge") as mock_judge:
        trust_prob, _, _, _, _, llm_verdict, llm_reasoning = \
            service.predict(features_clean, text="Fine dining experience.")
        mock_judge.assert_not_called()

    assert llm_verdict is None
    assert llm_reasoning is None


def test_llm_called_for_borderline_cases():
    """LLM judge IS called when hybrid score falls in 0.30–0.70 range."""
    service = ModelService()
    service.model = None

    # Score designed to land ~0.50 (one promo flag: -0.3, rule_score=0.7, no ML)
    features_borderline = {
        "text_length": 50,
        "sentiment_score": 0.2,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.1,
    }

    mock_result = {"verdict": "fake", "reasoning": "模板化用語。"}

    with patch("app.services.inference.llm_judge_service.judge", return_value=mock_result) as mock_judge:
        trust_prob, _, _, _, _, llm_verdict, llm_reasoning = \
            service.predict(features_borderline, text="Great place! Highly recommend!")
        mock_judge.assert_called_once()

    assert llm_verdict == "fake"
    assert llm_reasoning == "模板化用語。"


def test_llm_unavailable_does_not_break_predict():
    """If Ollama is down, predict() still returns a valid result."""
    service = ModelService()
    service.model = None

    features_borderline = {
        "text_length": 50,
        "sentiment_score": 0.2,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.1,
    }

    with patch("app.services.inference.llm_judge_service.judge", return_value=None):
        trust_prob, is_suspicious, reasons, rule_score, model_score, llm_verdict, llm_reasoning = \
            service.predict(features_borderline, text="Great place!")

    assert isinstance(trust_prob, float)
    assert llm_verdict is None
    assert llm_reasoning is None
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_inference.py -v
```
Expected: FAIL — `not enough values to unpack` (predict still returns 5 values).

**Step 3: Update inference.py**

Replace the full content of `app/services/inference.py`:

```python
import pickle
import os
import numpy as np
from app.core.config import settings
from features.semantic_features import calculate_semantic_promo_score

MODEL_PATH = os.path.join(os.getcwd(), "verification", "model_artifacts", "v2_rf_model.pkl")

LLM_LOWER_THRESHOLD = 0.30
LLM_UPPER_THRESHOLD = 0.70


class ModelService:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            print(f"Model loaded from {MODEL_PATH}")
        else:
            print(f"Model not found at {MODEL_PATH}. Please run ml/train.py.")

    def predict(self, features: dict, text: str = "") -> tuple[float, bool, list[str], float, float, str | None, str | None]:
        """
        Returns:
            (trust_prob, is_suspicious, reasons, rule_score, model_score,
             llm_verdict, llm_reasoning)
        llm_verdict and llm_reasoning are None unless hybrid score is in 0.30–0.70.
        """
        # --- Rule-based score ---
        rule_score = 1.0
        reasons = []
        semantic_score = features.get("semantic_promo_score", calculate_semantic_promo_score(text))

        if features.get("has_promo_keywords", False):
            rule_score -= 0.3
            reasons.append("Contains promotional keywords.")
        if features.get("user_review_count_last_30d", 1) > 5:
            rule_score -= 0.2
            reasons.append("High volume of reviews from user recently.")
        if features.get("text_length", 0) < 20 and abs(features.get("sentiment_score", 0)) > 0.8:
            rule_score -= 0.2
            reasons.append("Short text with extreme sentiment.")
        if semantic_score > 0.6:
            rule_score -= 0.4
            reasons.append(f"Semantically similar to promotional content (Score: {semantic_score:.2f}).")

        rule_score = max(0.0, rule_score)

        # --- ML model score ---
        if not self.model:
            trust_prob = rule_score
            model_score = rule_score
        else:
            import pandas as pd
            feature_vector = pd.DataFrame([{
                "text_length": features.get("text_length", 0),
                "avg_word_length": features.get("avg_word_length", 0.0),
                "sentiment_score": features.get("sentiment_score", 0.0),
                "has_promo_keywords": int(features.get("has_promo_keywords", False)),
                "semantic_promo_score": semantic_score,
                "user_review_count_last_30d": features.get("user_review_count_last_30d", 1),
                "same_ip_review_count_last_7d": features.get("same_ip_review_count_last_7d", 0),
                "rating_deviation_from_avg": features.get("rating_deviation_from_avg", 0.0),
                "is_extreme_rater": int(features.get("is_extreme_rater", False)),
            }])
            try:
                model_score = self.model.predict_proba(feature_vector)[0][0]
                ml_suspicious = bool(self.model.predict(feature_vector)[0])
            except Exception as e:
                print("Model prediction error:", e)
                model_score = rule_score
                ml_suspicious = rule_score < 0.5

            if ml_suspicious:
                reasons.append("ML model flagged as suspicious.")
            trust_prob = (rule_score + model_score) / 2.0

        is_suspicious = trust_prob < 0.5

        # --- LLM judge for borderline cases ---
        llm_verdict = None
        llm_reasoning = None

        if LLM_LOWER_THRESHOLD <= trust_prob <= LLM_UPPER_THRESHOLD:
            from app.services.llm_judge import llm_judge_service
            result = llm_judge_service.judge(text, trust_prob)
            if result:
                llm_verdict = result.get("verdict")
                llm_reasoning = result.get("reasoning")

        return trust_prob, is_suspicious, reasons, rule_score, model_score, llm_verdict, llm_reasoning


model_service = ModelService()
```

**Step 4: Run tests**

```bash
uv run pytest tests/test_inference.py -v
```
Expected: 4 PASSED

**Step 5: Commit**

```bash
git add app/services/inference.py tests/test_inference.py
git commit -m "feat: extend inference.py with LLM judge for borderline cases"
```

---

## Task 9: Extend API schema and wire up llm fields

**Files:**
- Modify: `app/api/endpoints.py`

**Step 1: Add llm fields to PlaceReviewResult**

In `endpoints.py`, update `PlaceReviewResult`:
```python
class PlaceReviewResult(BaseModel):
    text: str
    rating: Optional[int] = None
    trust_score: float
    is_suspicious: bool
    reasons: List[str]
    sentiment_score: float
    author: str = ""
    date: str = ""
    rule_score: Optional[float] = None
    model_score: Optional[float] = None
    llm_verdict: Optional[str] = None
    llm_reasoning: Optional[str] = None
```

**Step 2: Update analyze_place to unpack 7 values**

In the `analyze_place` handler, find the predict call (currently):
```python
trust_score, is_suspicious, reasons, rule_score, model_score = model_service.predict(all_features, text=text)
```

Replace with:
```python
trust_score, is_suspicious, reasons, rule_score, model_score, llm_verdict, llm_reasoning = \
    model_service.predict(all_features, text=text)
```

And update the `PlaceReviewResult(...)` constructor call to include the new fields:
```python
analyzed.append(
    PlaceReviewResult(
        text=text,
        rating=rv.get("rating"),
        trust_score=trust_score,
        is_suspicious=is_suspicious,
        reasons=reasons,
        sentiment_score=all_features["sentiment_score"],
        author=rv.get("author", ""),
        date=rv.get("date", ""),
        rule_score=rule_score,
        model_score=model_score,
        llm_verdict=llm_verdict,
        llm_reasoning=llm_reasoning,
    )
)
```

**Step 3: Run full test suite**

```bash
uv run pytest -v
```
Expected: all tests PASS (or only pre-existing failures unrelated to this change).

**Step 4: Commit**

```bash
git add app/api/endpoints.py
git commit -m "feat: add llm_verdict and llm_reasoning to PlaceReviewResult API response"
```

---

## Task 10: Update places.html to display LLM verdict

**Files:**
- Modify: `app/static/places.html`

**Step 1: Add LLM verdict CSS**

In the `<style>` block of `places.html`, add after the `.review-reasons span` block:

```css
/* ── LLM Judge ───────────────────────────── */
.llm-verdict {
    margin-top: 0.625rem;
    padding: 0.5rem 0.75rem;
    background: rgba(59,130,246,0.06);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 0.5rem;
    font-size: 0.8rem;
    line-height: 1.5;
}
.llm-verdict-label {
    font-weight: 600;
    margin-right: 0.25rem;
}
.llm-verdict-label.fake  { color: var(--danger); }
.llm-verdict-label.real  { color: var(--success); }
.llm-reasoning {
    color: var(--text-muted);
    margin-top: 0.2rem;
    font-size: 0.78rem;
}
```

**Step 2: Update renderResults() to render LLM verdict block**

In the `renderResults()` function inside the `<script>` tag, find where `card.innerHTML` is set. After the `review-reasons` block, add the LLM verdict section:

```javascript
${r.llm_verdict ? `
<div class="llm-verdict">
    <span class="llm-verdict-label ${r.llm_verdict}">🤖 LLM 裁判: ${r.llm_verdict === 'fake' ? '可疑' : '真實'}</span>
    ${r.llm_reasoning ? `<div class="llm-reasoning">${escapeHtml(r.llm_reasoning)}</div>` : ''}
</div>` : ''}
```

The full updated `card.innerHTML` template:
```javascript
card.innerHTML = `
    <div class="review-header">
        <span class="review-author">${escapeHtml(r.author)}</span>
        <span class="review-date">${escapeHtml(r.date)}</span>
    </div>
    <div class="review-stars">${r.rating ? '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating) : ''}</div>
    <div class="review-text">${escapeHtml(r.text)}</div>
    <div class="review-trust">
        <div class="trust-bar">
            <div class="trust-bar-fill ${tc}" style="width:${pct}%;"></div>
        </div>
        <span class="trust-value ${tc}">${pct}%</span>
    </div>
    ${r.reasons.length ? '<div class="review-reasons">' + r.reasons.map(reason => '<span>' + escapeHtml(reason) + '</span>').join('') + '</div>' : ''}
    ${r.llm_verdict ? `
    <div class="llm-verdict">
        <span class="llm-verdict-label ${r.llm_verdict}">🤖 LLM 裁判: ${r.llm_verdict === 'fake' ? '可疑' : '真實'}</span>
        ${r.llm_reasoning ? '<div class="llm-reasoning">' + escapeHtml(r.llm_reasoning) + '</div>' : ''}
    </div>` : ''}
`;
```

**Step 3: Commit**

```bash
git add app/static/places.html
git commit -m "feat: display LLM judge verdict in review cards"
```

---

## Task 11: Add /api/status endpoint

**Files:**
- Modify: `app/api/endpoints.py`
- Create: `tests/test_status.py`

**Step 1: Write failing test**

Create `tests/test_status.py`:
```python
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from unittest.mock import patch
from app.main import app
from app.database import get_session

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(engine)

def get_test_session():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_test_session
client = TestClient(app)


def test_status_returns_expected_fields():
    with patch("httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"models": [{"name": "qwen3:14b"}]}
        response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["server"] == "ok"
    assert "ollama" in data
    assert "labeling_pending" in data
    assert "serpapi_credits" in data


def test_status_ollama_unavailable():
    with patch("httpx.get", side_effect=Exception("connection refused")):
        response = client.get("/api/status")

    assert response.status_code == 200
    data = response.json()
    assert data["ollama"] == "unavailable"
```

**Step 2: Run to verify failure**

```bash
uv run pytest tests/test_status.py -v
```
Expected: FAIL with 404 — `/api/status` does not exist yet.

**Step 3: Implement /api/status in endpoints.py**

Add after the `/api/serpapi/usage` endpoint:

```python
@router.get("/api/status")
def get_status(db: Session = Depends(get_session)):
    from sqlmodel import select
    import httpx

    # Check Ollama
    ollama_status = "unavailable"
    try:
        resp = httpx.get(f"{settings.OLLAMA_URL}/api/tags", timeout=3.0)
        if resp.status_code == 200:
            ollama_status = "ok"
    except Exception:
        pass

    # Pending labeling tasks
    from app.models import LabelingTask
    stmt = select(LabelingTask).where(LabelingTask.status == "pending")
    pending_count = len(db.exec(stmt).all())

    # SerpAPI credits
    serpapi_credits = None
    try:
        svc = SerpAPIService()
        info = svc.get_account_info()
        serpapi_credits = info.get("plan_searches_left") or info.get("searches_per_month")
    except Exception:
        pass

    return {
        "server": "ok",
        "ollama": ollama_status,
        "ollama_model": "qwen3:14b",
        "labeling_pending": pending_count,
        "serpapi_credits": serpapi_credits,
    }
```

Also add `from app.core.config import settings` to the imports at top of `endpoints.py`.

**Step 4: Run tests**

```bash
uv run pytest tests/test_status.py -v
```
Expected: 2 PASSED

**Step 5: Run full test suite**

```bash
uv run pytest -v
```
Expected: all passing.

**Step 6: Commit**

```bash
git add app/api/endpoints.py tests/test_status.py
git commit -m "feat: add /api/status endpoint for OpenClaw health monitoring"
```

---

## Verification

After all tasks complete, run the full suite and start the server to verify:

```bash
# 1. All tests green
uv run pytest -v

# 2. Start server (Ollama must be running in WSL2)
uv run uvicorn app.main:app --reload

# 3. Verify redirect
curl -I http://localhost:8000/
# Expected: HTTP/1.1 307 Temporary Redirect, location: /places

# 4. Verify status endpoint
curl http://localhost:8000/api/status
# Expected: {"server":"ok","ollama":"ok",...}
```
