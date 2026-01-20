---
name: run-tests
description: Use when running test suite, verifying code changes, debugging test failures, or checking code quality
---

# Running Tests

## Overview
Execute the pytest test suite for the Review Trust Analyzer. Tests cover API endpoints, feature extraction, and batch processing functionality.

## When to Use
- Before committing code changes
- After modifying API endpoints or feature engineering
- Debugging test failures in CI/CD
- Verifying bug fixes
- After dependency updates
- Before deploying to production

## Core Workflow

### 1. Run All Tests
```bash
python -m pytest
```

### 2. Run with Verbose Output
```bash
python -m pytest -v
```

### 3. Run with Coverage Report
```bash
python -m pytest --cov=app --cov=features --cov=ml --cov-report=term-missing
```

## Test Suite Structure

```
tests/
├── test_api.py              # FastAPI endpoint tests
│   ├── test_score_review()  # Single review scoring
│   ├── test_batch_upload()  # CSV batch processing
│   └── test_validation()    # Input validation
├── test_features.py         # Feature extraction tests
│   ├── test_text_features() # Text analysis
│   ├── test_semantic_promo()# Semantic similarity
│   └── test_sentiment()     # Sentiment scoring
└── test_batch_manual.py     # Manual batch processing tests
```

## Running Specific Tests

**Single test file:**
```bash
python -m pytest tests/test_api.py
```

**Single test function:**
```bash
python -m pytest tests/test_api.py::test_score_review -v
```

**Tests matching pattern:**
```bash
python -m pytest -k "batch" -v  # All tests with "batch" in name
```

**Stop on first failure:**
```bash
python -m pytest -x
```

## Understanding Test Output

**Good test run:**
```
tests/test_api.py::test_score_review PASSED        [ 33%]
tests/test_api.py::test_batch_upload PASSED        [ 66%]
tests/test_features.py::test_text_features PASSED  [100%]

============ 3 passed in 2.45s ============
```

**Failed test run:**
```
tests/test_api.py::test_score_review FAILED        [ 33%]

FAILED tests/test_api.py::test_score_review - AssertionError: assert 0.45 < 0.5
Expected trust_score < 0.5 for suspicious review, got 0.45
```

## Common Test Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Import errors | Missing dependencies | `pip install -r requirements.txt` |
| Model not found | ml/model.pkl missing | Run `python ml/train.py` first |
| Database errors | SQLite lock/connection | Tests use in-memory DB, check test fixtures |
| Hanging tests | Network requests | Mock external APIs, check for infinite loops |
| Flaky sentiment tests | TextBlob download | Run `python -m textblob.download_corpora` |

## Test Data

**Built-in test reviews:**
- English promotional: "Amazing! Free gifts! Highly recommend!"
- Chinese promotional: "超棒！免費贈品！強烈推薦！"
- Genuine reviews: "The food was good, service could be better."
- Edge cases: Empty text, extreme ratings, multilingual

**Using sample data:**
```bash
python -m pytest --csv-file=data/sample_reviews.csv
```

## Quality Checks

**Before committing, ensure:**
- [ ] All tests pass: `python -m pytest`
- [ ] No warnings: `python -m pytest -W error`
- [ ] Coverage > 80%: `python -m pytest --cov=app --cov-report=term-missing`
- [ ] No flaky tests (run 3x): `python -m pytest --count=3`

**CI/CD expectations:**
- Zero test failures
- No deprecation warnings
- Tests complete in < 30 seconds
- All critical paths covered

## Debugging Failed Tests

### 1. Run with detailed output
```bash
python -m pytest tests/test_api.py::test_score_review -vv -s
```

### 2. Enter debugger on failure
```bash
python -m pytest --pdb
```

### 3. Show print statements
```bash
python -m pytest -s  # Shows print() output
```

### 4. Inspect fixtures
```bash
python -m pytest --fixtures  # List all available fixtures
```

## Advanced Testing

**Parallel execution (faster):**
```bash
pip install pytest-xdist
python -m pytest -n auto  # Use all CPU cores
```

**Generate HTML report:**
```bash
pip install pytest-html
python -m pytest --html=report.html --self-contained-html
```

**Test performance profiling:**
```bash
pip install pytest-profiling
python -m pytest --profile
```

## Quick Reference

```bash
# Minimal (fast)
python -m pytest

# Standard (before commit)
python -m pytest -v

# Comprehensive (before PR)
python -m pytest -v --cov=app --cov=features --cov-report=term-missing

# Debug specific test
python -m pytest tests/test_api.py::test_score_review -vv -s --pdb
```

## Real-World Impact

Comprehensive testing ensures:
- API endpoints return correct trust scores
- Feature extraction handles edge cases (empty text, special characters)
- Batch processing works with large CSV files
- Multilingual support (English/Chinese) functions correctly
- No regression bugs when adding new features

**Current test coverage:** API endpoints (100%), feature extraction (95%), ML training (80%).
