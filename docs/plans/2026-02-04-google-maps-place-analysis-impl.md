# Google Maps Place Analysis — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "Place Analysis" feature that fetches Google Maps reviews via SerpAPI and analyzes their trustworthiness using the existing hybrid ML/NLP engine.

**Architecture:** New SerpAPI service module calls Google Maps Search + Reviews APIs. Two new API endpoints expose place search and analysis. A new UI tab presents summary + expandable per-review details. Uses existing `model_service.predict()` and `extract_text_features()` for scoring.

**Tech Stack:** Python/FastAPI (backend), SerpAPI REST API (data source), vanilla HTML/CSS/JS (frontend), uv (package management)

---

### Task 1: Migrate to uv package manager

**Files:**
- Modify: `pyproject.toml`
- Delete (after migration): N/A (keep `requirements.txt` as reference for now)

**Step 1: Install uv**

Run: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

Expected: uv installed, `uv --version` returns version number.

**Step 2: Initialize uv in project**

Run (from project root):
```bash
cd D:\Projects\review-trust-analyzer && uv init --no-readme
```

If pyproject.toml conflict, uv will adapt. Then sync:
```bash
uv sync
```

Expected: `uv.lock` created, `.venv` managed by uv, all dependencies installed.

**Step 3: Verify existing tests pass with uv**

Run: `uv run python -m pytest tests/test_api.py -v`

Expected: Tests pass (same as before migration).

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock .python-version
git commit -m "chore: migrate to uv package manager"
```

---

### Task 2: Add SERPAPI_KEY to config

**Files:**
- Modify: `app/core/config.py:1-9`
- Modify: `.env`
- Modify: `.env.example`

**Step 1: Write the failing test**

Create `tests/test_places.py`:

```python
from app.core.config import settings


def test_settings_has_serpapi_key():
    assert hasattr(settings, "SERPAPI_KEY")
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/test_places.py::test_settings_has_serpapi_key -v`

Expected: FAIL — `AssertionError`

**Step 3: Update config**

In `app/core/config.py`, add `SERPAPI_KEY` field to `Settings`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/review_trust_db"
    SERPAPI_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
```

Add to `.env`:
```
SERPAPI_KEY=
```

Add to `.env.example`:
```
# SerpAPI Configuration (for Google Maps place analysis)
SERPAPI_KEY=your_serpapi_key_here
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/test_places.py::test_settings_has_serpapi_key -v`

Expected: PASS

**Step 5: Commit**

```bash
git add app/core/config.py .env.example tests/test_places.py
git commit -m "feat: add SERPAPI_KEY to app config"
```

Note: Do NOT commit `.env` (it may contain real keys).

---

### Task 3: Create SerpAPI service module

**Files:**
- Create: `app/services/serpapi.py`
- Modify: `tests/test_places.py`

**Step 1: Write failing tests**

Append to `tests/test_places.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.serpapi import SerpAPIService


@pytest.fixture
def serpapi():
    return SerpAPIService(api_key="test_key")


def test_serpapi_service_init(serpapi):
    assert serpapi.api_key == "test_key"


def test_parse_google_maps_url():
    svc = SerpAPIService(api_key="test")
    # Standard URL with place name
    url = "https://www.google.com/maps/place/Taipei+101/@25.0339,121.5645"
    result = svc.parse_google_maps_url(url)
    assert result is not None
    assert "Taipei 101" in result or "Taipei+101" in result


def test_detect_input_type_url():
    svc = SerpAPIService(api_key="test")
    assert svc.is_google_maps_url("https://www.google.com/maps/place/Taipei+101") is True
    assert svc.is_google_maps_url("https://maps.app.goo.gl/abc123") is True
    assert svc.is_google_maps_url("Taipei 101") is False


@patch("app.services.serpapi.requests.get")
def test_search_places(mock_get, serpapi):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "local_results": [
                {
                    "title": "Taipei 101",
                    "address": "No. 7, Section 5, Xinyi Road",
                    "rating": 4.5,
                    "reviews": 50000,
                    "data_id": "0x3442abc",
                    "gps_coordinates": {"latitude": 25.03, "longitude": 121.56},
                }
            ]
        },
    )
    results = serpapi.search_places("Taipei 101")
    assert len(results) == 1
    assert results[0]["name"] == "Taipei 101"
    assert results[0]["data_id"] == "0x3442abc"


@patch("app.services.serpapi.requests.get")
def test_fetch_reviews(mock_get, serpapi):
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: {
            "place_info": {
                "title": "Taipei 101",
                "address": "No. 7, Section 5, Xinyi Road",
                "rating": 4.5,
                "reviews": 50000,
            },
            "reviews": [
                {
                    "user": {"name": "John"},
                    "rating": 5,
                    "snippet": "Amazing place!",
                    "date": "2 months ago",
                    "iso_date": "2025-12-01T00:00:00Z",
                }
            ],
        },
    )
    place_info, reviews = serpapi.fetch_reviews("0x3442abc")
    assert place_info["name"] == "Taipei 101"
    assert len(reviews) == 1
    assert reviews[0]["text"] == "Amazing place!"
    assert reviews[0]["author"] == "John"
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_places.py -v -k "not test_settings"`

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.serpapi'`

