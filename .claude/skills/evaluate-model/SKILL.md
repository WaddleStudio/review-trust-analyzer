---
name: evaluate-model
description: Use when assessing model performance, comparing versions, or analyzing classification metrics
---

# Model Performance Evaluation

## Overview
Evaluate the trained Logistic Regression model's performance using detailed classification metrics. Generates confusion matrix, precision/recall/F1 scores, and identifies areas for improvement.

## When to Use
- After training a new model
- Before deploying to production
- Comparing different model versions
- Investigating false positive/negative rates
- Debugging poor prediction quality
- Performance regression testing

## Core Workflow

### 1. Run Evaluation Script
```bash
python ml/evaluate.py
```

### 2. Review Metrics
The script outputs:
- **Accuracy**: Overall correctness (TP+TN)/(TP+TN+FP+FN)
- **Precision**: True positives / (TP + FP) - "How many flagged reviews are actually suspicious?"
- **Recall**: True positives / (TP + FN) - "How many suspicious reviews did we catch?"
- **F1 Score**: Harmonic mean of precision and recall
- **Confusion Matrix**: Visual breakdown of predictions

### 3. Interpret Results

**Example output:**
```
Model Evaluation Results
========================
Accuracy:  0.91 (91%)
Precision: 1.00 (100%)
Recall:    0.47 (47%)
F1 Score:  0.64

Confusion Matrix:
                Predicted Negative  Predicted Positive
Actual Negative               540                   0
Actual Positive               240                 220
```

## Understanding Metrics

### Accuracy (91%)
- Overall correctness across all predictions
- **Good for:** Balanced datasets
- **Misleading when:** Imbalanced classes (e.g., 95% genuine, 5% fake)

### Precision (100%)
- When we flag a review as suspicious, we're always right
- **High precision = Low false positive rate**
- Critical for user trust (don't want to incorrectly flag genuine reviews)

### Recall (47%)
- We catch 47% of actual suspicious reviews
- **Low recall = Missing many fake reviews (false negatives)**
- Room for improvement: Add more features or use better model

### F1 Score (0.64)
- Balance between precision and recall
- Useful when you care about both metrics equally

## Baseline Performance

**Current model (v0.1.0 - Logistic Regression):**
- Accuracy: 91%
- Precision: 100%
- Recall: 47%
- Training: Synthetic data (1000 samples)

**Targets for v0.2.0+:**
- Accuracy: > 93%
- Precision: > 95% (allow some false positives)
- Recall: > 70% (catch more fake reviews)
- Training: Real labeled data + synthetic augmentation

## Improving Performance

### Low Recall (< 50%)
**Causes:**
- Conservative model (high threshold)
- Weak features (not capturing fake review patterns)
- Limited training data

**Solutions:**
1. Add more features (user behavior, temporal patterns)
2. Adjust classification threshold: `model.predict_proba()` → lower cutoff
3. Use more sophisticated model (XGBoost, Random Forest)
4. Collect more labeled training data

### Low Precision (< 90%)
**Causes:**
- Aggressive model (low threshold)
- Features with false correlations
- Overfitting to promotional keywords

**Solutions:**
1. Increase classification threshold
2. Remove noisy features
3. Add regularization (increase C parameter in Logistic Regression)
4. Implement contrastive semantic analysis (already done in v0.1.0)

### Imbalanced Classes
**If genuine:fake ratio is 95:5:**
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(class_weight='balanced')  # Automatic reweighting
# or
model = LogisticRegression(class_weight={0: 1, 1: 19})  # Manual weights
```

## Detailed Evaluation

**Generate comprehensive report:**
```python
python ml/evaluate.py --detailed
```

**Outputs:**
- Per-class precision/recall/F1
- ROC curve (Receiver Operating Characteristic)
- Precision-Recall curve
- Feature importance (top predictive features)

**Analyze feature importance:**
```python
import joblib
import pandas as pd

model = joblib.load('ml/model.pkl')
feature_names = ['text_length', 'avg_word_length', 'sentiment_score',
                 'has_promo_keywords', 'semantic_promo_score']

importance = pd.DataFrame({
    'feature': feature_names,
    'coefficient': model.coef_[0]
}).sort_values('coefficient', ascending=False)

print(importance)
```

## Comparing Model Versions

**Save evaluation results:**
```bash
python ml/evaluate.py > results_v0.1.0.txt
# After retraining:
python ml/evaluate.py > results_v0.2.0.txt
diff results_v0.1.0.txt results_v0.2.0.txt
```

**Track metrics over time:**
```python
# evaluation_history.csv
version,accuracy,precision,recall,f1,date
v0.1.0,0.91,1.00,0.47,0.64,2025-01-15
v0.2.0,0.93,0.98,0.72,0.83,2025-01-20
```

## Common Evaluation Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Evaluation fails | No test data | Script generates test set automatically |
| Metrics = 0 | Model predicts all negative | Check model loading, retrain |
| Perfect scores (100%) | Overfitting or data leakage | Use separate test set, not training data |
| Inconsistent results | Random seed not set | Set `random_state=42` in train/test split |

## Real-World Performance Testing

**Test on actual reviews:**
```python
import pandas as pd
import requests

# Load real reviews with manual labels
df = pd.read_csv('data/labeled_reviews.csv')

for _, row in df.iterrows():
    response = requests.post('http://localhost:8000/reviews/score', json={
        'text': row['text'],
        'rating': row['rating'],
        'platform': row['platform'],
        'user_id': row['user_id']
    })
    predicted = response.json()['is_suspicious']
    actual = row['is_fake']

    if predicted != actual:
        print(f"MISMATCH: {row['text'][:50]}...")
        print(f"  Predicted: {predicted}, Actual: {actual}")
```

## Quick Reference

```bash
# Basic evaluation
python ml/evaluate.py

# Detailed with visualizations
python ml/evaluate.py --detailed --plot

# Test on specific dataset
python ml/evaluate.py --test-file data/labeled_reviews.csv

# Compare with baseline
python ml/evaluate.py > eval_results.txt
```

## Real-World Impact

Proper evaluation ensures:
- **High precision** → Users trust the system (few false alarms)
- **High recall** → Catch most fake reviews (protect business reputation)
- **Balanced F1** → Good overall performance
- **Continuous improvement** → Track progress across versions

**Example:** Improving recall from 47% → 75% means catching 50% more fake reviews, potentially saving thousands in revenue loss from fraudulent manipulation.

**Next steps for improvement:**
1. Collect 1000+ real labeled reviews
2. Implement XGBoost model (expected +10-15% recall)
3. Add user behavior features (review velocity, profile age)
4. Deploy A/B testing to compare models in production
