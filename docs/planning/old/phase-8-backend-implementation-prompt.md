# Phase 8: Backend Control Plane (Django) - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 4 weeks
**Dependencies**: Phase 1 (Foundation utilities), Phase 2 (CLI - revised)

---

## Task Overview

Implement the **Django-based Control Plane** as the authoritative backend for the Enterprise Endpoint Application Packaging & Deployment Factory. This phase replaces the originally planned PowerShell (Pode) API Gateway with a production-grade Django + DRF stack, while preserving PowerShell for execution plane connectors.

**Success Criteria**:
- Django Control Plane API operational with authentication, RBAC, and audit logging
- 6 core components implemented (API Gateway, Policy Engine, Orchestrator, CAB Workflow, Evidence Store, Event Store)
- REST API matches OpenAPI specification from `docs/api/control-plane-api.yaml`
- Session-based authentication with Entra ID OAuth2 integration
- PostgreSQL database with tenant-scoped schema and append-only event store
- ≥90% test coverage across all Django apps
- PowerShell connectors successfully integrated with Django API

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Thin Control Plane**: Policy + Orchestration + Evidence only (no direct endpoint management)
- ✅ **Deterministic Risk Scoring**: Formula-based, no AI/ML decisions
- ✅ **Evidence-First**: All CAB submissions backed by complete evidence packs
- ✅ **Separation of Duties**: Django enforces RBAC, PowerShell connectors scoped per execution plane
- ✅ **Idempotency**: All API operations safe to retry with correlation IDs

### Quality Standards
- ✅ **Black + Flake8**: Auto-formatted code, ZERO linting warnings (`--max-warnings 0`)
- ✅ **mypy with django-stubs**: Type safety enforced, ZERO new type errors
- ✅ **pytest-django**: ≥90% test coverage per Django app
- ✅ **API Contract Tests**: OpenAPI spec validation via drf-spectacular
- ✅ **Pre-Commit Hooks**: Enforced blocking (see `.pre-commit-config.yaml`)

### Security Requirements
- ✅ **Authentication**: Session-based with Entra ID OAuth2 (MSAL integration)
- ✅ **Authorization**: Policy Engine (ABAC) + Django permissions
- ✅ **Secrets**: Azure Key Vault integration (no hardcoded credentials)
- ✅ **Audit Trail**: Every operation logged to Event Store with correlation ID
- ✅ **SIEM**: Privileged actions forwarded to Azure Sentinel

---

## Scope: Django Project Structure

### Project Layout
```
backend/
├── manage.py
├── pyproject.toml                    # Poetry/pip-tools dependency management
├── .env.example                      # Environment variable template
├── requirements/
│   ├── base.txt                      # Shared dependencies
│   ├── development.txt               # Dev-only (pytest, black, etc.)
│   └── production.txt                # Production-only (gunicorn, etc.)
├── config/                           # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                   # Base settings
│   │   ├── development.py            # Dev overrides
│   │   ├── staging.py                # Staging overrides
│   │   └── production.py             # Production settings
│   ├── urls.py                       # Root URL configuration
│   ├── wsgi.py                       # WSGI entry point
│   └── asgi.py                       # ASGI entry point (async support)
├── apps/                             # Django applications
│   ├── core/                         # Shared utilities, base models
│   ├── authentication/               # Entra ID OAuth2 + session management
│   ├── policy_engine/                # ABAC evaluation, risk scoring
│   ├── deployment_intents/           # Deployment orchestration
│   ├── cab_workflow/                 # CAB approval workflows
│   ├── evidence_store/               # Artifact/evidence management
│   ├── event_store/                  # Append-only audit trail
│   ├── connectors/                   # PowerShell connector API endpoints
│   └── telemetry/                    # Metrics, health checks
├── tests/                            # Integration tests
│   ├── integration/
│   ├── fixtures/
│   └── conftest.py                   # pytest configuration
└── scripts/                          # Management scripts (migrations, seed data)
```

---

## Phase 8.1: Django Project Initialization (Week 1, Days 1-2)

