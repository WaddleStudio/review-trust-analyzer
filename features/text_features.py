import re

PROMO_KEYWORDS = ["gift", "discount", "promo", "free", "offer", "coupon", "vouchar", "送禮", "折扣", "優惠", "免費"]

def extract_text_features(text: str) -> dict:
    if not text:
        return {
            "text_length": 0,
            "avg_word_length": 0.0,
            "sentiment_score": 0.0,
            "has_promo_keywords": False
        }
    
    # Text length
    text_length = len(text)
    
    # Average word length
    words = text.split()
    avg_word_length = sum(len(w) for w in words) / len(words) if words else 0.0
    
    # Promo keywords
    text_lower = text.lower()
    has_promo = any(keyword in text_lower for keyword in PROMO_KEYWORDS)
    
    # Simple Sentiment Score (Mock logic: longer text + high rating usually positive, but here we only have text)
    # Let's just use a very naive approach: 
    # Positive words: good, great, excellent, amazing, love, best
    # Negative words: bad, terrible, awful, worst, hate, poor
    positive_words = ["good", "great", "excellent", "amazing", "love", "best", "好", "棒", "讚"]
    negative_words = ["bad", "terrible", "awful", "worst", "hate", "poor", "差", "爛"]
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    # Normalize to -1 to 1 roughly
    total = pos_count + neg_count
    if total > 0:
        sentiment_score = (pos_count - neg_count) / total
    else:
        sentiment_score = 0.0
        
    return {
        "text_length": text_length,
        "avg_word_length": avg_word_length,
        "sentiment_score": sentiment_score,
        "has_promo_keywords": has_promo
    }