**Step 3: Implement SerpAPI service**

Create `app/services/serpapi.py`:

```python
import re
from urllib.parse import unquote

import requests

from app.core.config import settings

SERPAPI_BASE = "https://serpapi.com/search"


class SerpAPIService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.SERPAPI_KEY

    def is_google_maps_url(self, text: str) -> bool:
        patterns = [
            r"google\.\w+/maps",
            r"maps\.google\.",
            r"maps\.app\.goo\.gl",
            r"goo\.gl/maps",
        ]
        return any(re.search(p, text) for p in patterns)

    def parse_google_maps_url(self, url: str) -> str | None:
        """Extract place name from a Google Maps URL."""
        match = re.search(r"/maps/place/([^/@]+)", url)
        if match:
            return unquote(match.group(1).replace("+", " "))
        return None

    def search_places(self, query: str) -> list[dict]:
        """Search Google Maps for places matching the query."""
        params = {
            "engine": "google_maps",
            "q": query,
            "type": "search",
            "api_key": self.api_key,
        }
        resp = requests.get(SERPAPI_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("local_results", []):
            coords = item.get("gps_coordinates", {})
            results.append(
                {
                    "name": item.get("title", ""),
                    "address": item.get("address", ""),
                    "rating": item.get("rating"),
                    "total_reviews": item.get("reviews", 0),
                    "data_id": item.get("data_id", ""),
                    "gps_coordinates": {
                        "lat": coords.get("latitude"),
                        "lng": coords.get("longitude"),
                    },
                }
            )
        return results

    def fetch_reviews(self, data_id: str, num: int = 20) -> tuple[dict, list[dict]]:
        """Fetch reviews for a place by data_id."""
        params = {
            "engine": "google_maps_reviews",
            "data_id": data_id,
            "sort_by": "newestFirst",
            "num": num,
            "hl": "zh-TW",
            "api_key": self.api_key,
        }
        resp = requests.get(SERPAPI_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        pi = data.get("place_info", {})
        place_info = {
            "name": pi.get("title", ""),
            "address": pi.get("address", ""),
            "rating": pi.get("rating"),
            "total_reviews": pi.get("reviews", 0),
        }

        reviews = []
        for r in data.get("reviews", []):
            user = r.get("user", {})
            extracted = r.get("extracted_snippet", {})
            text = extracted.get("original") or r.get("snippet", "")
            reviews.append(
                {
                    "text": text,
                    "rating": r.get("rating"),
                    "author": user.get("name", "Anonymous"),
                    "date": r.get("date", ""),
                    "iso_date": r.get("iso_date", ""),
                }
            )
        return place_info, reviews
```

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_places.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add app/services/serpapi.py tests/test_places.py
git commit -m "feat: add SerpAPI service for Google Maps search and reviews"
```

---

### Task 4: Add API endpoints for place search and analysis

**Files:**
- Modify: `app/api/endpoints.py:1-5` (add imports)
- Modify: `app/api/endpoints.py` (append new endpoints)
- Modify: `tests/test_places.py` (add endpoint tests)

**Step 1: Write failing tests**

Append to `tests/test_places.py`:

```python
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from app.main import app
from app.database import get_session

# Reuse test DB setup from test_api.py pattern
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def _get_test_session():
    with Session(_engine) as session:
        yield session


app.dependency_overrides[get_session] = _get_test_session
_client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(_engine)
    yield
    SQLModel.metadata.drop_all(_engine)