### Deliverables
1. Django project scaffolding with settings modules
2. PostgreSQL database configuration (docker-compose.yml)
3. Redis session store configuration
4. Initial migration (`0001_initial.py` for each app)
5. Docker Compose development environment

### Implementation Steps

#### 1. Initialize Django Project
```bash
# From /Users/raghunathchava/Code/EUCORA/
mkdir backend
cd backend
poetry init --name eucora-control-plane --python "^3.12"
poetry add django djangorestframework django-cors-headers drf-spectacular
poetry add psycopg2-binary django-redis python-decouple
poetry add --group dev pytest-django pytest-cov black flake8 django-stubs mypy
django-admin startproject config .
```

#### 2. Settings Structure
**File**: `backend/config/settings/base.py`

```python
"""
Base settings for EUCORA Control Plane.
"""
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = config('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    # Local apps
    'apps.core',
    'apps.authentication',
    'apps.policy_engine',
    'apps.deployment_intents',
    'apps.cab_workflow',
    'apps.evidence_store',
    'apps.event_store',
    'apps.connectors',
    'apps.telemetry',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.CorrelationIdMiddleware',  # Custom
]

ROOT_URLCONF = 'config.urls'

# Database (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='eucora'),
        'USER': config('POSTGRES_USER', default='eucora_user'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432', cast=int),
    }
}

# Redis (Session Store)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# DRF Spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'EUCORA Control Plane API',
    'DESCRIPTION': 'Enterprise Endpoint Application Packaging & Deployment Factory',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS (for frontend development)
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173',  # Vite default port
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
}
```

#### 3. Docker Compose Development Environment
**File**: `backend/docker-compose.dev.yml`

```yaml
version: '3.9'

services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: eucora
      POSTGRES_USER: eucora_user
      POSTGRES_PASSWORD: eucora_dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: .
      dockerfile: Dockerfile.dev
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DATABASE_URL=postgresql://eucora_user:eucora_dev_password@db:5432/eucora
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:
  redis_data:
```

**Pester Tests Required** (PowerShell connectors integration):
- Django API responds to health check (`GET /api/v1/health`)
- PostgreSQL connection successful
- Redis session store accessible

---

## Phase 8.2: Core Django Apps (Week 1, Days 3-5)

### App 1: `apps/core` (Shared Utilities)

**Purpose**: Base models, utilities, middleware shared across all apps.

**Models**: `backend/apps/core/models.py`

```python
"""
Core models and utilities.
"""
from django.db import models
from django.utils import timezone
import uuid


class TimeStampedModel(models.Model):
    """Abstract base with created_at and updated_at."""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CorrelationIdModel(models.Model):
    """Abstract base with correlation_id for audit trail."""
    correlation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True
```

**Middleware**: `backend/apps/core/middleware.py`

```python
"""
Custom middleware for correlation ID injection.
"""
import uuid
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Inject correlation_id into request and log context.
    """
    def process_request(self, request):
        # Extract from header or generate new
        correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        request.correlation_id = correlation_id

        # Inject into logging context
        logger = logging.LoggerAdapter(
            logging.getLogger(__name__),
            {'correlation_id': correlation_id}
        )
        request.logger = logger

    def process_response(self, request, response):
        # Add correlation ID to response headers
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        return response
```

### App 2: `apps/authentication` (Entra ID OAuth2)

**Purpose**: Session-based authentication with Entra ID integration.

**Views**: `backend/apps/authentication/views.py`

