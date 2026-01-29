# Testing Standards

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This document defines the **mandatory testing standards** for EUCORA. All code MUST meet ≥90% test coverage with **zero tolerance** for quality gate failures.

**Design Principle**: Quality Gates — no compromises on test coverage, type safety, or CAB evidence standards.

---

## Coverage Requirements

### Minimum Coverage Thresholds

- **Lines**: ≥90%
- **Functions**: ≥90%
- **Branches**: ≥90%
- **Statements**: ≥90%

### Enforcement

- **Pre-commit Hooks**: Block commits with insufficient coverage
- **CI/CD**: Fail builds if coverage < 90%
- **Code Review**: Coverage reports required for PR approval

---

## Test Types

### 1. Unit Tests

**Scope**: Individual functions, methods, components
**Framework**:
- Backend: pytest-django
- Frontend: Vitest + React Testing Library

**Requirements**:
- Test all code paths
- Mock external dependencies
- Fast execution (<100ms per test)

**Example** (Backend):
```python
@pytest.mark.django_db
def test_calculate_risk_score():
    evidence_pack = {'requires_admin': True}
    result = calculate_risk_score(evidence_pack, 'correlation-id')
    assert result['risk_score'] > 50
```

**Example** (Frontend):
```typescript
it('renders component correctly', () => {
  render(<Component prop="value" />);
  expect(screen.getByText('Expected')).toBeInTheDocument();
});
```

### 2. Integration Tests

**Scope**: Component interactions, API endpoints, database operations
**Framework**: pytest-django (backend), Vitest (frontend)

**Requirements**:
- Test component interactions
- Use test database
- Test API endpoints end-to-end

**Example** (Backend):
```python
@pytest.mark.django_db
def test_deployment_intent_creation():
    intent = DeploymentIntent.objects.create(...)
    assert intent.status == 'PENDING'
    assert intent.correlation_id is not None
```

### 3. End-to-End Tests

**Scope**: Complete workflows (packaging → CAB → publishing)
**Framework**: pytest + Playwright (planned)

**Requirements**:
- Test complete user workflows
- Test ring progression scenarios
- Test rollback scenarios

### 4. Idempotency Tests

**Scope**: Connector operations
**Requirements**:
- Verify safe retries
- Test idempotent keys
- Test concurrent operations

**Example**:
```python
def test_connector_idempotency():
    # First call
    result1 = connector.deploy(params, idempotent_key='key-123')
    # Retry with same key
    result2 = connector.deploy(params, idempotent_key='key-123')
    assert result1['object_id'] == result2['object_id']
```

### 5. Rollback Tests

**Scope**: Rollback strategies per execution plane
**Requirements**:
- Test rollback execution
- Validate rollback success
- Test rollback failure handling

---

## Test Organization

### Backend Structure

```
backend/
├── apps/
│   └── {app_name}/
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── test_models.py
│       │   ├── test_views.py
│       │   ├── test_services.py
│       │   └── test_services_coverage.py  # Additional coverage tests
```

### Frontend Structure

```
frontend/
├── src/
│   └── components/
│       └── {component}/
│           ├── Component.tsx
│           └── Component.test.tsx
```

---

## Pre-Commit Hook Requirements

### Backend

- **black**: Code formatting
- **flake8**: Linting (zero warnings)
- **mypy**: Type checking (zero new errors)
- **pytest**: Run tests (all must pass)

### Frontend

- **ESLint**: Linting (zero warnings)
- **TypeScript**: Type checking
- **Vitest**: Run tests (all must pass)

---

## CI/CD Test Execution

### Backend Tests

```yaml
- name: Run pytest with coverage
  run: |
    cd backend
    pytest --cov=apps --cov-report=xml --cov-fail-under=90 -v
```

### Frontend Tests

```yaml
- name: Run tests with coverage
  run: |
    cd frontend
    npm run test:ci
```

---

## Coverage Reporting

### Codecov Integration

- Backend coverage: `backend/coverage.xml`
- Frontend coverage: `frontend/coverage/coverage-final.json`
- Coverage badges in README
- PR comments with coverage diff

---

## Test Data Management

### Fixtures

- **Backend**: `conftest.py` with pytest fixtures
- **Frontend**: Test utilities in `src/test/utils.tsx`

### Test Database

- Separate test database (`eucora_test`)
- Migrations run before tests
- Database reset between test runs

---

## Performance Requirements

- **Unit Tests**: <100ms per test
- **Integration Tests**: <1s per test
- **E2E Tests**: <30s per test

---

## References

- [Quality Gates](./quality-gates.md)
- [Pre-Commit Hooks](../infrastructure/ci-cd-pipelines.md)
- [CI/CD Pipelines](../infrastructure/ci-cd-pipelines.md)
