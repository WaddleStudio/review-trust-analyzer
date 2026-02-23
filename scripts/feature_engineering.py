import os
import sys
from sqlmodel import Session, select
from sqlalchemy.orm import aliased
import json

# Ensure app is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import ReviewRaw, ReviewFeatures
from features.text_features import extract_text_features
from features.semantic_features import calculate_semantic_promo_score
from features.user_behavior_features import get_user_stats

def compute_and_store_features(batch_size: int = 1000):
    print(f"Starting feature engineering job (batch_size={batch_size})...")
    
    with Session(engine) as session:
        # Find raw reviews without features inserted yet
        subq = select(ReviewFeatures.id)
        stmt = select(ReviewRaw).where(ReviewRaw.id.not_in(subq)).limit(batch_size)
        unprocessed = session.exec(stmt).all()
        
        print(f"Found {len(unprocessed)} unprocessed reviews for feature engineering.")
        
        count = 0
        for rv in unprocessed:
            text = rv.text or ""
            
            # Structural & Sentiment Features
            t_feats = extract_text_features(text)
            
            # Semantic Features
            semantic_score = calculate_semantic_promo_score(text)
            
            # Behavioral Features
            u_feats = get_user_stats(rv.user_id, session, rv.rating)
            
            feature_row = ReviewFeatures(
                id=rv.id,
                text_length=t_feats.get("text_length", 0),
                avg_word_length=t_feats.get("avg_word_length", 0.0),
                sentiment_score=t_feats.get("sentiment_score", 0.0),
                has_promo_keywords=t_feats.get("has_promo_keywords", False),
                semantic_promo_score=semantic_score,
                user_review_count_last_30d=u_feats.get("user_review_count_last_30d", 1),
                same_ip_review_count_last_7d=u_feats.get("same_ip_review_count_last_7d", 0),
                rating_deviation_from_avg=u_feats.get("rating_deviation_from_avg", 0.0),
                is_extreme_rater=u_feats.get("is_extreme_rater", False)
            )
            
            session.add(feature_row)
            count += 1
            
        session.commit()
        print(f"Feature engineering complete. Inserted features for {count} reviews.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()
    compute_and_store_features(args.batch_size)
