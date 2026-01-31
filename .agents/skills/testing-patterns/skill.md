---
name: testing-patterns
description: EUCORA testing strategies for ≥90% coverage enforcement. Use when writing tests, reviewing test coverage, or implementing quality gates. Includes idempotency tests, rollback tests, connector integration tests, and correlation ID isolation patterns.
status: ✅ Working
last-validated: 2026-01-30
---

# Testing Patterns for EUCORA

Testing strategies aligned with EUCORA's quality gates and CAB-ready governance requirements.

---

## Quick Reference

| Requirement | Threshold |
|-------------|-----------|
| Test Coverage | ≥90% (enforced by CI) |
| Pre-commit Hooks | ZERO bypasses allowed |
| Type Checking | ZERO new errors beyond baseline |
| Linting | `--max-warnings 0` |
| Ring 0 Tests | Rollback validated before Ring 1 |

---

## Testing Pyramid (EUCORA-Specific)

```
        ┌─────────────┐
        │   E2E (5%)  │  Ring rollout scenarios
        └──────┬──────┘
               │
       ┌───────┴───────┐
       │ Integration   │  Connector tests, API contracts
       │   (25%)       │
       └───────┬───────┘
               │
   ┌───────────┴───────────┐
   │     Unit Tests        │  Models, services, components
   │       (70%)           │
   └───────────────────────┘
```

---

## Coverage Requirements (NON-NEGOTIABLE)

### ≥90% Coverage Enforced

```bash
# Backend (pytest)
pytest --cov --cov-fail-under=90

# Frontend (Vitest)
vitest run --coverage --coverage.thresholds.lines=90

# PowerShell (Pester)
Invoke-Pester -CodeCoverage @{ Path = '*.ps1' } -CodeCoverageOutputFileThreshold 90
```

### CI Enforcement

```yaml
# .github/workflows/test.yml
- name: Run tests with coverage
  run: pytest --cov --cov-fail-under=90 --cov-report=xml

- name: Fail if coverage below threshold
  if: failure()
  run: |
    echo "❌ Coverage below 90% - build blocked"
    exit 1
```

---

## MANDATORY Test Types

### 1. Correlation ID Isolation Tests

**MANDATORY for all Django apps** — Verifies correlation ID filtering works correctly.

```python
# tests/test_correlation_isolation.py

import pytest
from uuid import uuid4
from apps.deployments.models import Deployment

@pytest.mark.django_db
class TestCorrelationIdIsolation:
    """Verify correlation ID filtering in queries."""

    def test_filter_by_correlation_id(self, deployment_factory):
        """Deployments are correctly filtered by correlation_id."""
        correlation_id = str(uuid4())

        # Create deployment with specific correlation ID
        deployment = deployment_factory(correlation_id=correlation_id)

        # Create other deployments
        deployment_factory()
        deployment_factory()

        # Filter should return only matching deployment
        result = Deployment.objects.filter(correlation_id=correlation_id)

        assert result.count() == 1
        assert result.first().id == deployment.id

    def test_correlation_id_uniqueness(self, deployment_factory):
        """Correlation IDs are unique across deployments."""
        d1 = deployment_factory()
        d2 = deployment_factory()

        assert d1.correlation_id != d2.correlation_id

    def test_correlation_id_in_audit_log(self, deployment_factory, audit_log_factory):
        """Audit logs include correlation ID from deployment."""
        deployment = deployment_factory()

        log = audit_log_factory(
            action="deployment.approved",
            correlation_id=deployment.correlation_id,
        )

        assert log.correlation_id == deployment.correlation_id
```

### 2. Idempotency Tests

**MANDATORY for all connector operations** — Verifies safe retries.

