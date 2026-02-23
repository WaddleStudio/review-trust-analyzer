from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

import httpx

from app.core.config import settings
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

@router.get("/api/status")
def get_status(db: Session = Depends(get_session)):
    # Check Ollama
    ollama_status = "unavailable"
    try:
        resp = httpx.get(f"{settings.OLLAMA_URL}/api/tags", timeout=3.0)
        if resp.status_code == 200:
            ollama_status = "ok"
    except Exception:
        pass

    # Pending labeling tasks
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
    rule_score: Optional[float] = None
    model_score: Optional[float] = None
    llm_verdict: Optional[str] = None
    llm_reasoning: Optional[str] = None


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
        user_feats = get_user_stats("anonymous", db, rv.get("rating"))
        from features.semantic_features import calculate_semantic_promo_score
        semantic_score = calculate_semantic_promo_score(text)
        all_features = {
            **text_feats, 
            **user_feats, 
            "semantic_promo_score": semantic_score
        }
        trust_score, is_suspicious, reasons, rule_score, model_score, llm_verdict, llm_reasoning = \
            model_service.predict(all_features, text=text)
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
                llm_reasoning=llm_reasoning
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

# --- Labeling API ---

class LabelingTaskResponse(BaseModel):
    id: int
    project_type: str
    source_id: str
    content_json: dict
    pre_label: Optional[str] = None
    pre_confidence: Optional[float] = None
    
class LabelSubmitRequest(BaseModel):
    human_label: str  # e.g., 'real', 'suspicious'
    status: str = "labeled"

@router.get("/api/labeling/pending", response_model=List[LabelingTaskResponse])
def get_pending_tasks(limit: int = 10, db: Session = Depends(get_session)):
    from sqlmodel import select
    stmt = select(LabelingTask).where(LabelingTask.status == "pending").limit(limit)
    tasks = db.exec(stmt).all()
    return tasks

@router.post("/api/labeling/{task_id}/submit")
def submit_label(task_id: int, req: LabelSubmitRequest, db: Session = Depends(get_session)):
    task = db.get(LabelingTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task.human_label = req.human_label
    task.status = req.status
    task.labeled_at = datetime.utcnow()
    
    db.add(task)
    db.commit()
    return {"status": "success"}
