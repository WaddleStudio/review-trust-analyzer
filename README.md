# Review Trust Analyzer

## Overview
A system to analyze Google Maps review credibility and detect fake reviews using a hybrid approach (Rule-based + ML + NLP + Local LLM Judge).

## Features
- **Place Analysis**: Analyze Google Maps reviews via SerpAPI — core workflow
- **Hybrid Scoring**: Rules + ML model, with Qwen3-14B as LLM judge for borderline cases (30–70% trust score)
- **Labeling Pipeline**: Web UI + Discord interactive buttons for semi-automated dataset curation
- **Remote Control**: OpenClaw integration — trigger analyses, run tests, monitor system via Discord
- **Interactive UI**: Dark mode glassmorphism interface

## Tech Stack
- **Backend**: Python 3.10+ / FastAPI
- **Package Manager**: uv (recommended) or pip
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: PostgreSQL / SQLite (dev)
- **ML/NLP**: Scikit-learn, Sentence-Transformers
- **LLM Judge**: Qwen3-14B via Ollama (WSL2, local GPU)
- **Remote Control**: OpenClaw via Discord
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Ollama running in WSL2 with `qwen3:14b` pulled (for LLM judge)

**Install uv:**
```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Mac/Linux / WSL2
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Install Ollama (WSL2):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:14b
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
- Place Analysis: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Labeling Queue: http://localhost:8000/admin/labeling

### Docker Alternative

```bash
docker-compose up --build
```

## Available Scripts

This project uses [Superpowers](https://github.com/anthropics/superpowers) for workflow automation:

| Skill | Description |
|-------|-------------|
| `/dev-setup` | Complete development environment setup |
| `/run-tests` | Run test suite with coverage |
| `/train-model` | Train the ML model |
| `/evaluate-model` | Evaluate model performance |
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

**POST /places/analyze**
```json
{ "query": "店名或 Google Maps URL" }
```

**Response** (borderline reviews include LLM judgment):
```json
{
  "place": { "name": "...", "rating": 4.2, "total_reviews": 312 },
  "summary": {
    "overall_trust_score": 0.61,
    "suspicious_count": 4,
    "total_analyzed": 20
  },
  "reviews": [
    {
      "text": "...",
      "trust_score": 0.52,
      "is_suspicious": false,
      "llm_verdict": "fake",
      "llm_reasoning": "用詞模板化，缺乏具體消費細節..."
    }
  ]
}
```

**GET /api/status**
```json
{
  "server": "ok",
  "ollama": "ok",
  "ollama_model": "qwen3:14b",
  "labeling_pending": 12,
  "serpapi_credits": 85
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
├── features/               # Feature engineering scripts
├── ml/                     # ML training (train_pipeline.py)
├── scripts/                # Utility scripts (batch crawling, feature generation, pre-labeling)
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
SERPAPI_KEY=your_serpapi_key_here
OLLAMA_URL=http://host.docker.internal:11434  # Docker
# OLLAMA_URL=http://localhost:11434           # Local dev
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

