import pytest
from app.services.inference import ModelService

def test_inference_rule_score_only():
    service = ModelService()
    # Force fallback
    service.model = None

    features = {
        "text_length": 15,
        "sentiment_score": 0.9,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 6
    }
    
    trust_prob, is_suspicious, reasons, rule_score, _ = service.predict(features, text="Good free gift")
    
    assert trust_prob < 1.0
    assert rule_score <= 1.0
    assert "Contains promotional keywords." in reasons
    assert is_suspicious == (trust_prob < 0.5)

def test_inference_with_ml_model():
    service = ModelService()
    service.load_model()
    
    features = {
        "text_length": 50,
        "sentiment_score": 0.2,
        "has_promo_keywords": False,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.1
    }
    
    trust_prob, is_suspicious, reasons, rule_score, model_score = service.predict(features, text="Normal review text without any promo stuff.")
    
    if service.model:
        assert len(reasons) == 0 or "ML model flagged as suspicious" in reasons
        assert trust_prob == (rule_score + model_score) / 2
    else:
        assert trust_prob == rule_score