```python
"""
Authentication views for Entra ID OAuth2.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
import requests
from decouple import config


@api_view(['POST'])
@permission_classes([AllowAny])
def entra_id_login(request):
    """
    Exchange Entra ID authorization code for user session.

    POST /api/v1/auth/login
    Body: {"code": "..."}
    """
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Authorization code required'}, status=status.HTTP_400_BAD_REQUEST)

    # Exchange code for token (MSAL backend handles this in frontend)
    # Backend validates token and creates session
    token_data = _exchange_code_for_token(code)

    if not token_data:
        return Response({'error': 'Invalid authorization code'}, status=status.HTTP_401_UNAUTHORIZED)

    # Get or create user from Entra ID profile
    user_profile = _get_user_profile(token_data['access_token'])
    user, created = User.objects.get_or_create(
        username=user_profile['userPrincipalName'],
        defaults={
            'email': user_profile['mail'],
            'first_name': user_profile.get('givenName', ''),
            'last_name': user_profile.get('surname', ''),
        }
    )

    # Create Django session
    login(request, user)

    return Response({
        'user': {
            'username': user.username,
            'email': user.email,
        },
        'session_id': request.session.session_key,
    })


@api_view(['POST'])
def auth_logout(request):
    """
    Logout and destroy session.

    POST /api/v1/auth/logout
    """
    logout(request)
    return Response({'message': 'Logged out successfully'})


def _exchange_code_for_token(code: str) -> dict:
    """Exchange authorization code for access token via Entra ID."""
    # Implementation: POST to https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
    # with grant_type=authorization_code
    pass


def _get_user_profile(access_token: str) -> dict:
    """Fetch user profile from Microsoft Graph API."""
    # Implementation: GET https://graph.microsoft.com/v1.0/me
    pass
```

**Tests**: `backend/apps/authentication/tests/test_views.py`

```python
"""
Tests for authentication views.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_login_with_valid_code():
    """Test successful login with valid Entra ID code."""
    client = APIClient()
    response = client.post(reverse('auth:login'), {'code': 'valid_test_code'})
    assert response.status_code == 200
    assert 'session_id' in response.data


@pytest.mark.django_db
def test_login_without_code():
    """Test login fails without authorization code."""
    client = APIClient()
    response = client.post(reverse('auth:login'), {})
    assert response.status_code == 400
```

---

## Phase 8.3: Policy Engine & Risk Scoring (Week 2)

### App 3: `apps/policy_engine`

**Purpose**: ABAC evaluation, risk score calculation, promotion gate validation.

**Models**: `backend/apps/policy_engine/models.py`

```python
"""
Policy engine models for risk assessment.
"""
from django.db import models
from apps.core.models import TimeStampedModel
import json


class RiskModel(TimeStampedModel):
    """
    Versioned risk scoring model.
    """
    version = models.CharField(max_length=10, unique=True)  # e.g., "v1.0"
    factors = models.JSONField()  # List of factors with weights
    threshold = models.IntegerField(default=50)  # CAB approval threshold
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-version']


class RiskAssessment(TimeStampedModel):
    """
    Risk assessment result for a deployment intent.
    """
    deployment_intent = models.OneToOneField('deployment_intents.DeploymentIntent', on_delete=models.CASCADE)
    risk_model_version = models.CharField(max_length=10)
    risk_score = models.IntegerField()  # 0-100
    factor_scores = models.JSONField()  # Detailed breakdown per factor
    requires_cab_approval = models.BooleanField()

    class Meta:
        indexes = [
            models.Index(fields=['risk_score']),
        ]
```

**Risk Scoring Logic**: `backend/apps/policy_engine/services.py`

