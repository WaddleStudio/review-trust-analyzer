import pandas as pd
import numpy as np
import pickle
import os
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")

def generate_synthetic_data(n_samples=1000):
    np.random.seed(42)
    
    data = {
        "text_length": np.random.randint(10, 500, n_samples),
        "avg_word_length": np.random.uniform(3, 8, n_samples),
        "sentiment_score": np.random.uniform(-1, 1, n_samples),
        "has_promo_keywords": np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
        "user_review_count_last_30d": np.random.poisson(2, n_samples),
        "rating": np.random.randint(1, 6, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    # Define logic for suspicious reviews (Ground Truth for training)
    # Suspicious if:
    # 1. Has promo keywords
    # 2. High user review count (> 5)
    # 3. Extreme rating (1 or 5) AND very short text (< 20)
    
    def is_suspicious(row):
        score = 0
        if row["has_promo_keywords"]:
            score += 3
        if row["user_review_count_last_30d"] > 5:
            score += 2
        if (row["rating"] == 1 or row["rating"] == 5) and row["text_length"] < 20:
            score += 1
            
        # Add some noise
        if np.random.random() < 0.05:
            score += 2
            
        return 1 if score >= 2 else 0

    df["is_suspicious"] = df.apply(is_suspicious, axis=1)
    
    return df

def train_model():
    print("Generating synthetic data...")
    df = generate_synthetic_data()
    
    X = df[["text_length", "avg_word_length", "sentiment_score", "has_promo_keywords", "user_review_count_last_30d"]]
    y = df["is_suspicious"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Logistic Regression model...")
    model = LogisticRegression()
    model.fit(X_train, y_train)
    
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    print(f"Saving model to {MODEL_PATH}...")
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print("Done.")

if __name__ == "__main__":
    train_model()
