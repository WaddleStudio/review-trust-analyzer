import pickle
import os
import numpy as np
from app.core.config import settings

# Path to the model
MODEL_PATH = os.path.join(os.getcwd(), "ml", "model.pkl")

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

    def predict(self, features: dict, text: str = "") -> tuple[float, bool, list[str]]:
        if not self.model:
            # Fallback or error
            return 0.5, False, ["Model not loaded"]
        
        # Calculate semantic promo score
        semantic_score = calculate_semantic_promo_score(text)
        
        # Prepare feature vector
        # Order must match training: "text_length", "avg_word_length", "sentiment_score", "has_promo_keywords", "user_review_count_last_30d"
        import pandas as pd
        feature_vector = pd.DataFrame([{
            "text_length": features["text_length"],
            "avg_word_length": features["avg_word_length"],
            "sentiment_score": features["sentiment_score"],
            "has_promo_keywords": int(features["has_promo_keywords"]),
            "user_review_count_last_30d": features["user_review_count_last_30d"]
        }])
        
        # Predict probability
        trust_prob = self.model.predict_proba(feature_vector)[0][0] # Prob of class 0 (Not Suspicious) -> Trust Score
        is_suspicious = bool(self.model.predict(feature_vector)[0])
        
        # Hybrid Logic: Combine ML result with Semantic Score
        # If semantic score is high (> 0.6), force suspicious even if ML missed it
        if semantic_score > 0.6:
            is_suspicious = True
            trust_prob = min(trust_prob, 0.3) # Penalize trust score
        
        # Generate reasons (Simple rule-based explanation)
        reasons = []
        if features["has_promo_keywords"]:
            reasons.append("Contains promotional keywords.")
        if features["user_review_count_last_30d"] > 5:
            reasons.append("High volume of reviews from user recently.")
        if features["text_length"] < 20 and (features["sentiment_score"] > 0.8 or features["sentiment_score"] < -0.8):
            reasons.append("Short text with extreme sentiment.")
        if semantic_score > 0.6:
            reasons.append(f"Semantically similar to promotional content (Score: {semantic_score:.2f}).")
            
        if is_suspicious and not reasons:
            reasons.append("Pattern matches suspicious activity.")
            
        return trust_prob, is_suspicious, reasons

model_service = ModelService()