```python
# tests/connectors/test_idempotency.py

import pytest
from apps.connectors.intune import IntuneConnector

@pytest.mark.integration
class TestConnectorIdempotency:
    """Verify connector operations are idempotent."""

    def test_duplicate_publish_returns_same_result(self, intune_connector, package):
        """Publishing same package twice returns same result."""
        correlation_id = "test-idempotency-001"

        # First publish
        result1 = intune_connector.publish(
            package=package,
            correlation_id=correlation_id,
        )

        # Second publish with same correlation ID
        result2 = intune_connector.publish(
            package=package,
            correlation_id=correlation_id,
        )

        # Should return same result, not create duplicate
        assert result1.intune_app_id == result2.intune_app_id
        assert result1.status == result2.status

    def test_duplicate_publish_returns_conflict_status(self, intune_connector, package):
        """Duplicate correlation ID returns 409 conflict, not new deployment."""
        correlation_id = "test-idempotency-002"

        # First publish
        intune_connector.publish(package=package, correlation_id=correlation_id)

        # Second attempt should indicate existing
        result = intune_connector.publish(package=package, correlation_id=correlation_id)

        assert result.was_existing is True
        assert result.conflict_resolved is True

    def test_different_correlation_ids_create_separate(self, intune_connector, package):
        """Different correlation IDs create separate deployments."""
        result1 = intune_connector.publish(
            package=package,
            correlation_id="test-idempotency-003",
        )

        result2 = intune_connector.publish(
            package=package,
            correlation_id="test-idempotency-004",
        )

        # Different correlation IDs = different deployments
        assert result1.intune_app_id != result2.intune_app_id
```

### 3. Rollback Tests

**MANDATORY before Ring 2+ promotion** — Validates rollback strategies per plane.

```python
# tests/rollback/test_rollback_validation.py

import pytest
from apps.orchestrator.rollback import RollbackValidator

@pytest.mark.integration
class TestRollbackValidation:
    """Verify rollback strategies work before Ring promotion."""

    def test_ring0_rollback_required_before_ring1(self, deployment):
        """Ring 0 rollback must be validated before Ring 1 promotion."""
        validator = RollbackValidator(deployment)

        # Should fail if rollback not tested
        assert not validator.can_promote_to_ring(1)

        # Validate rollback in Ring 0
        validator.execute_rollback_test()

        # Now promotion allowed
        assert validator.can_promote_to_ring(1)

    @pytest.mark.parametrize("connector_type", [
        "intune",
        "jamf",
        "sccm",
        "landscape",
    ])
    def test_plane_specific_rollback(self, connector_type, deployment):
        """Each execution plane has working rollback strategy."""
        connector = get_connector(connector_type)

        # Deploy
        deployment_result = connector.deploy(deployment)
        assert deployment_result.success

        # Rollback
        rollback_result = connector.rollback(
            deployment_id=deployment_result.id,
            target_version=deployment.previous_version,
        )

        assert rollback_result.success
        assert rollback_result.current_version == deployment.previous_version

    def test_rollback_sla_enforcement(self, deployment):
        """Rollback completes within SLA (≤4 hours for P0/P1)."""
        import time

        start = time.time()

        rollback_result = execute_rollback(deployment)

        elapsed_hours = (time.time() - start) / 3600

        assert rollback_result.success
        assert elapsed_hours <= 4, f"Rollback took {elapsed_hours}h, exceeds 4h SLA"
```

### 4. Connector Integration Tests

**MANDATORY for each execution plane** — Tests connector end-to-end.

```python
# tests/integration/connectors/test_intune_connector.py

import pytest
from apps.connectors.intune import IntuneConnector
from apps.connectors.models import ConnectorResult

@pytest.mark.integration
class TestIntuneConnector:
    """Integration tests for Intune connector."""

    def test_publish_win32_app(self, intune_connector, win32_package, correlation_id):
        """Publish Win32 app to Intune successfully."""
        result = intune_connector.publish(
            package=win32_package,
            correlation_id=correlation_id,
        )

        assert result.success
        assert result.intune_app_id is not None
        assert result.correlation_id == correlation_id

    def test_query_deployment_status(self, intune_connector, deployed_app):
        """Query deployment status from Intune."""
        status = intune_connector.get_deployment_status(deployed_app.intune_app_id)

        assert status.install_success_count >= 0
        assert status.install_failure_count >= 0

    def test_error_classification_transient(self, intune_connector):
        """Transient errors are correctly classified for retry."""
        # Simulate 429 rate limit
        with mock_graph_response(status_code=429):
            result = intune_connector.publish(package, correlation_id)

        assert result.error_class == "TRANSIENT"
        assert result.should_retry is True

    def test_error_classification_permanent(self, intune_connector):
        """Permanent errors are correctly classified (no retry)."""
        # Simulate 400 bad request
        with mock_graph_response(status_code=400):
            result = intune_connector.publish(package, correlation_id)

        assert result.error_class == "PERMANENT"
        assert result.should_retry is False

    def test_error_classification_policy_violation(self, intune_connector):
        """Policy violations are correctly classified."""
        # Simulate 403 forbidden
        with mock_graph_response(status_code=403):
            result = intune_connector.publish(package, correlation_id)

        assert result.error_class == "POLICY_VIOLATION"
        assert result.should_retry is False
```

