from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

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
    semantic_promo_score: float = Field(default=0.0)
    rating_deviation_from_avg: float = Field(default=0.0)
    is_extreme_rater: bool = Field(default=False)
    
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

class LabelingTask(SQLModel, table=True):
    __tablename__ = "labeling_tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_type: str = Field(default="review_trust", max_length=50)
    source_id: str = Field(max_length=255)
    content_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    pre_label: Optional[str] = Field(default=None, max_length=20)
    pre_confidence: Optional[float] = None
    human_label: Optional[str] = Field(default=None, max_length=20)
    status: str = Field(default="pending", max_length=20)   # pending, labeled, skipped
    labeled_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
