# Review Trust Analyzer

## Overview
A system to analyze review credibility and detect potential fake reviews using a hybrid approach (Rule-based + ML).

## 🎯 Features
- ✅ **Real-time Analysis**: Instant trust score calculation
- ✅ **ML-Powered Detection**: Logistic Regression baseline model
- ✅ **Interactive UI**: Beautiful dark mode interface with glassmorphism design
- ✅ **Multi-Platform Support**: Google Maps, Booking.com, Agoda, TripAdvisor
- ✅ **Detailed Explanations**: Clear reasoning for suspicious patterns

## Tech Stack
- **Backend**: Python 3 + FastAPI
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: PostgreSQL / SQLite (dev)
- **ML**: Scikit-learn (Logistic Regression)
- **Containerization**: Docker + Docker Compose

## 🤖 AI-Assisted Development with Superpowers

This project integrates the [Superpowers](https://github.com/obra/superpowers) agentic skills framework to enhance development workflow automation. Skills provide structured commands for common tasks.

### Available Skills
- `/train-model` - Train the ML model
- `/dev-setup` - Complete development environment setup
- `/run-tests` - Run the test suite with coverage
- `/batch-analyze` - Process CSV files with multiple reviews
- `/evaluate-model` - Evaluate model performance metrics
- `/docker-dev` - Start Docker development environment

📖 **[詳細文檔 / Detailed Documentation (繁體中文)](.claude/README.md)**

## Setup & Run

### 1. Prerequisites
- Docker & Docker Compose installed (for production)
- Python 3.10+ (for local development)

### 2. Quick Start (AI-Assisted)
Using the Superpowers `/dev-setup` skill workflow:
```bash
pip install -r requirements.txt   # Install dependencies
python ml/train.py                 # Train ML model
python -m uvicorn app.main:app --reload  # Start server
```

### 3. Start Services with Docker
```bash
docker-compose up --build
```
The application will be available at `http://localhost:8000`.
API Documentation (Swagger): `http://localhost:8000/docs`.

### 4. Local Development (Without Docker)
If you want to run locally:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Train the ML model:
   ```bash
   python ml/train.py
   ```
   This will generate `ml/model.pkl`.

3. Run the development server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   The app will use SQLite by default (configured in `.env`).

## Testing
Run unit tests:
```bash
python -m pytest
```

## 🎨 Frontend Features
The web interface provides an intuitive way to analyze reviews:

### Visual Trust Score Indicator
- **Green (80-100%)**: Trustworthy reviews
- **Yellow (50-79%)**: Moderate risk
- **Red (0-49%)**: Suspicious

### Real-time Analysis
- Enter review details (platform, rating, user ID, text)
- Click "Analyze Trust Score"
- See instant results with visual feedback

### Detailed Breakdown
- Trust score percentage
- Suspicious verdict
- Specific reasons for suspicion

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
Response:
```json
{
  "trust_score": 0.12,
  "is_suspicious": true,
  "reasons": ["Contains promotional keywords."]
}
```

## 📊 Example Results

### Trustworthy Review (90% Trust Score)
```json
{
  "text": "Had a wonderful stay. Staff was friendly and helpful.",
  "rating": 4,
  "platform": "google",
  "user_id": "verified_user"
}
```
**Result**: ✅ "No specific suspicious patterns detected."

### Suspicious Review (10% Trust Score)
```json
{
  "text": "Amazing discount! Free gift! Book now!",
  "rating": 5,
  "platform": "booking",
  "user_id": "promo_user_99"
}
```
**Result**: ⚠️ "Contains promotional keywords."

## Project Structure
```
review-trust-analyzer/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models.py            # Database models
│   ├── database.py          # DB connection
│   ├── static/              # Frontend assets
│   │   ├── index.html
│   │   ├── style.css
│   │   └── script.js
│   ├── api/
│   │   └── endpoints.py     # API routes
│   └── services/
│       └── inference.py     # ML inference
├── features/                # Feature engineering
│   ├── text_features.py
│   └── user_behavior_features.py
├── ml/                      # ML training pipeline
│   ├── train.py
│   ├── evaluate.py
│   └── model.pkl
├── tests/
│   ├── test_features.py
│   └── test_api.py
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🚀 Next Steps
- [ ] Enhance feature engineering (NLP, user history patterns)
- [ ] Upgrade to XGBoost or BERT-based models
- [ ] Add batch analysis capabilities
- [ ] Implement user authentication
- [ ] Add analytics dashboard
