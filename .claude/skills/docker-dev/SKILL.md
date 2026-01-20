---
name: docker-dev
description: Use when setting up containerized development environment or deploying with Docker
---

# Docker Development Environment

## Overview
Run the Review Trust Analyzer in a containerized environment using Docker Compose. Automatically sets up FastAPI application with PostgreSQL database, networking, and volume persistence.

## When to Use
- Production-like local development
- Team onboarding (consistent environment)
- Avoiding Python version conflicts
- Testing PostgreSQL integration
- CI/CD pipeline testing
- Deployment preparation
- Windows/Mac environment isolation

## Core Workflow

### 1. Start Containers
```bash
docker-compose up --build
```

**This starts:**
- FastAPI app on port 8000
- PostgreSQL database on port 5432
- Automatic database initialization
- Volume mounting for code hot-reload

### 2. Access Application
- Frontend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: localhost:5432 (user: postgres, password: password)

### 3. Stop Containers
```bash
# Graceful shutdown
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## Docker Compose Services

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    depends_on: [db]
    environment:
      DATABASE_URL: postgresql://postgres:password@db/review_trust_db
    volumes:
      - ./:/app  # Hot reload enabled

  db:
    image: postgres:15
    ports: ["5432:5432"]
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: review_trust_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

## Container Management

**View logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f db
```

**Execute commands inside container:**
```bash
# Run tests
docker-compose exec app python -m pytest

# Train model
docker-compose exec app python ml/train.py

# Open shell
docker-compose exec app bash
```

**Restart specific service:**
```bash
docker-compose restart app
```

**Rebuild after dependency changes:**
```bash
docker-compose up --build --force-recreate
```

## Dockerfile Structure

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP models at build time
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Copy application
COPY . .

# Train model
RUN python ml/train.py

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development Workflow

**1. Make code changes**
- Edit files locally
- Changes sync via volume mount
- Uvicorn auto-reloads (in dev mode)

**2. Test changes**
```bash
docker-compose exec app python -m pytest
```

**3. Check database**
```bash
docker-compose exec db psql -U postgres -d review_trust_db

# Inside psql:
\dt                          # List tables
SELECT * FROM reviewraw;     # Query reviews
\q                           # Exit
```

**4. View container status**
```bash
docker-compose ps
docker-compose top
```

## Common Docker Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Port 8000 in use | Another container/process | Change port in docker-compose.yml |
| Database connection refused | DB not ready | Add healthcheck, use `wait-for-it.sh` |
| Changes not reflected | Volume mount issue | Check paths, restart container |
| Build fails | Missing dependencies | Update requirements.txt, rebuild |
| Out of disk space | Old images/volumes | `docker system prune -a` |

## Production Configuration

**Environment variables (.env.production):**
```bash
DATABASE_URL=postgresql://user:pass@production-db/db
MODEL_PATH=/app/ml/model.pkl
LOG_LEVEL=INFO
WORKERS=4
CORS_ORIGINS=["https://yourdomain.com"]
```

**Multi-stage build (smaller image):**
```dockerfile
# Stage 1: Build
FROM python:3.10 as builder
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

## Database Persistence

**Backup database:**
```bash
docker-compose exec db pg_dump -U postgres review_trust_db > backup.sql
```

**Restore database:**
```bash
docker-compose exec -T db psql -U postgres review_trust_db < backup.sql
```

**Reset database:**
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Reinitialize
```

## Performance Optimization

**Resource limits (docker-compose.yml):**
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

**Scale workers (production):**
```bash
docker-compose up --scale app=3
```

**Use BuildKit for faster builds:**
```bash
DOCKER_BUILDKIT=1 docker-compose build
```

## Networking

**Access from other containers:**
```bash
# App container can reach DB at:
postgresql://postgres:password@db:5432/review_trust_db

# External access:
postgresql://postgres:password@localhost:5432/review_trust_db
```

**Custom network:**
```yaml
networks:
  app-network:
    driver: bridge

services:
  app:
    networks: [app-network]
  db:
    networks: [app-network]
```

## Health Checks

**Add to docker-compose.yml:**
```yaml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/docs"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## Quick Reference

```bash
# Start development environment
docker-compose up --build

# Background mode
docker-compose up -d

# View logs
docker-compose logs -f app

# Run tests
docker-compose exec app python -m pytest

# Open shell
docker-compose exec app bash

# Stop everything
docker-compose down

# Clean slate (remove volumes)
docker-compose down -v && docker system prune -f
```

## Real-World Impact

Docker provides:
- **Consistency**: Same environment across development, testing, production
- **Isolation**: No Python version conflicts, clean dependencies
- **Portability**: Works on Windows, Mac, Linux
- **Scalability**: Easy to add more workers or services
- **CI/CD**: Seamless integration with GitHub Actions, GitLab CI

**Typical startup time:**
- Cold build: ~5-10 minutes (downloading models)
- Warm start: ~30 seconds
- Hot reload: < 1 second per code change

**Recommended for:**
- Production deployment
- Team collaboration
- Integration testing
- Complex multi-service architecture
