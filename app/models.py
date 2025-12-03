from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class ReviewRaw(SQLModel, table=True):
    __tablename__ = "reviews_raw"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str
    external_review_id: Optional[str] = None
    user_id: str
    rating: int
    text: str
    created_at: datetime
    inserted_at: datetime = Field(default_factory=datetime.utcnow)
    
    features: Optional["ReviewFeatures"] = Relationship(back_populates="review")
    score: Optional["ReviewScore"] = Relationship(back_populates="review")

class ReviewFeatures(SQLModel, table=True):
    __tablename__ = "reviews_features"
    
    id: Optional[int] = Field(default=None, primary_key=True, foreign_key="reviews_raw.id")
    text_length: int
    avg_word_length: float
    sentiment_score: float
    has_promo_keywords: bool
    user_review_count_last_30d: int
    same_ip_review_count_last_7d: Optional[int] = None
    
    review: Optional[ReviewRaw] = Relationship(back_populates="features")

class ReviewScore(SQLModel, table=True):
    __tablename__ = "reviews_score"
    
    id: Optional[int] = Field(default=None, primary_key=True, foreign_key="reviews_raw.id")
    trust_score: float
    is_suspicious: bool
    reasons: Optional[str] = None # Storing reasons as a simple string or JSON string
    model_version: str
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    
    review: Optional[ReviewRaw] = Relationship(back_populates="score")