```python
"""
Risk scoring service implementation.
"""
from apps.policy_engine.models import RiskModel, RiskAssessment
from typing import Dict


def calculate_risk_score(evidence_pack: Dict) -> Dict:
    """
    Calculate risk score from evidence pack using active risk model.

    Returns:
        {
            'risk_score': int (0-100),
            'factor_scores': dict,
            'requires_cab_approval': bool,
            'model_version': str,
        }
    """
    risk_model = RiskModel.objects.filter(is_active=True).first()
    if not risk_model:
        raise ValueError("No active risk model found")

    factor_scores = {}
    weighted_sum = 0.0

    for factor in risk_model.factors:
        name = factor['name']
        weight = factor['weight']
        rubric = factor['rubric']

        # Evaluate factor score (0.0 - 1.0) based on evidence pack
        normalized_score = _evaluate_factor(name, evidence_pack, rubric)
        factor_scores[name] = normalized_score

        weighted_sum += weight * normalized_score

    # Clamp to 0-100
    risk_score = int(max(0, min(100, weighted_sum * 100)))

    return {
        'risk_score': risk_score,
        'factor_scores': factor_scores,
        'requires_cab_approval': risk_score > risk_model.threshold,
        'model_version': risk_model.version,
    }


def _evaluate_factor(factor_name: str, evidence_pack: Dict, rubric: Dict) -> float:
    """
    Evaluate a single risk factor.

    Args:
        factor_name: Name of the factor (e.g., "Privilege Elevation")
        evidence_pack: Complete evidence pack data
        rubric: Scoring rubric for this factor

    Returns:
        Normalized score (0.0 - 1.0)
    """
    # Implementation: Map evidence pack fields to rubric scores
    # Example for "Privilege Elevation":
    if factor_name == "Privilege Elevation":
        if evidence_pack.get('requires_admin'):
            return 1.0
        elif evidence_pack.get('requests_elevation'):
            return 0.5
        else:
            return 0.0

    # TODO: Implement all 8 factors from risk-model.md
    return 0.5  # Default placeholder
```

**Tests**: `backend/apps/policy_engine/tests/test_services.py`

```python
"""
Tests for risk scoring service.
"""
import pytest
from apps.policy_engine.services import calculate_risk_score
from apps.policy_engine.models import RiskModel


@pytest.fixture
def active_risk_model(db):
    """Create active risk model v1.0."""
    return RiskModel.objects.create(
        version='v1.0',
        threshold=50,
        is_active=True,
        factors=[
            {'name': 'Privilege Elevation', 'weight': 0.25, 'rubric': {}},
            {'name': 'Blast Radius', 'weight': 0.20, 'rubric': {}},
            # ... 6 more factors
        ]
    )


@pytest.mark.django_db
def test_high_risk_requires_cab_approval(active_risk_model):
    """Test high-risk deployment requires CAB approval."""
    evidence_pack = {
        'requires_admin': True,
        'blast_radius': 'global',
        # ... other fields
    }

    result = calculate_risk_score(evidence_pack)

    assert result['risk_score'] > 50
    assert result['requires_cab_approval'] is True


@pytest.mark.django_db
def test_low_risk_bypasses_cab(active_risk_model):
    """Test low-risk deployment bypasses CAB."""
    evidence_pack = {
        'requires_admin': False,
        'blast_radius': 'lab',
    }

    result = calculate_risk_score(evidence_pack)

    assert result['risk_score'] <= 50
    assert result['requires_cab_approval'] is False
```

---

## Phase 8.4: Deployment Intents & Orchestration (Week 2-3)

### App 4: `apps/deployment_intents`

**Purpose**: Deployment state machine, ring orchestration, promotion gates.

**Models**: `backend/apps/deployment_intents/models.py`

```python
"""
Deployment intent models and state machine.
"""
from django.db import models
from apps.core.models import TimeStampedModel, CorrelationIdModel
from django.contrib.auth.models import User


class DeploymentIntent(TimeStampedModel, CorrelationIdModel):
    """
    Represents a deployment request across rings.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AWAITING_CAB = 'AWAITING_CAB', 'Awaiting CAB Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        DEPLOYING = 'DEPLOYING', 'Deploying'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        ROLLED_BACK = 'ROLLED_BACK', 'Rolled Back'

    class Ring(models.TextChoices):
        LAB = 'LAB', 'Lab'
        CANARY = 'CANARY', 'Canary'
        PILOT = 'PILOT', 'Pilot'
        DEPARTMENT = 'DEPARTMENT', 'Department'
        GLOBAL = 'GLOBAL', 'Global'

    app_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    target_ring = models.CharField(max_length=20, choices=Ring.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # Evidence pack (JSON reference to artifact storage)
    evidence_pack_id = models.UUIDField()

    # Risk assessment
    risk_score = models.IntegerField(null=True, blank=True)
    requires_cab_approval = models.BooleanField(default=False)

    # CAB workflow link
    cab_approval = models.OneToOneField('cab_workflow.CABApproval', on_delete=models.SET_NULL, null=True, blank=True)

    # Submitter
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deployment_intents')

    class Meta:
        indexes = [
            models.Index(fields=['status', 'target_ring']),
            models.Index(fields=['correlation_id']),
        ]
        ordering = ['-created_at']


class RingDeployment(TimeStampedModel):
    """
    Tracks deployment progress within a specific ring.
    """
    deployment_intent = models.ForeignKey(DeploymentIntent, on_delete=models.CASCADE, related_name='ring_deployments')
    ring = models.CharField(max_length=20, choices=DeploymentIntent.Ring.choices)

    # Execution plane tracking
    connector_type = models.CharField(max_length=20)  # 'intune', 'jamf', 'sccm', etc.
    connector_object_id = models.CharField(max_length=255, null=True, blank=True)  # Platform-specific ID

    # Metrics
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)

    # Promotion status
    promoted_at = models.DateTimeField(null=True, blank=True)
    promotion_gate_passed = models.BooleanField(default=False)
```

