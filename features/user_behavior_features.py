from sqlmodel import Session, select
from sqlalchemy import func
from datetime import datetime, timedelta
import ssl
from app.models import ReviewRaw

def get_user_stats(user_id: str, db: Session = None, current_rating: float = None) -> dict:
    """
    Implementation of user behavior features by querying the database.
    """
    stats = {
        "user_review_count_last_30d": 1,
        "same_ip_review_count_last_7d": 0,
        "rating_deviation_from_avg": 0.0,
        "is_extreme_rater": False
    }
    
    if current_rating is not None:
        stats["is_extreme_rater"] = (current_rating == 1 or current_rating == 5)
        
    if not db or user_id == "Anonymous" or user_id == "anonymous":
        return stats
        
    try:
        # Count reviews in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        query_count = select(func.count(ReviewRaw.id)).where(
            ReviewRaw.user_id == user_id, 
            ReviewRaw.created_at >= thirty_days_ago
        )
        count = db.exec(query_count).one()
        stats["user_review_count_last_30d"] = count if count > 0 else 1
        
        # Calculate rating deviation
        if current_rating is not None:
            query_avg = select(func.avg(ReviewRaw.rating)).where(ReviewRaw.user_id == user_id)
            avg_rating = db.exec(query_avg).one()
            if avg_rating is not None:
                stats["rating_deviation_from_avg"] = float(abs(current_rating - avg_rating))
                
    except Exception as e:
        print(f"Error querying user stats for {user_id}: {e}")
        
    return stats
