import pytest
from features.text_features import extract_text_features

def test_extract_text_features_basic():
    text = "This is a good product."
    features = extract_text_features(text)
    
    assert features["text_length"] == 23
    assert features["avg_word_length"] > 0
    assert features["sentiment_score"] > 0 # 'good' is positive
    assert features["has_promo_keywords"] is False

def test_extract_text_features_promo():
    text = "Get a free gift now!"
    features = extract_text_features(text)
    
    assert features["has_promo_keywords"] is True

def test_extract_text_features_empty():
    features = extract_text_features("")
    assert features["text_length"] == 0
    assert features["avg_word_length"] == 0.0
    assert features["sentiment_score"] == 0.0
    assert features["has_promo_keywords"] is False
