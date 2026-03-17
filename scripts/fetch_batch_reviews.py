import os
import sys
import hashlib
import argparse
from datetime import datetime
from sqlmodel import Session, select
from tenacity import RetryError

# Ensure app is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine
from app.models import ReviewRaw
from app.services.serpapi import SerpAPIService
from app.core.config import settings

def generate_review_hash(user: str, text: str, date_str: str) -> str:
    """Generate a unique hash for a review to prevent duplicates."""
    content = f"{user}:{text}:{date_str}"
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def is_valid_review(text: str) -> bool:
    """Filter out empty reviews or extremely short garbage."""
    if not text or not text.strip():
        return False
    # Basic check for minimum length (e.g., at least 3 characters)
    if len(text.strip()) < 3:
        return False
    return True

def fetch_and_store_reviews(data_ids: list[str], max_reviews_per_place: int = 100):
    service = SerpAPIService(api_key=settings.SERPAPI_KEY)
    
    total_fetched = 0
    total_inserted = 0

    with Session(engine) as session:
        for data_id in data_ids:
            print(f"Fetching reviews for Place Data ID: {data_id}...")
            try:
                place_info, reviews = service.fetch_reviews(data_id=data_id, num=max_reviews_per_place)
            except RetryError as e:
                print(f"Failed to fetch reviews for {data_id} after retries: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error for {data_id}: {e}")
                continue
            
            total_fetched += len(reviews)
            new_inserts = 0
            
            for r in reviews:
                text = r.get("text", "")
                if not is_valid_review(text):
                    continue
                
                author = r.get("author", "Anonymous")
                date_str = r.get("date", "")
                
                # Deduplication logic
                review_hash = generate_review_hash(author, text, date_str)
                
                # Check if exists
                stmt = select(ReviewRaw).where(ReviewRaw.external_review_id == review_hash)
                existing = session.exec(stmt).first()
                if existing:
                    continue
                
                # Parse date if possible, else use current time
                created_at = datetime.utcnow()
                iso_date = r.get("iso_date")
                if iso_date:
                    try:
                        # Some iso_date might end with Z
                        created_at = datetime.fromisoformat(iso_date.replace("Z", "+00:00")).replace(tzinfo=None)
                    except ValueError:
                        pass
                
                review = ReviewRaw(
                    platform="Google Maps",
                    external_review_id=review_hash,
                    user_id=author,
                    rating=r.get("rating", 0),
                    text=text,
                    created_at=created_at
                )
                session.add(review)
                new_inserts += 1
            
            session.commit()
            total_inserted += new_inserts
            print(f"  -> Inserted {new_inserts} new valid reviews out of {len(reviews)} fetched for {place_info.get('name', 'Unknown')}.")
    
    print(f"\nBatch Job Complete: Total Fetched={total_fetched}, Total Inserted={total_inserted}")

def main():
    parser = argparse.ArgumentParser(description="Batch fetch Google Maps reviews via SerpAPI.")
    parser.add_argument("--data-ids", nargs="+", required=True, help="List of Google Maps data_ids")
    parser.add_argument("--max-reviews", type=int, default=100, help="Maximum number of reviews per place to fetch")
    args = parser.parse_args()
    
    fetch_and_store_reviews(args.data_ids, args.max_reviews)

if __name__ == "__main__":
    main()