**API Views**: `backend/apps/deployment_intents/views.py`

```python
"""
Deployment intent API views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeploymentIntent
from .serializers import DeploymentIntentSerializer
from apps.policy_engine.services import calculate_risk_score


class DeploymentIntentViewSet(viewsets.ModelViewSet):
    """
    API endpoints for deployment intents.

    POST /api/v1/deployment-intents/ - Create deployment intent
    GET /api/v1/deployment-intents/ - List deployment intents
    GET /api/v1/deployment-intents/{id}/ - Get deployment intent details
    """
    queryset = DeploymentIntent.objects.all()
    serializer_class = DeploymentIntentSerializer

    def create(self, request, *args, **kwargs):
        """
        Create deployment intent with risk assessment.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Calculate risk score
        evidence_pack_data = request.data.get('evidence_pack', {})
        risk_result = calculate_risk_score(evidence_pack_data)

        # Create intent with risk assessment
        deployment_intent = serializer.save(
            submitter=request.user,
            risk_score=risk_result['risk_score'],
            requires_cab_approval=risk_result['requires_cab_approval'],
            status=DeploymentIntent.Status.AWAITING_CAB if risk_result['requires_cab_approval'] else DeploymentIntent.Status.APPROVED
        )

        # Log to event store
        self._log_event(deployment_intent, 'INTENT_CREATED', risk_result)

        return Response(
            self.get_serializer(deployment_intent).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def promote_ring(self, request, pk=None):
        """
        Promote deployment to next ring (with promotion gate validation).

        POST /api/v1/deployment-intents/{id}/promote_ring/
        """
        intent = self.get_object()

        # Validate promotion gates
        if not self._validate_promotion_gates(intent):
            return Response(
                {'error': 'Promotion gates not met'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Promote to next ring
        next_ring = self._get_next_ring(intent.target_ring)
        intent.target_ring = next_ring
        intent.save()

        self._log_event(intent, 'RING_PROMOTED', {'new_ring': next_ring})

        return Response(self.get_serializer(intent).data)

    def _validate_promotion_gates(self, intent: DeploymentIntent) -> bool:
        """Validate promotion gate thresholds."""
        # Implementation: Check success rate, time-to-compliance, rollback validation
        return True  # Placeholder

    def _get_next_ring(self, current_ring: str) -> str:
        """Get next ring in sequence."""
        rings = ['LAB', 'CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL']
        current_index = rings.index(current_ring)
        return rings[current_index + 1] if current_index < len(rings) - 1 else current_ring

    def _log_event(self, intent: DeploymentIntent, event_type: str, metadata: dict):
        """Log event to event store."""
        from apps.event_store.models import DeploymentEvent
        DeploymentEvent.objects.create(
            correlation_id=intent.correlation_id,
            event_type=event_type,
            deployment_intent=intent,
            metadata=metadata,
        )
```

**Tests**: `backend/apps/deployment_intents/tests/test_views.py`

