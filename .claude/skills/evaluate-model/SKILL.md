---
name: evaluate-model
description: Use when assessing model performance, comparing versions, or analyzing classification metrics
---

# Model Performance Evaluation

## Overview
Evaluate the trained model's performance using **uv**. Generates confusion matrix, precision/recall/F1 scores, and identifies areas for improvement.

## When to Use
- After training a new model
- Before deploying to production
- Comparing different model versions
- Investigating false positive/negative rates
- Debugging poor prediction quality

## Core Workflow

### 1. Run Evaluation Script
```bash
uv run python ml/evaluate.py
```

### 2. Review Metrics
- **Accuracy**: Overall correctness
- **Precision**: "How many flagged reviews are actually suspicious?"
- **Recall**: "How many suspicious reviews did we catch?"
- **F1 Score**: Balance of precision and recall

### 3. Example Output
```
Model Evaluation Results
========================
Accuracy:  0.91 (91%)
Precision: 1.00 (100%)
Recall:    0.47 (47%)
F1 Score:  0.64
```

## Understanding Metrics

| Metric | Current | Target | Meaning |
|--------|---------|--------|---------|
| Accuracy | 91% | > 93% | Overall correctness |
| Precision | 100% | > 95% | Low false positives |
| Recall | 47% | > 70% | Catching fake reviews |
| F1 | 0.64 | > 0.80 | Balance |

## Improving Performance

**Low Recall (< 50%):**
- Add more features
- Lower classification threshold
- Use XGBoost/Random Forest
- Collect more training data

**Low Precision (< 90%):**
- Increase threshold
- Remove noisy features
- Add regularization

## Comparing Versions

```bash
# Save results
uv run python ml/evaluate.py > results_v1.txt

# After changes
uv run python ml/evaluate.py > results_v2.txt

# Compare
diff results_v1.txt results_v2.txt
```

## Quick Reference

```bash
# Basic evaluation
uv run python ml/evaluate.py

# Detailed with plots (if implemented)
uv run python ml/evaluate.py --detailed --plot

# Save to file
uv run python ml/evaluate.py > evaluation_report.txt
```
