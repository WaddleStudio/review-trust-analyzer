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
