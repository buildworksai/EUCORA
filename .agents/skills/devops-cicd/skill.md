---
name: devops-cicd
description: DevOps and CI/CD patterns for EUCORA including GitHub Actions workflows, Docker Compose orchestration, quality gates, and pre-commit hooks. Use when creating pipelines, configuring containers, or implementing quality enforcement.
status: ✅ Working
last-validated: 2026-01-30
---

# DevOps & CI/CD Patterns

CI/CD and container orchestration patterns for the EUCORA platform.

---

## Quick Reference

| Technology | Pattern |
|------------|---------|
| CI/CD | GitHub Actions |
| Containers | Docker Compose (dev), Kubernetes (prod) |
| Quality Gates | Pre-commit hooks + CI enforcement |
| Coverage | ≥90% enforced |
| Linting | Zero warnings tolerance |

---

## GitHub Actions Workflows

### Workflow Structure

```yaml
# .github/workflows/code-quality.yml
name: Code Quality

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests with coverage
        run: pytest --cov --cov-fail-under=90 --cov-report=xml
        env:
          DATABASE_URL: postgres://test:test@localhost:5432/test_db

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
          fail_ci_if_error: true

  frontend-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: frontend

      - name: TypeScript check
        run: npx tsc --noEmit
        working-directory: frontend

      - name: ESLint (zero warnings)
        run: npm run lint -- --max-warnings 0
        working-directory: frontend

      - name: Run tests
        run: npm test -- --coverage
        working-directory: frontend
```

### Quality Gate Enforcement

```yaml
# Quality gate job - blocks merge if failed
quality-gate:
  runs-on: ubuntu-latest
  needs: [backend-tests, frontend-tests, security-scan]

  steps:
    - name: Check all jobs passed
      run: |
        echo "All quality gates passed ✅"
        echo "- Backend tests: ${{ needs.backend-tests.result }}"
        echo "- Frontend tests: ${{ needs.frontend-tests.result }}"
        echo "- Security scan: ${{ needs.security-scan.result }}"
```

---

## Docker Compose

### Development Configuration

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
    environment:
      - DEBUG=True
      - DATABASE_URL=postgres://user:pass@db:5432/eucora
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: eucora
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d eucora"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/eucora
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - web
      - redis

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: celery -A config beat -l info
    volumes:
      - ./backend:/app
    depends_on:
      - celery-worker
    deploy:
      replicas: 1  # Singleton pattern

volumes:
  postgres_data:
  static_volume:
```

### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: eucora/backend:${TAG:-latest}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Pre-Commit Hooks

### Configuration

```yaml
# .pre-commit-config.yaml
repos:
  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  # JavaScript/TypeScript
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        args: [--max-warnings, '0']
        files: \.[jt]sx?$

  # Security
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # General
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: no-commit-to-branch
        args: [--branch, main]
```

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

---

## Dockerfile Patterns

### Multi-Stage Build

```dockerfile
# Dockerfile
# Stage 1: Build
FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy app
COPY backend/ .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### Development Dockerfile

```dockerfile
# Dockerfile.dev
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## Quality Gates Checklist

### CI Pipeline Must Enforce

```
☐ Backend tests pass (pytest)
☐ Frontend tests pass (vitest)
☐ Coverage ≥90% (pytest-cov, vitest --coverage)
☐ TypeScript check passes (tsc --noEmit)
☐ ESLint zero warnings (--max-warnings 0)
☐ Python linting passes (ruff)
☐ Security scan passes (trivy, detect-secrets)
☐ SPDX compliance check passes
```

### Pre-Commit Must Block

```
☐ Trailing whitespace
☐ Merge conflicts
☐ Invalid YAML/JSON
☐ Secrets in code
☐ Direct commits to main
☐ Type errors (mypy)
☐ Linting errors (ruff, eslint)
```

---

## Commands Reference

```bash
# Docker Compose
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml logs -f web
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.dev.yml down -v

# Pre-commit
pre-commit install
pre-commit run --all-files
pre-commit autoupdate

# Testing with coverage
pytest --cov --cov-fail-under=90 --cov-report=html
npm test -- --coverage

# Build and push
docker build -t eucora/backend:latest .
docker push eucora/backend:latest
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Skipping CI checks | All checks must pass |
| Coverage < 90% | Enforce ≥90% in CI |
| `--no-verify` commits | Pre-commit hooks mandatory |
| Secrets in Dockerfile | Use build args or vault |
| Root user in container | Create non-root user |
| No health checks | Always define health checks |