```python
"""
Tests for deployment intent views.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.deployment_intents.models import DeploymentIntent


@pytest.mark.django_db
def test_create_deployment_intent_high_risk(authenticated_client, active_risk_model):
    """Test creating high-risk deployment intent requires CAB approval."""
    response = authenticated_client.post(
        reverse('deployment-intents-list'),
        {
            'app_name': 'Notepad++',
            'version': '8.5.1',
            'target_ring': 'CANARY',
            'evidence_pack': {'requires_admin': True}
        }
    )

    assert response.status_code == 201
    assert response.data['status'] == 'AWAITING_CAB'
    assert response.data['requires_cab_approval'] is True


@pytest.mark.django_db
def test_create_deployment_intent_low_risk(authenticated_client, active_risk_model):
    """Test creating low-risk deployment intent bypasses CAB."""
    response = authenticated_client.post(
        reverse('deployment-intents-list'),
        {
            'app_name': '7-Zip',
            'version': '24.0.0',
            'target_ring': 'CANARY',
            'evidence_pack': {'requires_admin': False}
        }
    )

    assert response.status_code == 201
    assert response.data['status'] == 'APPROVED'
    assert response.data['requires_cab_approval'] is False
```

---

## Phase 8.5: CAB Workflow & Evidence Store (Week 3)

### App 5: `apps/cab_workflow`

**Models**: `backend/apps/cab_workflow/models.py`

```python
"""
CAB (Change Advisory Board) workflow models.
"""
from django.db import models
from apps.core.models import TimeStampedModel
from django.contrib.auth.models import User


class CABApproval(TimeStampedModel):
    """
    CAB approval record for high-risk deployments.
    """
    class Decision(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CONDITIONAL = 'CONDITIONAL', 'Approved with Conditions'

    deployment_intent = models.OneToOneField('deployment_intents.DeploymentIntent', on_delete=models.CASCADE)
    decision = models.CharField(max_length=20, choices=Decision.choices, default=Decision.PENDING)

    # Approver details
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cab_approvals')
    approval_date = models.DateTimeField(null=True, blank=True)

    # Comments and conditions
    comments = models.TextField(blank=True)
    conditions = models.JSONField(default=list, blank=True)  # List of conditions for CONDITIONAL approval

    # Audit trail
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']
```

### App 6: `apps/evidence_store`

**Models**: `backend/apps/evidence_store/models.py`

```python
"""
Evidence store for artifact metadata and evidence packs.
"""
from django.db import models
from apps.core.models import TimeStampedModel, CorrelationIdModel


class EvidencePack(TimeStampedModel, CorrelationIdModel):
    """
    Immutable evidence pack for CAB submission.
    """
    deployment_intent = models.ForeignKey('deployment_intents.DeploymentIntent', on_delete=models.CASCADE)

    # Artifact metadata
    artifact_hash = models.CharField(max_length=64)  # SHA-256
    artifact_signature = models.TextField()  # Code signing certificate details
    artifact_storage_url = models.URLField()  # MinIO/Blob Storage URL

    # SBOM and vulnerability scan
    sbom_data = models.JSONField()  # SPDX/CycloneDX format
    vulnerability_scan_results = models.JSONField()
    scan_policy_decision = models.CharField(max_length=20)  # 'PASS', 'FAIL', 'EXCEPTION'

    # Exception tracking (if scan_policy_decision == 'EXCEPTION')
    exception_reason = models.TextField(blank=True)
    exception_expiry_date = models.DateTimeField(null=True, blank=True)
    compensating_controls = models.JSONField(default=list, blank=True)

    # Rollback plan
    rollback_plan = models.JSONField()  # Platform-specific rollback strategies

    # Test evidence
    test_evidence = models.JSONField(default=dict, blank=True)  # Lab + Ring 0 test results

    class Meta:
        indexes = [
            models.Index(fields=['correlation_id']),
            models.Index(fields=['artifact_hash']),
        ]
```

---

## Phase 8.6: Event Store & Telemetry (Week 3-4)

### App 7: `apps/event_store`

**Models**: `backend/apps/event_store/models.py`

