import pytest
from unittest.mock import patch
from app.services.inference import ModelService


def test_inference_rule_score_only():
    """Fallback to pure rule score when no ML model loaded. Returns 7 values."""
    service = ModelService()
    service.model = None

    features = {
        "text_length": 15,
        "sentiment_score": 0.9,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 6,
    }

    trust_prob, is_suspicious, reasons, rule_score, _, llm_verdict, llm_reasoning = \
        service.predict(features, text="Good free gift")

    assert trust_prob < 1.0
    assert rule_score <= 1.0
    assert "Contains promotional keywords." in reasons
    assert is_suspicious == (trust_prob < 0.5)


def test_llm_not_called_for_clear_cases():
    """LLM judge must NOT be called when score is clearly above 0.70."""
    service = ModelService()
    service.model = None

    # No flags → rule_score = 1.0, trust_prob = 1.0 → above 0.70
    features_clean = {
        "text_length": 80,
        "sentiment_score": 0.1,
        "has_promo_keywords": False,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.0,
    }

    with patch("app.services.inference.llm_judge_service.judge") as mock_judge:
        trust_prob, _, _, _, _, llm_verdict, llm_reasoning = \
            service.predict(features_clean, text="Fine dining experience.")
        mock_judge.assert_not_called()

    assert llm_verdict is None
    assert llm_reasoning is None


def test_llm_called_for_borderline_cases():
    """LLM judge IS called when hybrid score is in 0.30–0.70."""
    service = ModelService()
    service.model = None

    # has_promo_keywords=True → rule_score = 0.7 (1.0 - 0.3), no ML → trust_prob = 0.7
    # 0.7 is exactly on the upper boundary → should call LLM
    features_borderline = {
        "text_length": 50,
        "sentiment_score": 0.2,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.1,
    }

    mock_result = {"verdict": "fake", "reasoning": "模板化用語。"}

    with patch("app.services.inference.llm_judge_service.judge", return_value=mock_result) as mock_judge:
        trust_prob, _, _, _, _, llm_verdict, llm_reasoning = \
            service.predict(features_borderline, text="Great place! Highly recommend!")
        mock_judge.assert_called_once()

    assert llm_verdict == "fake"
    assert llm_reasoning == "模板化用語。"


def test_llm_unavailable_does_not_break_predict():
    """If Ollama is down, predict() still returns a valid result with None llm fields."""
    service = ModelService()
    service.model = None

    features_borderline = {
        "text_length": 50,
        "sentiment_score": 0.2,
        "has_promo_keywords": True,
        "user_review_count_last_30d": 1,
        "semantic_promo_score": 0.1,
    }

    with patch("app.services.inference.llm_judge_service.judge", return_value=None):
        trust_prob, is_suspicious, reasons, rule_score, model_score, llm_verdict, llm_reasoning = \
            service.predict(features_borderline, text="Great place!")

    assert isinstance(trust_prob, float)
    assert llm_verdict is None
    assert llm_reasoning is None
