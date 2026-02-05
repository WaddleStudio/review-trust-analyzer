---
name: train-model
description: Use when the ML model needs to be trained or retrained with updated data or parameters
---

# Training ML Model

## Overview
Train the Logistic Regression model for review trust analysis using **uv**. Generates synthetic training data, trains the model, and saves it to `ml/model.pkl`.

## When to Use
- Initial project setup (no model.pkl exists)
- Model performance degradation detected
- Feature engineering changes requiring retraining
- New training data available
- Experimenting with hyperparameters

## Core Workflow

### 1. Execute Training Script
```bash
uv run python ml/train.py
```

### 2. Expected Output
```
Training model...
Model saved to ml/model.pkl
Accuracy: 0.91
Precision: 1.00
Recall: 0.47
```

### 3. Verify Model Creation
```bash
ls -lh ml/model.pkl  # Should be ~10-50KB
```

## Quality Checks

**Good Training Run:**
- Model.pkl file created with recent timestamp
- Accuracy > 0.85
- No errors during training
- File size ~10-50KB

**Bad Training Run:**
- Training script crashes
- Accuracy < 0.70
- Model.pkl not created or 0 bytes

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| ImportError | Missing dependencies | `uv sync` |
| Model accuracy too low | Feature bug | Check `features/` modules |
| File not found | Wrong directory | Run from project root |

## Integration

**After training, test the model:**
```bash
# Start server
uv run uvicorn app.main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/reviews/score \
  -H 'Content-Type: application/json' \
  -d '{"text": "Amazing! Free gift!", "rating": 5, "platform": "google", "user_id": "test"}'
```

## Quick Reference

```bash
# Train model
uv run python ml/train.py

# Verify
ls -lh ml/model.pkl

# Evaluate
uv run python ml/evaluate.py
```