```python
"""
Append-only event store for audit trail.
"""
from django.db import models
from apps.core.models import TimeStampedModel


class DeploymentEvent(TimeStampedModel):
    """
    Immutable deployment event for audit trail.

    This table is APPEND-ONLY. No updates or deletes allowed.
    """
    correlation_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=50)  # e.g., 'INTENT_CREATED', 'RING_PROMOTED', 'ROLLBACK_INITIATED'

    # Event metadata
    deployment_intent = models.ForeignKey('deployment_intents.DeploymentIntent', on_delete=models.CASCADE, related_name='events')
    metadata = models.JSONField(default=dict)

    # Classification
    error_classification = models.CharField(
        max_length=30,
        choices=[
            ('NONE', 'None'),
            ('TRANSIENT', 'Transient'),
            ('PERMANENT', 'Permanent'),
            ('POLICY_VIOLATION', 'Policy Violation'),
        ],
        default='NONE'
    )

    class Meta:
        indexes = [
            models.Index(fields=['correlation_id', 'created_at']),
            models.Index(fields=['event_type']),
        ]
        ordering = ['created_at']
        permissions = [
            ('view_audit_trail', 'Can view audit trail'),
        ]

    def save(self, *args, **kwargs):
        """Override save to enforce append-only behavior."""
        if self.pk:
            raise ValueError("Cannot update existing event (append-only store)")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion."""
        raise ValueError("Cannot delete events (append-only store)")
```

### App 8: `apps/telemetry`

**Views**: `backend/apps/telemetry/views.py`

```python
"""
Telemetry and health check endpoints.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint.

    GET /api/v1/health
    """
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check Redis connectivity
    from django.core.cache import cache
    try:
        cache.set('health_check', 'ok', 10)
        redis_status = "healthy" if cache.get('health_check') == 'ok' else "unhealthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return Response({
        'status': 'healthy' if db_status == 'healthy' and redis_status == 'healthy' else 'degraded',
        'components': {
            'database': db_status,
            'redis': redis_status,
        },
        'version': '1.0.0',
    })
```

---

## Phase 8.7: Connector API Integration (Week 4)

### App 9: `apps/connectors`

**Purpose**: API endpoints for PowerShell connectors to report deployment status and query intents.

**Views**: `backend/apps/connectors/views.py`

```python
"""
Connector API endpoints for PowerShell execution plane scripts.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.deployment_intents.models import DeploymentIntent, RingDeployment


class ConnectorAPIViewSet(viewsets.ViewSet):
    """
    API endpoints for PowerShell connectors.

    GET /api/v1/connectors/pending-deployments/?connector_type=intune&ring=CANARY
    POST /api/v1/connectors/update-deployment-status/
    """

    @action(detail=False, methods=['get'])
    def pending_deployments(self, request):
        """
        Get pending deployments for a connector and ring.

        Query Params:
            connector_type: 'intune', 'jamf', 'sccm', 'landscape', 'ansible'
            ring: 'LAB', 'CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL'
        """
        connector_type = request.query_params.get('connector_type')
        ring = request.query_params.get('ring')

        deployments = DeploymentIntent.objects.filter(
            status=DeploymentIntent.Status.APPROVED,
            target_ring=ring,
        )

        # Format for PowerShell consumption
        return Response([
            {
                'correlation_id': str(d.correlation_id),
                'app_name': d.app_name,
                'version': d.version,
                'evidence_pack_id': str(d.evidence_pack_id),
            }
            for d in deployments
        ])

    @action(detail=False, methods=['post'])
    def update_deployment_status(self, request):
        """
        Update deployment status from PowerShell connector.

        POST Body:
        {
            "correlation_id": "...",
            "ring": "CANARY",
            "connector_type": "intune",
            "connector_object_id": "app-123",
            "success_count": 95,
            "failure_count": 5
        }
        """
        correlation_id = request.data.get('correlation_id')
        ring = request.data.get('ring')
        connector_type = request.data.get('connector_type')

        try:
            intent = DeploymentIntent.objects.get(correlation_id=correlation_id)
        except DeploymentIntent.DoesNotExist:
            return Response({'error': 'Deployment intent not found'}, status=404)

        # Update or create ring deployment
        ring_deployment, created = RingDeployment.objects.update_or_create(
            deployment_intent=intent,
            ring=ring,
            connector_type=connector_type,
            defaults={
                'connector_object_id': request.data.get('connector_object_id'),
                'success_count': request.data.get('success_count', 0),
                'failure_count': request.data.get('failure_count', 0),
                'success_rate': request.data.get('success_count', 0) / (request.data.get('success_count', 0) + request.data.get('failure_count', 1)) * 100,
            }
        )

        return Response({'status': 'updated'})
```

