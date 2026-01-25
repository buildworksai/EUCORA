# EUCORA Coding Standards

**SPDX-License-Identifier: Apache-2.0**
**Version**: 1.0.0
**Last Updated**: January 8, 2026
**Authority**: REQUIRED — All Code Must Comply

---

## Purpose

This document defines coding standards for all Python (backend) and TypeScript (frontend) code in EUCORA. These standards are **MANDATORY** and enforced by pre-commit hooks and CI/CD pipelines.

**Related Documentation:**
- [Quality Gates](../architecture/quality-gates.md)
- [Testing Standards](../architecture/testing-standards.md)
- [AGENTS.md](../../AGENTS.md)
- [CLAUDE.md](../../CLAUDE.md)

---

## Python Standards (Backend)

### Dependency Management

**MANDATORY: Use `pyproject.toml` for all Python projects.**

```toml
[project]
name = "eucora-backend"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "django>=5.0.6",
    "djangorestframework>=3.15.1",
    # ... other dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "black>=24.0.0",
    "flake8>=7.2.0",
    "mypy>=1.8.0",
    # ... dev dependencies
]
```

**FORBIDDEN:** Do NOT use `requirements.txt`. This is a compliance violation.

### Formatting

| Tool | Configuration | Enforcement |
|------|---------------|-------------|
| Black | `line-length = 120` | Pre-commit |
| isort | `profile = black` | Pre-commit |
| Flake8 | `max-line-length = 120` | Pre-commit |

### Type Hints

**MANDATORY** for all functions and methods.

```python
# ✅ CORRECT
def get_deployment_intent(
    intent_id: str, correlation_id: str
) -> Optional[DeploymentIntent]:
    """Get deployment intent by ID with correlation ID validation."""
    return DeploymentIntent.objects.filter(
        id=intent_id, correlation_id=correlation_id
    ).first()

# ❌ WRONG - Missing type hints
def get_deployment_intent(intent_id, correlation_id):
    return DeploymentIntent.objects.filter(
        id=intent_id, correlation_id=correlation_id
    ).first()
```

### Docstrings

**REQUIRED** for all public functions, classes, and modules.

```python
def create_deployment_intent(
    app_id: str,
    ring: int,
    target_scope: dict,
    rollback_plan: dict,
    correlation_id: str,
) -> DeploymentIntent:
    """
    Create a new deployment intent for an application.

    Args:
        app_id: Application identifier
        ring: Target ring (0-4)
        target_scope: Target scope dictionary (site, BU, geography)
        rollback_plan: Rollback plan dictionary (plane-specific)
        correlation_id: Correlation ID for audit trail

    Returns:
        Created DeploymentIntent instance

    Raises:
        ValidationError: If target_scope is invalid or rollback_plan missing
        PermissionDenied: If user lacks deployment.create permission
    """
    ...
```

### Import Order

```python
# 1. Standard library
import uuid
from datetime import date, datetime
from typing import Optional, List

# 2. Third-party packages
from django.db import models, transaction
from rest_framework import viewsets, status

# 3. Local application
from apps.core.utils import get_correlation_id
from .models import DeploymentIntent, RingDeployment
from .services import DeploymentIntentService
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Module | snake_case | `deployment_intent_service.py` |
| Class | PascalCase | `DeploymentIntentService` |
| Function | snake_case | `create_deployment_intent` |
| Variable | snake_case | `deployment_status` |
| Constant | UPPER_SNAKE | `MAX_RING_LEVEL` |
| Private | _prefix | `_calculate_risk_score` |

### Django/DRF Standards

#### Model Definition

```python
class DeploymentIntent(models.Model):
    """Deployment intent model with correlation ID tracking."""

    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # CRITICAL: Correlation ID for audit trail
    correlation_id = models.UUIDField(db_index=True)

    # Foreign keys
    app = models.ForeignKey(
        'apps.App',
        on_delete=models.PROTECT,
        related_name='deployment_intents',
    )

    # Fields
    ring = models.IntegerField(choices=RingLevel.choices, default=RingLevel.LAB)
    status = models.CharField(
        max_length=20,
        choices=DeploymentStatus.choices,
        default=DeploymentStatus.PENDING,
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'deployment_intents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['correlation_id', 'status']),
            models.Index(fields=['correlation_id', 'app']),
        ]

    def __str__(self) -> str:
        return f"DeploymentIntent {self.id}"