---

## Unit Testing Patterns

### Django Model Tests

```python
# tests/test_models.py

import pytest
from decimal import Decimal
from apps.deployments.models import Deployment

@pytest.mark.django_db
class TestDeploymentModel:
    """Unit tests for Deployment model."""

    def test_requires_cab_approval_high_risk(self, deployment_factory):
        """Deployments with risk > 50 require CAB approval."""
        deployment = deployment_factory(risk_score=Decimal("75.00"))

        assert deployment.requires_cab_approval is True

    def test_requires_cab_approval_low_risk(self, deployment_factory):
        """Deployments with risk ≤ 50 don't require CAB approval."""
        deployment = deployment_factory(risk_score=Decimal("45.00"))

        assert deployment.requires_cab_approval is False

    def test_risk_score_constraint(self, deployment_factory):
        """Risk score must be between 0 and 100."""
        with pytest.raises(Exception):
            deployment_factory(risk_score=Decimal("150.00"))
```

### Django API Tests

```python
# tests/test_api.py

import pytest
from rest_framework import status
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestDeploymentAPI:
    """API tests for Deployment endpoints."""

    def test_list_deployments_authenticated(self, api_client, user, deployment_factory):
        """Authenticated users can list deployments."""
        api_client.force_authenticate(user=user)
        deployment_factory()
        deployment_factory()

        response = api_client.get("/api/v1/deployments/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_list_deployments_unauthenticated(self, api_client):
        """Unauthenticated requests are rejected."""
        response = api_client.get("/api/v1/deployments/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_deployment_calculates_risk(self, api_client, user, application):
        """Creating deployment automatically calculates risk score."""
        api_client.force_authenticate(user=user)

        response = api_client.post("/api/v1/deployments/", {
            "application_id": str(application.id),
            "version": "1.0.0",
            "target_ring": 0,
        })

        assert response.status_code == status.HTTP_201_CREATED
        assert "risk_score" in response.data
        assert 0 <= response.data["risk_score"] <= 100
```

### Service Layer Tests

```python
# tests/test_services.py

import pytest
from apps.policy_engine.services import calculate_risk_score

@pytest.mark.django_db
class TestRiskScoring:
    """Tests for risk scoring service."""

    def test_risk_score_formula(self):
        """Risk score follows documented formula."""
        factors = {
            "privilege_impact": 0.5,
            "supply_chain_trust": 0.2,
            "exploitability": 0.3,
        }
        weights = {
            "privilege_impact": 20,
            "supply_chain_trust": 15,
            "exploitability": 10,
        }

        # RiskScore = clamp(0..100, Σ(weight_i × normalized_factor_i))
        expected = (0.5 * 20) + (0.2 * 15) + (0.3 * 10)  # = 16

        result = calculate_risk_score(factors, weights)

        assert result == expected

    def test_risk_score_clamped(self):
        """Risk score is clamped between 0 and 100."""
        factors = {"all_high": 1.0}
        weights = {"all_high": 200}  # Would be 200 unclamped

        result = calculate_risk_score(factors, weights)

        assert result == 100  # Clamped to max
```

---

## Frontend Testing Patterns

### React Component Tests

