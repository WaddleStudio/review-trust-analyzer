import os
import sys
from sqlmodel import Session, select
from sqlalchemy.orm import aliased
import json

# Ensure app is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import ReviewRaw, LabelingTask
from features.text_features import extract_text_features
from features.user_behavior_features import get_user_stats
from app.services.inference import model_service

def generate_pre_labels(batch_size: int = 500):
    """
    Generate pre-labels for unprocessed reviews in `reviews_raw`.
    Reviews with scores > 0.85 are automatically labeled "real".
    Reviews with scores < 0.15 are automatically labeled "suspicious".
    Others are "pending" for human review.
    """
    print(f"Starting pre-labeling job (batch_size={batch_size})...")
    
    with Session(engine) as session:
        # Find reviews that don't have a task yet
        # We can do an outer join or subquery
        subq = select(LabelingTask.source_id)
        stmt = select(ReviewRaw).where(ReviewRaw.external_review_id.not_in(subq)).limit(batch_size)
        
        pending_reviews = session.exec(stmt).all()
        print(f"Found {len(pending_reviews)} unprocessed reviews.")
        
        new_tasks = 0
        for review in pending_reviews:
            # 1. Feature extraction
            text_feats = extract_text_features(review.text)
            user_feats = get_user_stats(review.user_id, session, review.rating)
            all_feats = {**text_feats, **user_feats}
            
            # 2. Pre-label scoring
            trust_score, is_suspicious, reasons, rule_score, model_score = model_service.predict(all_feats, text=review.text)
            
            # 3. Determine label and status
            pre_label = None
            human_label = None
            status = "pending"
            
            if trust_score > 0.85:
                pre_label = "real"
                human_label = "real"
                status = "labeled"
            elif trust_score < 0.15:
                pre_label = "suspicious"
                human_label = "suspicious"
                status = "labeled"
            else:
                pre_label = "suspicious" if trust_score < 0.5 else "real"
                status = "pending"
            
            content_json = {
                "text": review.text,
                "author": review.user_id,
                "rating": review.rating,
                "date": review.created_at.isoformat() if review.created_at else None
            }
            
            task = LabelingTask(
                project_type="review_trust",
                source_id=review.external_review_id,
                content_json=content_json,
                pre_label=pre_label,
                pre_confidence=trust_score if pre_label == "real" else 1 - trust_score,
                human_label=human_label,
                status=status
            )
            session.add(task)
            new_tasks += 1
            
        session.commit()
        print(f"Pre-labeling complete. Created {new_tasks} new labeling tasks.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    generate_pre_labels(args.batch_size)