@patch("app.api.endpoints.SerpAPIService")
def test_places_search_endpoint(mock_cls):
    instance = mock_cls.return_value
    instance.search_places.return_value = [
        {
            "name": "Taipei 101",
            "address": "Xinyi Road",
            "rating": 4.5,
            "total_reviews": 50000,
            "data_id": "0x3442abc",
            "gps_coordinates": {"lat": 25.03, "lng": 121.56},
        }
    ]
    resp = _client.get("/places/search", params={"q": "Taipei 101"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["name"] == "Taipei 101"


@patch("app.api.endpoints.SerpAPIService")
def test_places_analyze_endpoint(mock_cls):
    instance = mock_cls.return_value
    instance.is_google_maps_url.return_value = False
    instance.search_places.return_value = [
        {"name": "Test Place", "address": "Addr", "rating": 4.0, "total_reviews": 100, "data_id": "0xabc", "gps_coordinates": {"lat": 0, "lng": 0}}
    ]
    instance.fetch_reviews.return_value = (
        {"name": "Test Place", "address": "Addr", "rating": 4.0, "total_reviews": 100},
        [
            {"text": "Great food!", "rating": 5, "author": "User1", "date": "1 month ago", "iso_date": "2026-01-01"},
            {"text": "Best place ever! Highly recommended! Must visit!", "rating": 5, "author": "User2", "date": "2 weeks ago", "iso_date": "2026-01-15"},
        ],
    )
    resp = _client.post("/places/analyze", json={"query": "Test Place"})
    assert resp.status_code == 200
    data = resp.json()
    assert "place" in data
    assert "summary" in data
    assert "reviews" in data
    assert data["summary"]["total_analyzed"] == 2
    assert data["place"]["name"] == "Test Place"
```

**Step 2: Run tests to verify they fail**

Run: `uv run python -m pytest tests/test_places.py::test_places_search_endpoint tests/test_places.py::test_places_analyze_endpoint -v`

Expected: FAIL — endpoint not found (404)

**Step 3: Implement the endpoints**

Add to `app/api/endpoints.py` — new imports at the top (after existing imports):

```python
from app.services.serpapi import SerpAPIService
```

Append new Pydantic models and endpoints at the end of `app/api/endpoints.py`:

```python
# --- Place Analysis ---

class PlaceSearchResult(BaseModel):
    name: str
    address: str
    rating: Optional[float] = None
    total_reviews: int = 0
    data_id: str = ""
    gps_coordinates: Optional[dict] = None


class PlaceSearchResponse(BaseModel):
    results: List[PlaceSearchResult]


class PlaceAnalyzeRequest(BaseModel):
    query: str
    api_key: Optional[str] = None


class PlaceReviewResult(BaseModel):
    text: str
    rating: Optional[int] = None
    trust_score: float
    is_suspicious: bool
    reasons: List[str]
    sentiment_score: float
    author: str = ""
    date: str = ""


class PlaceSummary(BaseModel):
    overall_trust_score: float
    suspicious_count: int
    total_analyzed: int
    suspicious_ratio: float
    key_findings: List[str]


class PlaceInfo(BaseModel):
    name: str
    address: str
    rating: Optional[float] = None
    total_reviews: int = 0


class PlaceAnalyzeResponse(BaseModel):
    place: PlaceInfo
    summary: PlaceSummary
    reviews: List[PlaceReviewResult]


@router.get("/places/search", response_model=PlaceSearchResponse)
def search_places(q: str, api_key: Optional[str] = None):
    svc = SerpAPIService(api_key=api_key or None)
    if not svc.api_key:
        raise HTTPException(status_code=400, detail="SerpAPI key not configured. Set SERPAPI_KEY in .env or provide api_key parameter.")
    results = svc.search_places(q)
    return PlaceSearchResponse(results=results)


@router.post("/places/analyze", response_model=PlaceAnalyzeResponse)
def analyze_place(req: PlaceAnalyzeRequest, db: Session = Depends(get_session)):
    svc = SerpAPIService(api_key=req.api_key or None)
    if not svc.api_key:
        raise HTTPException(status_code=400, detail="SerpAPI key not configured. Set SERPAPI_KEY in .env or provide api_key parameter.")

    # Determine data_id from input
    data_id = None
    if svc.is_google_maps_url(req.query):
        place_name = svc.parse_google_maps_url(req.query)
        if place_name:
            candidates = svc.search_places(place_name)
            if candidates:
                data_id = candidates[0]["data_id"]
    else:
        # Treat as keyword or direct data_id
        if req.query.startswith("0x"):
            data_id = req.query
        else:
            candidates = svc.search_places(req.query)
            if candidates:
                data_id = candidates[0]["data_id"]

    if not data_id:
        raise HTTPException(status_code=404, detail="Place not found. Try a different search term or URL.")

    # Fetch reviews
    place_info, raw_reviews = svc.fetch_reviews(data_id)

    # Analyze each review
    analyzed = []
    for rv in raw_reviews:
        text = rv.get("text", "")
        if not text:
            continue
        text_feats = extract_text_features(text)
        user_feats = get_user_stats("anonymous", db)
        all_features = {**text_feats, **user_feats}
        trust_score, is_suspicious, reasons = model_service.predict(all_features, text=text)
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
            )
        )

    # Build summary
    total = len(analyzed)
    suspicious_count = sum(1 for r in analyzed if r.is_suspicious)
    avg_trust = sum(r.trust_score for r in analyzed) / total if total else 0

    findings = []
    if suspicious_count > 0:
        findings.append(f"{suspicious_count}/{total} reviews flagged as suspicious ({suspicious_count/total*100:.0f}%)")
    promo_count = sum(1 for r in analyzed if any("promotional" in reason.lower() for reason in r.reasons))
    if promo_count:
        findings.append(f"{promo_count} reviews contain promotional keywords")
    semantic_count = sum(1 for r in analyzed if any("semantic" in reason.lower() for reason in r.reasons))
    if semantic_count:
        findings.append(f"{semantic_count} reviews are semantically similar to promotional content")
    if not findings:
        findings.append("No significant suspicious patterns detected")

    # Sort: suspicious first
    analyzed.sort(key=lambda r: r.trust_score)

    return PlaceAnalyzeResponse(
        place=PlaceInfo(
            name=place_info.get("name", ""),
            address=place_info.get("address", ""),
            rating=place_info.get("rating"),
            total_reviews=place_info.get("total_reviews", 0),
        ),
        summary=PlaceSummary(
            overall_trust_score=round(avg_trust, 4),
            suspicious_count=suspicious_count,
            total_analyzed=total,
            suspicious_ratio=round(suspicious_count / total, 4) if total else 0,
            key_findings=findings,
        ),
        reviews=analyzed,
    )
