---
name: dev-setup
description: Use when setting up local development environment for the first time or after clean checkout
---

# Development Environment Setup

## Overview
Complete setup workflow for the Review Trust Analyzer development environment using **uv** package manager. Installs dependencies, trains the ML model, and starts the FastAPI development server.

## When to Use
- Fresh clone of the repository
- New developer onboarding
- After `rm -rf .venv` or virtual environment corruption
- Switching between development machines
- After major dependency updates in pyproject.toml

## Prerequisites

**Install uv (if not installed):**
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Core Workflow

### 1. Install Python Dependencies
```bash
uv sync
```

**What happens:**
- Creates `.venv/` automatically (no manual venv activation needed)
- Installs all dependencies from `pyproject.toml`
- Creates `uv.lock` for reproducible builds

### 2. Train Initial Model
```bash
uv run python ml/train.py
```

**Creates:** `ml/model.pkl` (Logistic Regression classifier)

### 3. Start Development Server
```bash
uv run uvicorn app.main:app --reload
```

**Access points:**
- Frontend UI: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Place Analysis: http://localhost:8000/places

## Complete Setup Script

```bash
# Ensure you're in project root
cd D:\Projects\review-trust-analyzer

# Install dependencies (auto-creates .venv)
uv sync

# Download NLP models
uv run python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Train ML model
uv run python ml/train.py

# Verify installation
uv run pytest

# Start server
uv run uvicorn app.main:app --reload
```

## Verification Checklist

**After setup, verify:**
- [ ] `ml/model.pkl` exists and is ~10-50KB
- [ ] Server starts without errors
- [ ] http://localhost:8000 shows the UI
- [ ] http://localhost:8000/docs shows API documentation
- [ ] Tests pass: `uv run pytest`

## Common Setup Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| uv not found | Not installed | Install uv (see Prerequisites) |
| Import error: textblob | Missing NLTK data | `uv run python -m textblob.download_corpora` |
| Transformers download hangs | Network/firewall | Set `HF_HOME` env var |
| Port 8000 in use | Another service | Use `--port 8001` |

## Environment Configuration

**Required `.env` file:**
```bash
DATABASE_URL=sqlite:///./dev.db
SERPAPI_KEY=your_serpapi_key_here  # For Place Analysis
```

## Docker Alternative

For containerized setup:
```bash
docker-compose up --build
```

## Quick Reference

```bash
# Minimum setup (3 commands)
uv sync
uv run python ml/train.py
uv run uvicorn app.main:app --reload

# Full setup with testing
uv sync
uv run python ml/train.py
uv run pytest
uv run python ml/evaluate.py
uv run uvicorn app.main:app --reload

# Add new package
uv add package-name

# Update all packages
uv sync --upgrade
```

## uv vs pip 對照

| 動作 | 舊 (pip) | 新 (uv) |
|------|----------|---------|
| 安裝套件 | `pip install -r requirements.txt` | `uv sync` |
| 執行 Python | `python script.py` | `uv run python script.py` |
| 執行 pytest | `pytest` | `uv run pytest` |
| 新增套件 | `pip install X` + 手動編輯 | `uv add X` |
| 啟動 server | `uvicorn app.main:app` | `uv run uvicorn app.main:app` |

**Note:** 使用 `uv run` 不需要手動 activate 虛擬環境。
