import pickle
import os
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from ml.train import generate_synthetic_data, MODEL_PATH

def evaluate_model():
    if not os.path.exists(MODEL_PATH):
        print("Model not found. Please run train.py first.")
        return

    print("Loading model...")
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)

    print("Generating test data...")
    df = generate_synthetic_data(n_samples=200) # New data
    X = df[["text_length", "avg_word_length", "sentiment_score", "has_promo_keywords", "user_review_count_last_30d"]]
    y = df["is_suspicious"]

    print("Predicting...")
    y_pred = model.predict(X)

    print("\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {accuracy_score(y, y_pred):.4f}")
    print(f"Precision: {precision_score(y, y_pred):.4f}")
    print(f"Recall:    {recall_score(y, y_pred):.4f}")
    print(f"F1 Score:  {f1_score(y, y_pred):.4f}")

    print("\n--- Confusion Matrix ---")
    cm = confusion_matrix(y, y_pred)
    print(f"TN: {cm[0][0]}  FP: {cm[0][1]}")
    print(f"FN: {cm[1][0]}  TP: {cm[1][1]}")

if __name__ == "__main__":
    evaluate_model()