**PowerShell Integration Example** (from `scripts/connectors/intune/IntuneConnector.ps1`):

```powershell
function Publish-ToControlPlane {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,

        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentStatus
    )

    $apiUri = Get-ConfigValue -Key "ControlPlaneApiUri"
    $sessionToken = Get-ControlPlaneSession

    $body = @{
        correlation_id = $CorrelationId
        ring = $DeploymentStatus.Ring
        connector_type = "intune"
        connector_object_id = $DeploymentStatus.IntuneAppId
        success_count = $DeploymentStatus.SuccessCount
        failure_count = $DeploymentStatus.FailureCount
    } | ConvertTo-Json

    Invoke-RestMethod -Uri "$apiUri/api/v1/connectors/update-deployment-status/" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -Headers @{ "Cookie" = "sessionid=$sessionToken" }
}
```

---

## Quality Checklist

### Per Django App
- [ ] PSScriptAnalyzer equivalent (Black + Flake8) passes with ZERO errors/warnings
- [ ] mypy type checking passes with ZERO new errors
- [ ] pytest-django tests ≥90% coverage
- [ ] OpenAPI schema auto-generated and validated
- [ ] All models have migrations (`python manage.py makemigrations`)
- [ ] Correlation IDs logged for all operations
- [ ] Integration with PowerShell connectors tested

### Database
- [ ] PostgreSQL append-only event store enforced (no updates/deletes on `DeploymentEvent`)
- [ ] Redis session store configured and tested
- [ ] Migrations run successfully (`python manage.py migrate`)

### API
- [ ] OpenAPI docs accessible at `/api/schema/swagger-ui/`
- [ ] Session authentication working with Entra ID
- [ ] CORS configured for frontend development

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. Migrations fail or create schema inconsistencies
2. Type checking (`mypy`) introduces new errors
3. Test coverage falls below 90% for any app
4. API responses don't match OpenAPI spec
5. PowerShell connectors cannot authenticate with Django API

**Escalate to human if**:
- Entra ID OAuth2 integration fails (tenant configuration issue?)
- PostgreSQL connection issues (Docker networking?)
- Redis session store unreachable

---

## Delivery Checklist

- [ ] All 9 Django apps implemented (`core`, `authentication`, `policy_engine`, `deployment_intents`, `cab_workflow`, `evidence_store`, `event_store`, `connectors`, `telemetry`)
- [ ] Docker Compose development environment functional
- [ ] Django migrations applied successfully
- [ ] OpenAPI schema generated and published
- [ ] PowerShell connectors integrated and tested
- [ ] pytest-django coverage report: ≥90%
- [ ] Black + Flake8 + mypy: 0 errors, 0 warnings
- [ ] README with setup instructions (environment variables, Docker commands)

---

## Related Documentation

- [.agents/rules/13-tech-stack.md](../../.agents/rules/13-tech-stack.md) — Authoritative tech stack
- [AGENTS.md](../../AGENTS.md) — Agent roles
- [CLAUDE.md](../../CLAUDE.md) — Architectural principles
- [docs/api/control-plane-api.yaml](../../docs/api/control-plane-api.yaml) — OpenAPI specification
- [docs/planning/phase-9-frontend-implementation-prompt.md](./phase-9-frontend-implementation-prompt.md) — Frontend (React) implementation

---

**End of Phase 8 Prompt**
