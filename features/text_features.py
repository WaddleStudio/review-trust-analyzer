import re

# Expanded keywords based on NLP analysis (WordNet) + Manual curation
PROMO_KEYWORDS = [
    # English
    "gift", "discount", "promo", "free", "offer", "coupon", "voucher", "deal", "sale", 
    "rebate", "gratis", "complimentary", "giveaway", "bonus", "bargain", "special", 
    "cut-rate", "markdown", "clearance",
    # Chinese
    "送禮", "折扣", "優惠", "免費", "促銷", "特價", "好康", "抽獎", "贈送", "禮物", "折抵"
]

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
    
    # Sentiment Score using TextBlob
    from textblob import TextBlob
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity
        
    return {
        "text_length": text_length,
        "avg_word_length": avg_word_length,
        "sentiment_score": sentiment_score,
        "has_promo_keywords": has_promo
    }
