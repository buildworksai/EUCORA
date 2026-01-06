# CI/CD Pipelines

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

This document defines the **CI/CD pipeline configuration** for EUCORA. All pipelines enforce **quality gates** with zero tolerance for failures.

**Design Principle**: Quality Gates — no compromises on pre-commit hooks, test coverage, type safety.

---

## Pipeline Stages

### 1. Pre-Commit Hooks

**Location**: Local development environment  
**Enforcement**: Blocks commits if checks fail

**Checks**:
- Type safety (mypy, TypeScript)
- Linting (flake8, ESLint)
- Code formatting (black, Prettier)
- Secrets detection (detect-secrets)
- Test coverage (pytest, Vitest)

### 2. Code Quality Checks

**Location**: GitHub Actions  
**Trigger**: Push to main/develop, Pull Requests

**Jobs**:
- SPDX compliance
- PowerShell linting (PSScriptAnalyzer)
- File quality (trailing whitespace, large files)
- Branding compliance

### 3. Backend Tests

**Location**: GitHub Actions  
**Trigger**: Push to main/develop, Pull Requests

**Configuration**:
- PostgreSQL service container
- pytest with coverage enforcement (≥90%)
- Coverage reporting to Codecov

**Command**:
```bash
pytest --cov=apps --cov-report=xml --cov-fail-under=90 -v
```

### 4. Frontend Tests

**Location**: GitHub Actions  
**Trigger**: Push to main/develop, Pull Requests

**Configuration**:
- Node.js 20
- Vitest with coverage (≥90%)
- Coverage reporting to Codecov

**Command**:
```bash
npm run test:ci
```

### 5. Frontend Linting

**Location**: GitHub Actions  
**Trigger**: Push to main/develop, Pull Requests

**Configuration**:
- ESLint with zero warnings
- TypeScript compilation check

**Command**:
```bash
npm run lint
npm run build
```

---

## Quality Gate Enforcement

### Pre-Commit Gates

**Zero Tolerance**:
- Type errors
- Linting warnings
- Insufficient test coverage (<90%)
- Hardcoded secrets

**Action**: Block commit

### CI Gates

**Zero Tolerance**:
- Test failures
- Coverage <90%
- Linting errors
- Build failures

**Action**: Block merge to main

---

## Pipeline Configuration

### GitHub Actions Workflow

**File**: `.github/workflows/code-quality.yml`

**Jobs**:
1. `spdx-compliance`: SPDX header validation
2. `powershell-lint`: PSScriptAnalyzer
3. `file-quality`: Trailing whitespace, large files, JSON/YAML validation
4. `branding-compliance`: EUCORA branding checks
5. `backend-tests`: pytest with coverage
6. `frontend-lint`: ESLint and TypeScript
7. `frontend-tests`: Vitest with coverage
8. `summary`: Quality summary report

### Pre-Commit Configuration

**File**: `.pre-commit-config.yaml`

**Hooks**:
- `trailing-whitespace`: Remove trailing whitespace
- `end-of-file-fixer`: Ensure files end with newline
- `check-yaml`: Validate YAML syntax
- `check-json`: Validate JSON syntax
- `black`: Python code formatting
- `flake8`: Python linting
- `mypy`: Python type checking
- `detect-secrets`: Secrets detection
- `psscriptanalyzer`: PowerShell linting

---

## Coverage Reporting

### Codecov Integration

**Backend**:
- Coverage file: `backend/coverage.xml`
- Flag: `backend`
- Threshold: 90%

**Frontend**:
- Coverage file: `frontend/coverage/coverage-final.json`
- Flag: `frontend`
- Threshold: 90%

### Coverage Badges

- README badges showing coverage percentage
- PR comments with coverage diff
- Coverage trends dashboard

---

## Deployment Pipelines

### Development

**Trigger**: Push to `develop` branch  
**Actions**:
- Run tests
- Build Docker images
- Deploy to development environment

### Staging

**Trigger**: Merge to `main` branch  
**Actions**:
- Run full test suite
- Build production images
- Deploy to staging environment
- Run smoke tests

### Production

**Trigger**: Manual approval + tag  
**Actions**:
- Run full test suite
- Build production images
- Deploy to production
- Run health checks

---

## Pipeline Optimization

### Caching

- **Python**: pip cache
- **Node.js**: npm cache
- **Docker**: Layer caching

### Parallel Execution

- Backend and frontend tests run in parallel
- Code quality checks run in parallel
- Summary job waits for all jobs

---

## References

- [Testing Standards](../architecture/testing-standards.md)
- [Quality Gates](../architecture/quality-gates.md)
- [Pre-Commit Hooks](.pre-commit-config.yaml)