```typescript
// DeploymentCard.test.tsx

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DeploymentCard } from './DeploymentCard';

describe('DeploymentCard', () => {
  const mockDeployment = {
    id: '123',
    name: 'Test App',
    status: 'pending',
    risk_score: 45,
  };

  it('renders deployment name', () => {
    render(<DeploymentCard deployment={mockDeployment} />);

    expect(screen.getByText('Test App')).toBeInTheDocument();
  });

  it('shows risk score', () => {
    render(<DeploymentCard deployment={mockDeployment} />);

    expect(screen.getByText(/45/)).toBeInTheDocument();
  });

  it('calls onApprove when approve button clicked', async () => {
    const onApprove = vi.fn();
    render(<DeploymentCard deployment={mockDeployment} onApprove={onApprove} />);

    await userEvent.click(screen.getByRole('button', { name: /approve/i }));

    expect(onApprove).toHaveBeenCalledWith('123');
  });
});
```

### Hook Tests

```typescript
// useDeployments.test.ts

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDeployments } from './hooks';

describe('useDeployments', () => {
  it('fetches deployments from API', async () => {
    const { result } = renderHook(() => useDeployments(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
  });
});
```

---

## PowerShell Testing (Pester)

```powershell
# tests/unit/Logging.Tests.ps1

Describe "Write-StructuredLog" {
    BeforeAll {
        . "$PSScriptRoot/../../utilities/Logging.ps1"
    }

    Context "When logging with correlation ID" {
        It "Should include correlation_id in output" {
            $output = Write-StructuredLog -Message "Test" -CorrelationId "test-123" 6>&1

            $parsed = $output | ConvertFrom-Json
            $parsed.correlation_id | Should -Be "test-123"
        }
    }

    Context "Error classification" {
        It "Should classify 429 as TRANSIENT" {
            $error = [System.Exception]::new("429 Too Many Requests")

            $result = Get-ErrorClassification -Exception $error

            $result | Should -Be "TRANSIENT"
        }

        It "Should classify 403 as POLICY_VIOLATION" {
            $error = [System.Exception]::new("403 Forbidden")

            $result = Get-ErrorClassification -Exception $error

            $result | Should -Be "POLICY_VIOLATION"
        }
    }
}
```

---

## Test Fixtures and Factories

### pytest Fixtures

```python
# conftest.py

import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        password="testpass123",
    )

@pytest.fixture
def deployment_factory(db):
    def create_deployment(**kwargs):
        from apps.deployments.models import Deployment
        defaults = {
            "name": "Test Deployment",
            "status": "pending",
            "risk_score": Decimal("25.00"),
        }
        defaults.update(kwargs)
        return Deployment.objects.create(**defaults)
    return create_deployment

@pytest.fixture
def correlation_id():
    from uuid import uuid4
    return str(uuid4())
```

---

## Pre-Commit Testing Enforcement

```yaml
# .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest --cov --cov-fail-under=90 -x
        language: system
        pass_filenames: false
        always_run: true

      - id: mypy
        name: mypy
        entry: mypy apps/
        language: system
        types: [python]

      - id: eslint
        name: eslint
        entry: npm run lint -- --max-warnings 0
        language: system
        files: \.(ts|tsx)$
```

---

## Checklist

### Before Submitting Code

```
☐ Unit tests written for all new code
☐ Integration tests for connector operations
☐ Idempotency tests for any retry-able operations
☐ Correlation ID isolation tests for Django apps
☐ Coverage ≥90% (run: pytest --cov --cov-fail-under=90)
☐ Pre-commit hooks pass (run: pre-commit run --all-files)
```

### Before Ring Promotion

```
☐ Ring 0 rollback validated
☐ All tests passing in CI
☐ Coverage threshold met (≥90%)
☐ No linting warnings (--max-warnings 0)
☐ Type checking passes (ZERO new errors)
```

---

## Anti-Patterns to Avoid

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Coverage < 90% | Coverage ≥ 90% enforced |
| Skipping idempotency tests | All connectors have idempotency tests |
| Missing rollback tests | Rollback validated before Ring 2+ |
| No correlation ID tests | Every Django app has isolation tests |
| Bypassing pre-commit hooks | ZERO bypasses allowed |
| `pytest.skip()` without reason | Skips documented and tracked |
