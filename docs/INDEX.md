# Review Trust Analyzer - Documentation Index

Welcome to the documentation for the Review Trust Analyzer system. This index provides a comprehensive guide to all available documentation.

## 📚 Main Documentation

### Getting Started
- **[README.md](../README.md)** - Main project overview, features, setup instructions, and API usage examples
- **[.claude/README.md](../.claude/README.md)** - Claude Code Superpowers integration guide (中英文雙語)

### Feature Documentation
- **[FRONTEND_DEMO.md](../FRONTEND_DEMO.md)** - Frontend features demonstration and UI highlights
- **[TEST_CASES.md](./TEST_CASES.md)** - Validation test cases with expected outcomes

### Version & History
- **[VERSION_COMPARISON.md](../VERSION_COMPARISON.md)** - Version history and feature comparison
- **[COMMIT_LOG.md](../COMMIT_LOG.md)** - Recent commit messages and changes

---

## 🛠️ Claude Code Skills

The project includes 6 specialized skills for development workflows:

| Skill | Purpose | Documentation |
|-------|---------|---------------|
| **train-model** | Train/retrain ML model | [train-model/SKILL.md](../.claude/skills/train-model/SKILL.md) |
| **dev-setup** | Local development setup | [dev-setup/SKILL.md](../.claude/skills/dev-setup/SKILL.md) |
| **run-tests** | Execute test suite | [run-tests/SKILL.md](../.claude/skills/run-tests/SKILL.md) |
| **batch-analyze** | Process CSV batch reviews | [batch-analyze/SKILL.md](../.claude/skills/batch-analyze/SKILL.md) |
| **evaluate-model** | Assess model performance | [evaluate-model/SKILL.md](../.claude/skills/evaluate-model/SKILL.md) |
| **docker-dev** | Docker development environment | [docker-dev/SKILL.md](../.claude/skills/docker-dev/SKILL.md) |

---

## 🏗️ Architecture Documentation

### Core Modules

#### Backend (FastAPI)
- **`app/main.py`** - Application entry point
- **`app/api/endpoints.py`** - API route definitions
- **`app/models.py`** - SQLModel database models
- **`app/database.py`** - Database connection configuration
- **`app/services/inference.py`** - ML inference service

#### Machine Learning
- **`ml/train.py`** - Model training script
- **`ml/evaluate.py`** - Model evaluation and metrics
- **`ml/model.pkl`** - Trained Logistic Regression model

#### Feature Engineering
- **`features/text_features.py`** - Text-based feature extraction (TextBlob sentiment)
- **`features/semantic_features.py`** - Multilingual semantic analysis (sentence-transformers)
- **`features/user_behavior_features.py`** - User behavior patterns (⚠️ Currently stubbed)

#### Frontend
- **`app/static/index.html`** - Single review analysis UI
- **`app/static/batch.html`** - Batch processing UI
- **`app/static/style.css`** - Glassmorphism design styles

#### Testing
- **`tests/test_api.py`** - API endpoint tests
- **`tests/test_features.py`** - Feature extraction tests
- **`tests/test_batch_manual.py`** - Manual batch processing tests

---

## 📊 Data & Configuration

### Configuration Files
- **`.env`** - Environment variables (DATABASE_URL)
- **`.env.example`** - Environment variable template
- **`pyproject.toml`** - Modern Python project configuration
- **`requirements.txt`** - Python dependencies
- **`docker-compose.yml`** - Multi-service orchestration
- **`Dockerfile`** - Container image definition

### Data Files
- **`data/sample_reviews.csv`** - Sample review data for batch testing
- **`data/dev.db`** - SQLite development database

---

## 🎯 Development Guides

### Quick Start
1. Read [README.md](../README.md) for project overview
2. Use `/dev-setup` skill for environment setup
3. Run `/run-tests` to verify installation
4. Explore [TEST_CASES.md](./TEST_CASES.md) for usage examples

### Development Workflow
1. **Before making changes**: Run `/run-tests`
2. **For model changes**: Use `/train-model` → `/evaluate-model`
3. **For batch analysis**: Use `/batch-analyze` with CSV files
4. **For Docker deployment**: Use `/docker-dev`

### Testing Strategy
- **Unit Tests**: `pytest tests/test_*.py`
- **Coverage Report**: `pytest --cov=. --cov-report=html`
- **Manual Testing**: Use test cases in [TEST_CASES.md](./TEST_CASES.md)

---

## 🔍 Key Concepts

### Trust Score Calculation
The system uses a **hybrid approach**:
1. **ML Prediction** - Logistic Regression probability
2. **Semantic Analysis** - Contrastive similarity with promotional/genuine seeds
3. **Text Features** - TextBlob sentiment, keyword detection
4. **User Behavior** - Review frequency, IP patterns (⚠️ Not implemented)

### Platform Support
- Google Maps
- Booking.com
- Agoda
- TripAdvisor

### Multilingual Support
Supports 50+ languages including:
- English
- Traditional Chinese (繁體中文)
- Simplified Chinese (简体中文)
- And more via `paraphrase-multilingual-MiniLM-L12-v2`

---

## 📈 Current Status

### Implemented Features ✅
- NLP sentiment analysis (TextBlob + sentence-transformers)
- Batch CSV processing
- Single review API (`POST /review/score`)
- Batch review API (`POST /reviews/batch`)
- Frontend UI with glassmorphism design
- Docker containerization

### Known Limitations ⚠️
- **User Behavior Features**: Currently stubbed (mock data only)
- **Model Recall**: Only 47% (53% of fake reviews missed)
- **Authentication**: Not implemented (all endpoints public)
- **Test Coverage**: ~50% (needs improvement)

### Roadmap 🚀
See [swirling-sparking-mountain.md](../../.claude/plans/swirling-sparking-mountain.md) for detailed development plan.

---

## 🤝 Contributing

### Code Standards
- Python 3.10+
- Type hints preferred
- Follow existing code structure
- Add tests for new features

### Before Submitting
1. Run `/run-tests` - Ensure all tests pass
2. Update documentation if needed
3. Add test cases for new features
4. Update version history

---

## 📞 Support & Resources

### Documentation Files
- **Main README**: [../README.md](../README.md)
- **Skills Guide**: [../.claude/README.md](../.claude/README.md)
- **Test Cases**: [./TEST_CASES.md](./TEST_CASES.md)

### Development Plans
- **Current Plan**: [../../.claude/plans/swirling-sparking-mountain.md](../../.claude/plans/swirling-sparking-mountain.md)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Last Updated**: 2026-01-21
**Version**: 0.2.0
**Status**: Active Development