```

#### ViewSet Definition

```python
class DeploymentIntentViewSet(viewsets.ModelViewSet):
    """
    API endpoints for deployment intents.

    CRITICAL:
    - Correlation ID filtering in get_queryset()
    - Permission checks on all actions
    - Audit logging on mutations
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return DeploymentIntentWriteSerializer
        return DeploymentIntentReadSerializer

    def get_queryset(self):
        """
        Filter by correlation_id.

        CRITICAL: This is the primary audit trail mechanism.
        """
        correlation_id = get_request_correlation_id(self.request)
        if not correlation_id:
            return DeploymentIntent.objects.none()

        queryset = DeploymentIntent.objects.filter(correlation_id=correlation_id)

        # Apply filters
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset.select_related('app')

    def perform_create(self, serializer):
        """Set correlation_id on create."""
        correlation_id = get_request_correlation_id(self.request)
        serializer.save(
            correlation_id=correlation_id,
            created_by=self.request.user.id,
        )
```

#### API View with AllowAny in DEBUG Mode

**CRITICAL**: When using `AllowAny if settings.DEBUG else IsAuthenticated` with POST/PUT/DELETE endpoints, you MUST exempt CSRF in DEBUG mode.

**Why**: DRF's `SessionAuthentication` enforces CSRF protection for state-changing operations even with `AllowAny` permission. In development with mock authentication, this causes 403 errors.

**Pattern**:

```python
from apps.core.utils import exempt_csrf_in_debug
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings

# ✅ CORRECT: CSRF exemption for AllowAny POST in DEBUG
@exempt_csrf_in_debug
@api_view(['POST'])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def my_endpoint(request):
    """Endpoint that allows unauthenticated access in development."""
    # Implementation
    pass

# ❌ WRONG: Missing CSRF exemption (will cause 403 in DEBUG)
@api_view(['POST'])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def my_endpoint(request):
    # This will fail with 403 in development
    pass
```

**Security Note**:
- CSRF exemption is **only active in DEBUG mode** (`settings.DEBUG=True`)
- In production (`DEBUG=False`), CSRF protection is **fully enforced**
- This maintains security in production while allowing development workflows

**Location**: `apps.core.utils.exempt_csrf_in_debug`

#### Service Layer Pattern

```python
class DeploymentIntentService:
    """
    Business logic for deployment intents.

    CRITICAL:
    - All business logic in services, NOT in ViewSets
    - All database operations wrapped in transactions
    - All correlation ID access validated
    """

    @staticmethod
    def create_deployment_intent(
        app_id: str,
        ring: int,
        target_scope: dict,
        rollback_plan: dict,
        correlation_id: str,
        user_id: str,
    ) -> DeploymentIntent:
        """
        Create deployment intent with validation.

        Args:
            app_id: Application to deploy
            ring: Target ring (0-4)
            target_scope: Target scope dictionary
            rollback_plan: Rollback plan dictionary
            correlation_id: Correlation ID for audit
            user_id: Creating user (for audit)

        Returns:
            Created DeploymentIntent

        Raises:
            ValidationError: Invalid data
            App.DoesNotExist: App not found
        """
        # Validate app exists
        app = App.objects.get(id=app_id)

        with transaction.atomic():
            # Create deployment intent
            intent = DeploymentIntent.objects.create(
                app=app,
                ring=ring,
                target_scope=target_scope,
                rollback_plan=rollback_plan,
                correlation_id=correlation_id,
                created_by=user_id,
            )

            # Emit event for other modules
            EventBus.emit('deployment_intent.created', {
                'intent_id': str(intent.id),
                'correlation_id': str(correlation_id),
                'ring': ring,
            })

        return intent
```

---

## TypeScript Standards (Frontend)

### Formatting

| Tool | Configuration | Enforcement |
|------|---------------|-------------|
| Prettier | Default | Pre-commit |
| ESLint | `--max-warnings 0` | Pre-commit |

### Type Safety

**NO `any` type allowed.** Use explicit types.

```typescript
// ✅ CORRECT
interface DeploymentIntent {
  id: string;
  correlation_id: string;
  app_id: string;
  ring: number;
  status: 'pending' | 'approved' | 'deploying' | 'completed' | 'failed';
  target_scope: {
    site?: string;
    business_unit?: string;
    geography?: string;
  };
}

async function fetchDeploymentIntent(
  intentId: string
): Promise<DeploymentIntent> {
  const response = await api.get<DeploymentIntent>(
    `/api/v1/deployments/${intentId}/`
  );
  return response.data;
}

// ❌ WRONG - Using any
async function fetchDeploymentIntent(intentId: any): Promise<any> {
  const response = await api.get(`/api/v1/deployments/${intentId}/`);
  return response.data;
}
```

### Component Structure

```typescript
// Component file structure
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

// Types
interface Props {
  intentId: string;
}

// Component
export function DeploymentIntentDetail({ intentId }: Props) {
  // ✅ ALL HOOKS FIRST (before any early returns)
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const { data, isLoading, error } = useQuery({
    queryKey: ['deployment-intent', intentId],
    queryFn: () => fetchDeploymentIntent(intentId),
  });

  // ✅ Early returns AFTER all hooks
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!data) return null;

  // Main render
  return (
    <div className="deployment-intent-detail">
      {/* ... */}
    </div>
  );
}
```

### React Hooks Rules (CRITICAL)

**⚠️ CRITICAL**: All React hooks MUST be called before any conditional early returns.

**✅ CORRECT Hook Placement:**
```typescript
export function Component() {
  // ✅ ALL HOOKS FIRST (before any early returns)
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [state, setState] = useState('');
  const { data } = useQuery(...);
  const memoized = useMemo(() => compute(data), [data]);
  const callback = useCallback(() => handle(), []);

  // ✅ Early returns AFTER all hooks
  if (!hasRole('admin')) {
    return <AccessDenied />;
  }

  if (isLoading) {
    return <Loading />;
  }

  return <Content data={memoized} />;
}
```

**❌ FORBIDDEN Hook Placement:**
```typescript
export function Component() {
  const navigate = useNavigate();

  if (someCondition) {
    return <EarlyReturn />; // ❌ WRONG - hook called before this
  }

  const { data } = useQuery(...); // ❌ WRONG - hook after early return
  // ...
}
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Component | PascalCase | `DeploymentIntentList.tsx` |
| Hook | camelCase, use prefix | `useDeploymentIntents.ts` |
| Utility | camelCase | `formatDate.ts` |
| Type/Interface | PascalCase | `DeploymentIntent`, `RingDeployment` |
| Constant | UPPER_SNAKE | `MAX_RING_LEVEL` |

### Module Contracts Architecture

**Every frontend app/domain MUST have a `contracts.ts` file.**

```typescript
// frontend/src/apps/deployments/contracts.ts

// === AGENT INSTRUCTION ===
// Read this file FIRST when working on this module.
// All types and endpoints are defined here.

import type { components } from "@/types/api";

// === EXPORTED TYPES ===
export type DeploymentIntent = components["schemas"]["DeploymentIntent"];
export type DeploymentIntentCreate = components["schemas"]["DeploymentIntentCreate"];

// === ENDPOINT REGISTRY ===
export const ENDPOINTS = {
  DEPLOYMENTS: {
    LIST: "/api/v1/deployments/",
    DETAIL: (id: string) => `/api/v1/deployments/${id}/` as const,
    CREATE: "/api/v1/deployments/",
    UPDATE: (id: string) => `/api/v1/deployments/${id}/` as const,
    DELETE: (id: string) => `/api/v1/deployments/${id}/` as const,
  },
} as const;
```

**Benefits:**
- Single source of truth for module types
- Prevents endpoint URL drift
- Enables type safety across the module

---

## Testing Standards

### Test Structure

**Backend:**
- `test_models.py` — Model tests
- `test_api.py` — API endpoint tests
- `test_services.py` — Service layer tests
- `test_correlation_isolation.py` — **MANDATORY** for correlation ID isolation

**Frontend:**
- `*.test.tsx` — Component tests
- `*.test.ts` — Utility/hook tests
- Integration tests in `__tests__/` directory

### Coverage Requirements

- **≥90% coverage** enforced by CI
- Tests MUST cover: happy paths, edge cases, errors, isolation

---

## Git Commit Standards

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Usage |
|------|-------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation |
| style | Formatting (no code change) |
| refactor | Code restructure |
| test | Adding tests |
| chore | Maintenance |

### Examples

```
feat(deployments): add ring-based rollout orchestration

- Add DeploymentIntent model with ring state machine
- Implement promotion gate evaluation
- Add rollback strategy validation

Closes #123
```

---

## Enforcement

| Standard | Requirement | Enforcement |
|----------|-------------|-------------|
| Type hints | Mandatory for all functions | Pre-commit + CI |
| Docstrings | Required for public APIs | Pre-commit + CI |
| TypeScript strict mode | Enabled | Pre-commit + CI |
| No `any` types | Forbidden | ESLint + CI |
| React hooks rules | Hooks before early returns | ESLint + CI |
| Test coverage | ≥90% | CI (blocking) |

---

**Classification**: PROPRIETARY — REQUIRED
**Enforcement**: PRE-COMMIT HOOKS + CI/CD
**Review**: Code review required for all changes
