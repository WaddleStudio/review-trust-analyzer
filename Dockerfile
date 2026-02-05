FROM python:3.10-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev || uv sync

# Download NLP models at build time
RUN uv run python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Copy application code
COPY . .

# Train model at build time
RUN uv run python ml/train.py

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
