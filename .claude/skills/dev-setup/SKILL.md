---
name: dev-setup
description: Use when setting up local development environment for the first time or after clean checkout
---

# Development Environment Setup

## Overview
Complete setup workflow for the Review Trust Analyzer development environment. Installs dependencies, trains the ML model, and starts the FastAPI development server.

## When to Use
- Fresh clone of the repository
- New developer onboarding
- After `rm -rf .venv` or virtual environment corruption
- Switching between development machines
- After major dependency updates in requirements.txt

## Core Workflow

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

**What gets installed:**
- FastAPI + Uvicorn (web framework & server)
- SQLModel + databases (ORM & PostgreSQL/SQLite)
- Scikit-learn (ML model)
- TextBlob + sentence-transformers (NLP)
- Pytest + testing utilities

### 2. Train Initial Model
```bash
python ml/train.py
```

**Creates:** `ml/model.pkl` (Logistic Regression classifier)

### 3. Start Development Server
```bash
python -m uvicorn app.main:app --reload
```

**Access points:**
- Frontend UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/reviews/score (POST endpoint)

## Complete Setup Script

```bash
# Ensure you're in project root
cd d:\Projects\review-trust-analyzer

# Activate virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix/Mac:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLP models (happens automatically on first TextBlob/transformers use)
python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Train ML model
python ml/train.py

# Verify installation
python -m pytest tests/ -v

# Start server
python -m uvicorn app.main:app --reload
```

## Verification Checklist

**After setup, verify:**
- [ ] `ml/model.pkl` exists and is ~10-50KB
- [ ] Server starts without errors
- [ ] http://localhost:8000 shows the UI
- [ ] http://localhost:8000/docs shows API documentation
- [ ] Tests pass: `python -m pytest`
- [ ] Database created: `dev.db` or PostgreSQL connection successful

## Common Setup Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| pip install fails | Python version < 3.10 | Upgrade to Python 3.10+ |
| Import error: textblob | Missing NLTK data | Run `python -m textblob.download_corpora` |
| Transformers download hangs | Network/firewall | Use `HF_HOME` environment variable for custom cache |
| Port 8000 in use | Another service running | Use `--port 8001` or kill existing process |
| Database connection error | PostgreSQL not running | Use SQLite: `DATABASE_URL=sqlite:///./dev.db` |

## Environment Configuration

**Required `.env` file:**
```bash
DATABASE_URL=sqlite:///./dev.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/review_trust_db
```

**Optional settings:**
```bash
MODEL_PATH=ml/model.pkl
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

## Docker Alternative

For containerized setup instead:
```bash
docker-compose up --build
# Access at http://localhost:8000
# PostgreSQL automatically configured
```

## Quick Reference

**Minimum setup (3 commands):**
```bash
pip install -r requirements.txt
python ml/train.py
python -m uvicorn app.main:app --reload
```

**Full setup with testing:**
```bash
pip install -r requirements.txt
python ml/train.py
python -m pytest
python ml/evaluate.py
python -m uvicorn app.main:app --reload
```

## Real-World Impact

Proper setup ensures:
- Consistent development environment across team members
- All NLP models pre-downloaded (no production surprises)
- Database schema initialized correctly
- ML model available for inference
- Hot-reload enabled for rapid development

**Setup time:** ~5-10 minutes depending on internet speed (transformers model is ~420MB).