```

**Step 4: Run tests to verify they pass**

Run: `uv run python -m pytest tests/test_places.py -v`

Expected: All tests PASS

**Step 5: Commit**

```bash
git add app/api/endpoints.py tests/test_places.py
git commit -m "feat: add /places/search and /places/analyze API endpoints"
```

---

### Task 5: Create Place Analysis UI page

**Files:**
- Create: `app/static/places.html`
- Modify: `app/static/index.html:32-35` (add third tab)
- Modify: `app/static/style.css` (append place analysis styles)
- Modify: `app/main.py` (add route for places.html)

**Step 1: Add route in main.py**

Append to `app/main.py` after the existing `read_root` route:

```python
@app.get("/places")
async def read_places():
    return FileResponse('app/static/places.html')
```

**Step 2: Create places.html**

Create `app/static/places.html` — a standalone page that:
- Shares the same `style.css` and glassmorphism look
- Has a single search input + "Analyze" button
- Has an expandable "Advanced Settings" section for SerpAPI key
- Shows a candidate list when searching by keyword
- Shows summary report card (place info, trust score circle, suspicious ratio, findings)
- Shows collapsible review detail cards
- Each review card has: author, date, stars, text, trust score bar, reasons
- Suspicious reviews have red-left-border, trustworthy have green

The HTML should include inline `<script>` at the bottom with:
- `detectInputType(text)` — returns `"url"` or `"keyword"`
- `handleSearch()` — calls GET `/places/search?q=...`, shows candidate list
- `handleAnalyze(dataId)` — calls POST `/places/analyze`, renders results
- `toggleReviewDetails()` — expand/collapse review section
- Color logic matching existing: green >= 80%, yellow >= 50%, red < 50%

Full content for `app/static/places.html`:

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Place Analysis - Trust Analyzer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/style.css">
    <style>
        /* Place Analysis specific styles */
        body { align-items: flex-start; padding-top: 2rem; }
        .container { max-width: 960px; }
        main { display: block; }

        .nav-tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; justify-content: center; }
        .nav-tabs a {
            padding: 0.5rem 1.25rem; border-radius: 0.5rem; text-decoration: none;
            color: var(--text-muted); border: 1px solid var(--border); font-size: 0.9rem; transition: all 0.2s;
        }
        .nav-tabs a:hover { border-color: var(--primary); color: var(--text-main); }
        .nav-tabs a.active { background: var(--primary); color: white; border-color: var(--primary); }

        .search-row { display: flex; gap: 0.75rem; }
        .search-row input { flex: 1; }
        .search-row button { width: auto; padding: 0.75rem 1.5rem; white-space: nowrap; }

        .advanced-toggle {
            background: none; border: none; color: var(--text-muted); font-size: 0.85rem;
            cursor: pointer; padding: 0.5rem 0; width: auto; text-align: left;
        }
        .advanced-toggle:hover { color: var(--primary); background: none; }
        .advanced-panel { display: none; margin-top: 0.5rem; }
        .advanced-panel.show { display: block; }

        .candidates { margin-top: 1rem; }
        .candidate-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 1rem; background: rgba(15,23,42,0.4); border-radius: 0.75rem;
            margin-bottom: 0.5rem; border: 1px solid var(--border); cursor: pointer; transition: all 0.2s;
        }
        .candidate-item:hover { border-color: var(--primary); background: rgba(99,102,241,0.1); }
        .candidate-name { font-weight: 600; }
        .candidate-meta { color: var(--text-muted); font-size: 0.85rem; }
        .candidate-rating { color: var(--warning); }

        .summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1.5rem 0; }
        .summary-stat {
            text-align: center; padding: 1.25rem; background: rgba(15,23,42,0.3);
            border-radius: 0.75rem; border: 1px solid var(--border);
        }
        .summary-stat .stat-value { font-size: 2rem; font-weight: 700; }
        .summary-stat .stat-label { color: var(--text-muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 0.25rem; }

        .findings { margin: 1rem 0; }
        .finding-item {
            padding: 0.75rem 1rem; background: rgba(15,23,42,0.3); border-radius: 0.5rem;
            margin-bottom: 0.5rem; border-left: 3px solid var(--primary); font-size: 0.9rem;
        }

        .details-toggle {
            background: none; border: 1px solid var(--border); color: var(--text-muted);
            padding: 0.75rem; border-radius: 0.75rem; margin-top: 1rem; font-size: 0.9rem; cursor: pointer;
        }
        .details-toggle:hover { border-color: var(--primary); color: var(--text-main); background: none; }

        .review-list { margin-top: 1rem; }
        .review-card {
            padding: 1.25rem; background: rgba(15,23,42,0.3); border-radius: 0.75rem;
            margin-bottom: 0.75rem; border-left: 4px solid var(--success); transition: all 0.2s;
        }
        .review-card.suspicious { border-left-color: var(--danger); }
        .review-card.moderate { border-left-color: var(--warning); }
        .review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .review-author { font-weight: 600; font-size: 0.9rem; }
        .review-date { color: var(--text-muted); font-size: 0.8rem; }
        .review-stars { color: var(--warning); font-size: 0.9rem; margin-bottom: 0.5rem; }
        .review-text { font-size: 0.9rem; line-height: 1.6; margin-bottom: 0.75rem; color: var(--text-main); }
        .review-trust { display: flex; align-items: center; gap: 0.75rem; }
        .trust-bar { flex: 1; height: 6px; background: rgba(148,163,184,0.2); border-radius: 3px; overflow: hidden; }
        .trust-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
        .trust-value { font-weight: 600; font-size: 0.85rem; min-width: 3rem; text-align: right; }
        .review-reasons { margin-top: 0.5rem; }
        .review-reasons span {
            display: inline-block; font-size: 0.75rem; padding: 0.2rem 0.5rem;
            background: rgba(239,68,68,0.15); color: var(--danger); border-radius: 0.25rem; margin: 0.15rem 0.15rem 0 0;
        }

        .place-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
        .place-header h3 { font-size: 1.3rem; }
        .place-address { color: var(--text-muted); font-size: 0.9rem; }
        .place-google-rating { color: var(--warning); font-weight: 600; }

        .loading-overlay {
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(15,23,42,0.8); z-index: 999; justify-content: center; align-items: center;
            backdrop-filter: blur(4px);
        }
        .loading-overlay.show { display: flex; }
        .loading-spinner { text-align: center; color: var(--text-main); }
        .loading-spinner .loader { margin: 0 auto 1rem; width: 40px; height: 40px; border-width: 4px; }
    </style>
</head>
<body>
    <div class="background-glow"></div>
    <div class="container">
        <header>
            <div class="logo">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <h1>Trust Analyzer</h1>
            </div>
            <p class="subtitle">Detect fake reviews with AI-powered precision.</p>
        </header>

        <nav class="nav-tabs">
            <a href="/">Single Review</a>
            <a href="/" onclick="return false;">Batch Upload</a>
            <a href="/places" class="active">Place Analysis</a>
        </nav>

        <main>
            <div class="card">
                <h2>Analyze a Place</h2>
                <div class="search-row">
                    <input type="text" id="placeInput" placeholder="Paste a Google Maps URL or enter a place name...">
                    <button id="searchBtn" onclick="handleInput()">
                        <span class="btn-text">Analyze</span>
                        <div class="loader" style="display:none;"></div>
                    </button>
                </div>
                <button class="advanced-toggle" onclick="toggleAdvanced()">&#9662; Advanced Settings</button>
                <div class="advanced-panel" id="advancedPanel">
                    <div class="form-group">
                        <label for="apiKeyInput">SerpAPI Key (optional)</label>
                        <input type="text" id="apiKeyInput" placeholder="Your SerpAPI key (leave empty to use default)">
                    </div>
                </div>

                <div class="candidates" id="candidateList" style="display:none;">
                    <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:0.5rem;">Select a place:</p>
                    <div id="candidateItems"></div>
                </div>
            </div>

            <div class="card" id="resultCard" style="display:none;">
                <div class="place-header">
                    <div>
                        <h3 id="placeName"></h3>
                        <span class="place-address" id="placeAddress"></span>
                    </div>
                    <div>
                        <span class="place-google-rating" id="placeRating"></span>
                        <span style="color:var(--text-muted);font-size:0.85rem;" id="placeReviewCount"></span>
                    </div>
                </div>

                <div class="summary-grid">
                    <div class="summary-stat">
                        <div class="stat-value" id="trustScoreValue">--</div>
                        <div class="stat-label">Overall Trust Score</div>
                    </div>
                    <div class="summary-stat">
                        <div class="stat-value" id="suspiciousRatio">--</div>
                        <div class="stat-label">Suspicious Reviews</div>
                    </div>
                </div>

                <div class="findings" id="findings"></div>

                <button class="details-toggle" id="detailsToggle" onclick="toggleDetails()">
                    &#9662; View Detailed Review Analysis (<span id="reviewCount">0</span> reviews)
                </button>

                <div class="review-list" id="reviewList" style="display:none;"></div>
            </div>
        </main>
    </div>

    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-spinner">
            <div class="loader"></div>
            <p>Analyzing reviews...</p>
        </div>
    </div>

    <script>
    function getApiKey() {
        return document.getElementById('apiKeyInput').value.trim() || undefined;
    }

    function toggleAdvanced() {
        document.getElementById('advancedPanel').classList.toggle('show');
    }

    function isGoogleMapsUrl(text) {
        return /google\.\w+\/maps|maps\.google\.|maps\.app\.goo\.gl|goo\.gl\/maps/.test(text);
    }

    function showLoading(show) {
        document.getElementById('loadingOverlay').classList.toggle('show', show);
    }

    async function handleInput() {
        const input = document.getElementById('placeInput').value.trim();
        if (!input) return;

        document.getElementById('candidateList').style.display = 'none';
        document.getElementById('resultCard').style.display = 'none';

        if (isGoogleMapsUrl(input)) {
            await analyzePlace(input);
        } else {
            await searchPlaces(input);
        }
    }

    async function searchPlaces(query) {
        const btn = document.getElementById('searchBtn');
        btn.disabled = true;
        btn.querySelector('.loader').style.display = 'block';
        btn.querySelector('.btn-text').style.display = 'none';

        try {
            const params = new URLSearchParams({ q: query });
            const apiKey = getApiKey();
            if (apiKey) params.append('api_key', apiKey);

            const resp = await fetch('/places/search?' + params);
            if (!resp.ok) {
                const err = await resp.json();
                alert(err.detail || 'Search failed');
                return;
            }
            const data = await resp.json();

            if (data.results.length === 0) {
                alert('No places found. Try a different search term.');
                return;
            }

            if (data.results.length === 1) {
                await analyzeByDataId(data.results[0].data_id);
                return;
            }

            renderCandidates(data.results);
        } catch (e) {
            console.error(e);
            alert('An error occurred during search.');
        } finally {
            btn.disabled = false;
            btn.querySelector('.loader').style.display = 'none';
            btn.querySelector('.btn-text').style.display = 'block';
        }
    }

    function renderCandidates(results) {
        const container = document.getElementById('candidateItems');
        container.innerHTML = '';
        results.forEach(r => {
            const div = document.createElement('div');
            div.className = 'candidate-item';
            div.onclick = () => analyzeByDataId(r.data_id);
            div.innerHTML = `
                <div>
                    <div class="candidate-name">${r.name}</div>
                    <div class="candidate-meta">${r.address}</div>
                </div>
                <div style="text-align:right;">
                    <div class="candidate-rating">${r.rating ? '★ ' + r.rating : ''}</div>
                    <div class="candidate-meta">${r.total_reviews ? r.total_reviews + ' reviews' : ''}</div>
                </div>
            `;
            container.appendChild(div);
        });
        document.getElementById('candidateList').style.display = 'block';
    }

    async function analyzePlace(query) {
        showLoading(true);
        try {
            const body = { query };
            const apiKey = getApiKey();
            if (apiKey) body.api_key = apiKey;

            const resp = await fetch('/places/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!resp.ok) {
                const err = await resp.json();
                alert(err.detail || 'Analysis failed');
                return;
            }
            const data = await resp.json();
            renderResults(data);
        } catch (e) {
            console.error(e);
            alert('An error occurred during analysis.');
        } finally {
            showLoading(false);
        }
    }

    async function analyzeByDataId(dataId) {
        document.getElementById('candidateList').style.display = 'none';
        showLoading(true);
        try {
            const body = { query: dataId };
            const apiKey = getApiKey();
            if (apiKey) body.api_key = apiKey;

            const resp = await fetch('/places/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!resp.ok) {
                const err = await resp.json();
                alert(err.detail || 'Analysis failed');
                return;
            }
            const data = await resp.json();
            renderResults(data);
        } catch (e) {
            console.error(e);
            alert('An error occurred during analysis.');
        } finally {
            showLoading(false);
        }
    }

    function trustColor(score) {
        const pct = score * 100;
        if (pct >= 80) return 'var(--success)';
        if (pct >= 50) return 'var(--warning)';
        return 'var(--danger)';
    }

    function renderResults(data) {
        const { place, summary, reviews } = data;

        document.getElementById('placeName').textContent = place.name;
        document.getElementById('placeAddress').textContent = place.address;
        document.getElementById('placeRating').textContent = place.rating ? '★ ' + place.rating : '';
        document.getElementById('placeReviewCount').textContent = place.total_reviews ? `(${place.total_reviews} reviews on Google)` : '';

        const trustPct = Math.round(summary.overall_trust_score * 100);
        const trustEl = document.getElementById('trustScoreValue');
        trustEl.textContent = trustPct + '%';
        trustEl.style.color = trustColor(summary.overall_trust_score);

        const ratioEl = document.getElementById('suspiciousRatio');
        ratioEl.textContent = `${summary.suspicious_count} / ${summary.total_analyzed}`;
        ratioEl.style.color = summary.suspicious_count > 0 ? 'var(--danger)' : 'var(--success)';

        const findingsEl = document.getElementById('findings');
        findingsEl.innerHTML = '';
        summary.key_findings.forEach(f => {
            const div = document.createElement('div');
            div.className = 'finding-item';
            div.textContent = f;
            findingsEl.appendChild(div);
        });

        document.getElementById('reviewCount').textContent = reviews.length;

        const listEl = document.getElementById('reviewList');
        listEl.innerHTML = '';
        reviews.forEach(r => {
            const pct = Math.round(r.trust_score * 100);
            const cls = r.is_suspicious ? 'suspicious' : (r.trust_score < 0.8 ? 'moderate' : '');
            const card = document.createElement('div');
            card.className = 'review-card ' + cls;
            card.innerHTML = `
                <div class="review-header">
                    <span class="review-author">${r.author}</span>
                    <span class="review-date">${r.date}</span>
                </div>
                <div class="review-stars">${r.rating ? '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating) : ''}</div>
                <div class="review-text">${r.text}</div>
                <div class="review-trust">
                    <div class="trust-bar">
                        <div class="trust-bar-fill" style="width:${pct}%;background:${trustColor(r.trust_score)};"></div>
                    </div>
                    <span class="trust-value" style="color:${trustColor(r.trust_score)}">${pct}%</span>
                </div>
                ${r.reasons.length ? '<div class="review-reasons">' + r.reasons.map(reason => '<span>' + reason + '</span>').join('') + '</div>' : ''}
            `;
            listEl.appendChild(card);
        });

        listEl.style.display = 'none';
        document.getElementById('detailsToggle').innerHTML = `&#9662; View Detailed Review Analysis (<span id="reviewCount">${reviews.length}</span> reviews)`;
        document.getElementById('resultCard').style.display = 'block';
    }

    function toggleDetails() {
        const list = document.getElementById('reviewList');
        const btn = document.getElementById('detailsToggle');
        const count = document.getElementById('reviewCount').textContent;
        if (list.style.display === 'none') {
            list.style.display = 'block';
            btn.innerHTML = `&#9652; Hide Detailed Review Analysis (<span id="reviewCount">${count}</span> reviews)`;
        } else {
            list.style.display = 'none';
            btn.innerHTML = `&#9662; View Detailed Review Analysis (<span id="reviewCount">${count}</span> reviews)`;
        }
    }

    // Enter key triggers search
    document.getElementById('placeInput').addEventListener('keydown', e => {
        if (e.key === 'Enter') handleInput();
    });
    </script>
