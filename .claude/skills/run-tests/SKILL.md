---
name: run-tests
description: Use when running test suite, verifying code changes, debugging test failures, or checking code quality
---

# Running Tests

## Overview
Execute the pytest test suite for the Review Trust Analyzer using **uv**. Tests cover API endpoints, feature extraction, and batch processing functionality.

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
uv run pytest
```

### 2. Run with Verbose Output
```bash
uv run pytest -v
```

### 3. Run with Coverage Report
```bash
uv run pytest --cov=app --cov=features --cov=ml --cov-report=term-missing
```

## Test Suite Structure

```
tests/
├── test_api.py              # FastAPI endpoint tests
├── test_features.py         # Feature extraction tests
├── test_places.py           # Place Analysis API tests
└── test_batch_manual.py     # Batch processing tests
```

## Running Specific Tests

**Single test file:**
```bash
uv run pytest tests/test_api.py
```

**Single test function:**
```bash
uv run pytest tests/test_api.py::test_score_review -v
```

**Tests matching pattern:**
```bash
uv run pytest -k "batch" -v
```

**Stop on first failure:**
```bash
uv run pytest -x
```

## Debugging Failed Tests

```bash
# Detailed output
uv run pytest tests/test_api.py::test_score_review -vv -s

# Enter debugger on failure
uv run pytest --pdb

# Show print statements
uv run pytest -s
```

## Integration Tests

**With running server:**
```bash
# Terminal 1: Start server
uv run uvicorn app.main:app --port 8001

# Terminal 2: Test endpoint
curl -X POST http://localhost:8001/places/analyze \
  -H 'Content-Type: application/json' \
  -d '{"query": "測試店名"}'
```

## Common Test Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Import errors | Missing dependencies | `uv sync` |
| Model not found | ml/model.pkl missing | `uv run python ml/train.py` |
| Flaky sentiment tests | TextBlob download | `uv run python -m textblob.download_corpora` |

## Quality Checks

**Before committing:**
```bash
uv run pytest                    # All tests pass
uv run pytest -W error           # No warnings
uv run pytest --cov=app          # Coverage report
```

## Quick Reference

```bash
# Minimal (fast)
uv run pytest

# Standard (before commit)
uv run pytest -v

# Comprehensive (before PR)
uv run pytest -v --cov=app --cov=features --cov-report=term-missing

# Debug specific test
uv run pytest tests/test_api.py::test_score_review -vv -s --pdb
```
