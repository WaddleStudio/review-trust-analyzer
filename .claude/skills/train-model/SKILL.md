---
name: train-model
description: Use when the ML model needs to be trained or retrained with updated data or parameters
---

# Training ML Model

## Overview
Train the Logistic Regression model for review trust analysis. This skill generates synthetic training data, trains the model, and saves it to `ml/model.pkl` for use by the inference API.

## When to Use
- Initial project setup (no model.pkl exists)
- Model performance degradation detected
- Feature engineering changes requiring retraining
- New training data available
- Experimenting with hyperparameters

## Core Workflow

### 1. Execute Training Script
```bash
python ml/train.py
```

### 2. Verify Model Creation
The script will:
- Generate synthetic training data (1000 samples)
- Extract features using feature engineering modules
- Train Logistic Regression classifier
- Save model to `ml/model.pkl`
- Display training metrics (accuracy, precision, recall)

### 3. Expected Output
```
Training model...
Model saved to ml/model.pkl
Accuracy: 0.91
Precision: 1.00
Recall: 0.47
```

## Quality Checks

**Good Training Run:**
- ✅ Model.pkl file created/updated with recent timestamp
- ✅ Accuracy > 0.85
- ✅ No errors or warnings during training
- ✅ File size reasonable (~10-50KB for sklearn models)

**Bad Training Run:**
- ❌ Training script crashes with ImportError
- ❌ Accuracy < 0.70 (check feature extraction)
- ❌ Model.pkl not created or has 0 bytes
- ❌ Memory errors with large datasets

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| ImportError: textblob | Missing dependencies | Run `pip install -r requirements.txt` |
| Model accuracy too low | Feature engineering bug | Check `features/` modules |
| File not found error | Wrong working directory | Ensure running from project root |
| Model.pkl not loading | Corrupted file | Delete and retrain |

## Integration Points

**After training, test the model:**
1. Start API: `python -m uvicorn app.main:app --reload`
2. Test endpoint: POST to `/reviews/score` with sample review
3. Check trust_score and is_suspicious fields in response

**When to retrain:**
- Weekly for production systems
- After adding new features to `features/` modules
- When false positive/negative rate increases
- When semantic_features.py model is updated

## Quick Reference

```bash
# Full workflow
cd d:\Projects\review-trust-analyzer
python ml/train.py
ls -lh ml/model.pkl  # Verify creation
python ml/evaluate.py  # Optional: detailed metrics
```

## Real-World Impact

The trained model powers the trust score calculation for all review analysis. A well-trained model means:
- Accurate fake review detection
- Lower false positive rate (genuine reviews marked as suspicious)
- Higher recall (catching actual promotional/fake reviews)
- Faster inference (simpler models = quicker predictions)

Current baseline: 91% accuracy, 100% precision, 47% recall using Logistic Regression on synthetic data.
