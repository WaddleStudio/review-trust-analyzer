import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import engine
from app.models import ReviewFeatures, LabelingTask, ReviewRaw
from sqlmodel import Session, select

# Models to train
MODELS = {
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced"),
    "GradientBoosting": GradientBoostingClassifier(n_estimators=100, random_state=42),
    "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
}

FEATURE_COLS = [
    "text_length",
    "avg_word_length",
    "sentiment_score",
    "has_promo_keywords",
    "semantic_promo_score",
    "user_review_count_last_30d",
    "same_ip_review_count_last_7d",
    "rating_deviation_from_avg",
    "is_extreme_rater"
]

def load_data():
    """Load labeled data from DB"""
    print("Loading data from database...")
    with Session(engine) as session:
        # Get tasks that have human_label (either manually labeled or pre-labeled confidently)
        # Assuming we treat all 'real' / 'suspicious' human_labels as truth.
        stmt = select(LabelingTask, ReviewFeatures).join(
            ReviewFeatures, LabelingTask.source_id == ReviewRaw.external_review_id # Need joining via ReviewRaw to get Features.
        )
        
        # Proper JOIN: LabelingTask -> ReviewRaw (via source_id=external_review_id) -> ReviewFeatures (via id=id)
        stmt = select(LabelingTask.human_label, ReviewFeatures).join(
            ReviewRaw, LabelingTask.source_id == ReviewRaw.external_review_id
        ).join(
            ReviewFeatures, ReviewRaw.id == ReviewFeatures.id
        ).where(LabelingTask.human_label != None)
        
        results = session.exec(stmt).all()
        
    if not results:
        print("No labeled data found!")
        return pd.DataFrame(), pd.Series()
        
    features_list = []
    labels_list = []
    
    for label, feats in results:
        # Encode labels: suspicious = 1, real = 0
        y = 1 if label == "suspicious" else 0
        x = {
            "text_length": feats.text_length,
            "avg_word_length": feats.avg_word_length,
            "sentiment_score": feats.sentiment_score,
            "has_promo_keywords": int(feats.has_promo_keywords),
            "semantic_promo_score": feats.semantic_promo_score,
            "user_review_count_last_30d": feats.user_review_count_last_30d,
            "same_ip_review_count_last_7d": feats.same_ip_review_count_last_7d or 0,
            "rating_deviation_from_avg": feats.rating_deviation_from_avg,
            "is_extreme_rater": int(feats.is_extreme_rater)
        }
        features_list.append(x)
        labels_list.append(y)
        
    X = pd.DataFrame(features_list)
    y = pd.Series(labels_list)
    print(f"Loaded {len(y)} labeled records.")
    return X, y

def split_data(X, y):
    # 70/15/15 roughly achieved by 70/30 then 50/50 of the 30
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)
    return X_train, X_val, X_test, y_train, y_val, y_test

def evaluate(model, X_val, y_val):
    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)[:, 1] if hasattr(model, "predict_proba") else preds
    
    return {
        "precision": precision_score(y_val, preds, zero_division=0),
        "recall": recall_score(y_val, preds, zero_division=0),
        "f1": f1_score(y_val, preds, zero_division=0),
        "auc": roc_auc_score(y_val, probs)
    }

def train_and_evaluate(X_train, X_val, y_train, y_val):
    results = {}
    best_model_name = None
    best_score = -1
    
    print("Training models...")
    for name, model in MODELS.items():
        model.fit(X_train, y_train)
        metrics = evaluate(model, X_val, y_val)
        results[name] = metrics
        
        print(f"[{name}] Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}, F1: {metrics['f1']:.4f}, AUC: {metrics['auc']:.4f}")
        
        # Precision priority strategy: combine precision strongly
        score = metrics['precision'] * 0.7 + metrics['f1'] * 0.3
        if score > best_score:
            best_score = score
            best_model_name = name
            
    return best_model_name, results

def serialize(model, path="verification/model_artifacts/v2_rf_model.pkl"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"Model saved to {path}")

def generate_report(best_name, results, model, X_test, y_test, path="verification/model_artifacts/report.md"):
    test_metrics = evaluate(model, X_test, y_test)
    preds = model.predict(X_test)
    cm = confusion_matrix(y_test, preds)
    
    report = f"""# Model Training Report
Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Validation Results
"""
    for name, m in results.items():
        report += f"- **{name}**: P={m['precision']:.4f}, R={m['recall']:.4f}, F1={m['f1']:.4f}, AUC={m['auc']:.4f}\n"
        
    report += f"""
## Selected Model (Precision Strategy)
Winning Model: **{best_name}**

### Test Set Performance (15%)
- Precision: {test_metrics['precision']:.4f}
- Recall: {test_metrics['recall']:.4f}
- F1 Score: {test_metrics['f1']:.4f}
- AUC-ROC: {test_metrics['auc']:.4f}

### Confusion Matrix (Test Set)
| | Predicted Real (0) | Predicted Suspicious (1) |
|---|---|---|
| **Actual Real (0)** | {cm[0][0]} | {cm[0][1]} |
| **Actual Suspicious (1)** | {cm[1][0]} | {cm[1][1]} |
"""

    if hasattr(model, "feature_importances_"):
        importances = pd.Series(model.feature_importances_, index=FEATURE_COLS).sort_values(ascending=False)
        report += "\n### Feature Importances\n"
        for feat, imp in importances.items():
            report += f"- {feat}: {imp:.4f}\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved to {path}")

def main():
    X, y = load_data()
    if X.empty:
        return
        
    # Minimum rows to split
    if len(y) < 20:
        print("Not enough data to train. Need at least 20 labeled examples.")
        return
        
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(X, y)
    
    best_name, val_results = train_and_evaluate(X_train, X_val, y_train, y_val)
    print(f"\nBest model selected: {best_name}")
    
    best_model = MODELS[best_name]
    serialize(best_model)
    generate_report(best_name, val_results, best_model, X_test, y_test)

if __name__ == "__main__":
    main()
