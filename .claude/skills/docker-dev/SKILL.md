---
name: docker-dev
description: Use when setting up containerized development environment or deploying with Docker
---

# Docker Development Environment

## Overview
Run the Review Trust Analyzer in containers using Docker Compose. Sets up FastAPI + PostgreSQL with hot reload support.

## When to Use
- Production-like local development
- Team onboarding (consistent environment)
- Testing PostgreSQL integration
- Deployment preparation
- Windows environment isolation

## Core Workflow

### 1. Start Containers
```bash
docker-compose up --build
```

**Services started:**
- FastAPI app: http://localhost:8000
- PostgreSQL: localhost:5432
- API Docs: http://localhost:8000/docs

### 2. Stop Containers
```bash
docker-compose down        # Graceful shutdown
docker-compose down -v     # Remove volumes (clean slate)
```

## Container Management

```bash
# View logs
docker-compose logs -f app

# Run tests inside container
docker-compose exec app uv run pytest

# Train model
docker-compose exec app uv run python ml/train.py

# Open shell
docker-compose exec app bash
```

## Debugging Commands

**Test database connection:**
```bash
docker-compose exec app uv run python -c "
from app.core.config import settings
from sqlmodel import create_engine, Session, text
engine = create_engine(settings.DATABASE_URL)
with Session(engine) as s:
    print(s.exec(text('SELECT 1')).one())
"
```

**Test SerpAPI connection:**
```bash
docker-compose exec app uv run python -c "
from app.services.serpapi import SerpAPIService
svc = SerpAPIService()
print(f'API Key configured: {bool(svc.api_key)}')
"
```

**Test HTTP endpoint:**
```bash
curl -X POST http://localhost:8000/places/analyze \
  -H 'Content-Type: application/json' \
  -d '{"query": "測試店名"}'
```

**Check container status:**
```bash
docker-compose ps
docker-compose top
```

## Windows Hot Reload Fix

**docker-compose.yml** 需要加入 polling 設定：
```yaml
services:
  app:
    environment:
      - WATCHFILES_FORCE_POLLING=true  # Windows 必要
```

## Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Port 8000 in use | Another process | Change port or kill process |
| DB connection refused | DB not ready | Wait or check healthcheck |
| Changes not reflected | Volume mount | Restart container |
| Hot reload not working | Windows | Add WATCHFILES_FORCE_POLLING |

## Database Operations

```bash
# Backup
docker-compose exec db pg_dump -U postgres review_trust_db > backup.sql

# Restore
docker-compose exec -T db psql -U postgres review_trust_db < backup.sql

# Reset (delete all data)
docker-compose down -v && docker-compose up -d
```

## Quick Reference

```bash
# Start
docker-compose up --build

# Background mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Run tests
docker-compose exec app uv run pytest

# Stop
docker-compose down

# Clean slate
docker-compose down -v && docker system prune -f
```

## Dockerfile 結構

```dockerfile
FROM python:3.10-slim
WORKDIR /app

# Install uv
RUN pip install uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy app
COPY . .

# Train model at build time
RUN uv run python ml/train.py

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```
