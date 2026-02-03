from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from app.database import get_session
from app.models import ReviewRaw, ReviewFeatures, ReviewScore
from features.text_features import extract_text_features
from features.user_behavior_features import get_user_stats
from app.services.inference import model_service
from app.services.serpapi import SerpAPIService

router = APIRouter()

class ReviewCreate(BaseModel):
    text: str
    rating: int
    platform: str
    user_id: str
    created_at: Optional[datetime] = None

class ReviewResponse(BaseModel):
    trust_score: float
    is_suspicious: bool
    reasons: List[str]
    sentiment_score: float
    text: Optional[str] = None

@router.post("/reviews/score", response_model=ReviewResponse)
def score_review(review: ReviewCreate, db: Session = Depends(get_session)):
    # 1. Save Raw Review
    db_review = ReviewRaw(
        text=review.text,
        rating=review.rating,
        platform=review.platform,
        user_id=review.user_id,
        created_at=review.created_at or datetime.utcnow()
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # 2. Extract Features
    text_feats = extract_text_features(review.text)
    user_feats = get_user_stats(review.user_id, db)
    
    all_features = {**text_feats, **user_feats}
    
    db_features = ReviewFeatures(
        id=db_review.id,
        text_length=all_features["text_length"],
        avg_word_length=all_features["avg_word_length"],
        sentiment_score=all_features["sentiment_score"],
        has_promo_keywords=all_features["has_promo_keywords"],
        user_review_count_last_30d=all_features["user_review_count_last_30d"],
        same_ip_review_count_last_7d=all_features["same_ip_review_count_last_7d"]
    )
    db.add(db_features)
    
    # 3. Inference
    trust_score, is_suspicious, reasons = model_service.predict(all_features, text=review.text)
    
    # 4. Save Score
    db_score = ReviewScore(
        id=db_review.id,
        trust_score=trust_score,
        is_suspicious=is_suspicious,
        reasons="; ".join(reasons),
        model_version="v1_logistic_regression"
    )
    db.add(db_score)
    db.commit()
    
    return ReviewResponse(
        trust_score=trust_score,
        is_suspicious=is_suspicious,
        reasons=reasons,
        sentiment_score=all_features["sentiment_score"]
    )

from fastapi import File, UploadFile
import csv
import io

@router.post("/reviews/batch", response_model=List[ReviewResponse])
async def batch_score_reviews(file: UploadFile = File(...), db: Session = Depends(get_session)):
    content = await file.read()
    decoded_content = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded_content))
    
    results = []
    results = []
    # Use the global model_service instance imported at the top
    
    for row in csv_reader:
        # Parse row
        try:
            text = row.get("text", "")
            rating = int(row.get("rating", 5))
            platform = row.get("platform", "google")
            user_id = row.get("user_id", "anonymous")
        except ValueError:
            continue # Skip bad rows
            
        # 1. Extract Features
        text_features = extract_text_features(text)
        user_features = get_user_stats(user_id, db)
        all_features = {**text_features, **user_features}
        
        # 2. Inference
        trust_score, is_suspicious, reasons = model_service.predict(all_features, text=text)
        
        # 3. Append to results (We don't save to DB for batch to avoid cluttering, or we could)
        results.append(ReviewResponse(
            trust_score=trust_score,
            is_suspicious=is_suspicious,
            reasons=reasons,
            sentiment_score=all_features["sentiment_score"],
            text=text
        ))

    return results


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
