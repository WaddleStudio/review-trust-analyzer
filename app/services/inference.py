import pickle
import os
import numpy as np
from app.core.config import settings

# Path to the model
MODEL_PATH = os.path.join(os.getcwd(), "verification", "model_artifacts", "v2_rf_model.pkl")

from features.semantic_features import calculate_semantic_promo_score

class ModelService:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            print(f"Model loaded from {MODEL_PATH}")
        else:
            print(f"Model not found at {MODEL_PATH}. Please run ml/train.py.")

    def predict(self, features: dict, text: str = "") -> tuple[float, bool, list[str], float, float]:
        # Simple Rule-based Engine Score (0 to 1, higher is more trustworthy)
        rule_score = 1.0
        reasons = []
        
        semantic_score = features.get("semantic_promo_score", calculate_semantic_promo_score(text))
        
        if features.get("has_promo_keywords", False):
            rule_score -= 0.3
            reasons.append("Contains promotional keywords.")
        if features.get("user_review_count_last_30d", 1) > 5:
            rule_score -= 0.2
            reasons.append("High volume of reviews from user recently.")
        if features.get("text_length", 0) < 20 and abs(features.get("sentiment_score", 0)) > 0.8:
            rule_score -= 0.2
            reasons.append("Short text with extreme sentiment.")
        if semantic_score > 0.6:
            rule_score -= 0.4
            reasons.append(f"Semantically similar to promotional content (Score: {semantic_score:.2f}).")
            
        rule_score = max(0.0, rule_score)

        if not self.model:
            # Fallback to pure rule score
            trust_prob = rule_score
            is_suspicious = trust_prob < 0.5
            if is_suspicious and not reasons:
                reasons.append("Pattern matches suspicious activity.")
            return trust_prob, is_suspicious, reasons, rule_score, rule_score
        
        import pandas as pd
        feature_vector = pd.DataFrame([{
            "text_length": features.get("text_length", 0),
            "avg_word_length": features.get("avg_word_length", 0.0),
            "sentiment_score": features.get("sentiment_score", 0.0),
            "has_promo_keywords": int(features.get("has_promo_keywords", False)),
            "semantic_promo_score": semantic_score,
            "user_review_count_last_30d": features.get("user_review_count_last_30d", 1),
            "same_ip_review_count_last_7d": features.get("same_ip_review_count_last_7d", 0),
            "rating_deviation_from_avg": features.get("rating_deviation_from_avg", 0.0),
            "is_extreme_rater": int(features.get("is_extreme_rater", False))
        }])
        
        # ML model predict
        try:
            # Predict probability of being "real" (class 0) -> trust score
            model_score = self.model.predict_proba(feature_vector)[0][0]
            ml_suspicious = bool(self.model.predict(feature_vector)[0])
        except Exception as e:
            print("Model prediction error:", e)
            model_score = rule_score
            ml_suspicious = rule_score < 0.5

        if ml_suspicious and "ML model flagged as suspicious" not in reasons:
            reasons.append("ML model flagged as suspicious.")

        # Aggregated hybrid score (50/50 for A/B comparison)
        trust_prob = (rule_score + model_score) / 2.0
        
        # Final decision based on hybrid
        is_suspicious = trust_prob < 0.5
        
        return trust_prob, is_suspicious, reasons, rule_score, model_score

model_service = ModelService()