</body>
</html>
```

**Step 3: Add tab link in index.html**

In `app/static/index.html`, after the existing tabs div (line 32-35), add the "Place Analysis" tab. Modify the `.tabs` section:

```html
<div class="tabs">
    <button class="tab-btn active" onclick="switchTab('single')">Single Review</button>
    <button class="tab-btn" onclick="switchTab('batch')">Batch Upload (CSV)</button>
    <a href="/places" class="tab-btn" style="text-decoration:none;text-align:center;">Place Analysis</a>
</div>
```

**Step 4: Add route in main.py**

Append after the existing `read_root` route at line 22 in `app/main.py`:

```python
@app.get("/places")
async def read_places():
    return FileResponse('app/static/places.html')
```

**Step 5: Manual test**

Run: `uv run uvicorn app.main:app --reload`

1. Open `http://localhost:8000/places`
2. Verify the page loads with the glassmorphism theme
3. Verify the nav tabs link correctly
4. If you have a SerpAPI key, test with a real place name

**Step 6: Commit**

```bash
git add app/static/places.html app/static/index.html app/main.py
git commit -m "feat: add Place Analysis UI page with search and review display"
```

---

### Task 6: Update .env.example and final integration test

**Files:**
- Modify: `.env.example`
- Modify: `tests/test_places.py` (add integration-style tests)

**Step 1: Update .env.example**

Append to `.env.example`:

```
# SerpAPI Configuration (for Google Maps place analysis)
# Get your key at https://serpapi.com/
SERPAPI_KEY=your_serpapi_key_here
```

**Step 2: Add a test for the /places route**

Append to `tests/test_places.py`:

```python
def test_places_page_loads():
    resp = _client.get("/places")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
```

**Step 3: Run all tests**

Run: `uv run python -m pytest -v`

Expected: All tests pass.

**Step 4: Commit**

```bash
git add .env.example tests/test_places.py
git commit -m "feat: finalize place analysis feature with updated config and tests"
```

---

## Summary of all tasks

| Task | Description | Files |
|------|-------------|-------|
| 1 | Migrate to uv | `pyproject.toml`, `uv.lock` |
| 2 | Add SERPAPI_KEY config | `config.py`, `.env`, `.env.example`, `test_places.py` |
| 3 | SerpAPI service module | `serpapi.py`, `test_places.py` |
| 4 | API endpoints | `endpoints.py`, `test_places.py` |
| 5 | Place Analysis UI | `places.html`, `index.html`, `main.py`, `style.css` |
| 6 | Final integration | `.env.example`, `test_places.py` |
