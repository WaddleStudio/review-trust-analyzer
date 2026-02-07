# Review Trust Analyzer

## Overview
A system to analyze review credibility and detect potential fake reviews using a hybrid approach (Rule-based + ML + NLP).

## Features
- **Real-time Analysis**: Instant trust score calculation
- **ML-Powered Detection**: Logistic Regression + Semantic Similarity
- **Place Analysis**: Analyze Google Maps reviews via SerpAPI
- **Interactive UI**: Dark mode glassmorphism interface
- **Multilingual**: English + Chinese (Traditional/Simplified)

## Tech Stack
- **Backend**: Python 3.10+ / FastAPI
- **Package Manager**: uv (recommended) or pip
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: PostgreSQL / SQLite (dev)
- **ML/NLP**: Scikit-learn, Sentence-Transformers
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended)

**Install uv:**
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup & Run (3 commands)

```bash
# 1. Install dependencies
uv sync

# 2. Train ML model
uv run python ml/train.py

# 3. Start server
uv run uvicorn app.main:app --reload
```

**Access:**
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Place Analysis: http://localhost:8000/places

### Docker Alternative

```bash
docker-compose up --build
```

## Available Skills (AI-Assisted Development)

This project uses [Superpowers](https://github.com/anthropics/superpowers) for workflow automation:

| Skill | Description |
|-------|-------------|
| `/dev-setup` | Complete development environment setup |
| `/run-tests` | Run test suite with coverage |
| `/train-model` | Train the ML model |
| `/evaluate-model` | Evaluate model performance |
| `/batch-analyze` | Process CSV files with reviews |
| `/docker-dev` | Docker development environment |

## Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov=features

# Specific test
uv run pytest tests/test_api.py -v
```

## API Usage

**POST /reviews/score**
```json
{
  "text": "Best hotel ever! Free gift!",
  "rating": 5,
  "platform": "google",
  "user_id": "user_001"
}
```

**Response:**
```json
{
  "trust_score": 0.12,
  "is_suspicious": true,
  "reasons": ["Contains promotional keywords."]
}
```

**POST /places/analyze**
```json
{
  "query": "店名或 Google Maps URL"
}
```

## Project Structure

```
review-trust-analyzer/
├── app/                    # FastAPI application
│   ├── api/                # API endpoints
│   ├── core/               # Configuration
│   ├── services/           # Business logic
│   └── static/             # Frontend
├── features/               # Feature engineering
├── ml/                     # ML training & evaluation
├── tests/                  # Test suite
├── docs/                   # Documentation
│   └── plans/              # Implementation plans
├── .claude/                # Claude Code settings
│   └── skills/             # Custom skills
├── pyproject.toml          # Dependencies (uv)
├── uv.lock                 # Lock file
├── docker-compose.yml
└── Dockerfile
```

## Environment Variables

Create `.env` file:
```bash
DATABASE_URL=sqlite:///./dev.db
SERPAPI_KEY=your_serpapi_key_here  # For Place Analysis
```

## uv vs pip Commands

| Action | uv | pip (legacy) |
|--------|-----|--------------|
| Install deps | `uv sync` | `pip install -r requirements.txt` |
| Run Python | `uv run python script.py` | `python script.py` |
| Run pytest | `uv run pytest` | `pytest` |
| Add package | `uv add package` | `pip install package` |
| Start server | `uv run uvicorn app.main:app` | `uvicorn app.main:app` |

**Note:** `uv run` automatically uses the virtual environment without manual activation.

## License
MIT
