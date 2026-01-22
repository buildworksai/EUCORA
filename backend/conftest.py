# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Pytest configuration and fixtures for the entire EUCORA backend test suite.

This module provides:
- Database session/transaction setup
- Factory fixtures for common models
- Authentication/authorization fixtures
- HTTP client fixtures with auth context
- Mock fixtures for external services
"""

import pytest
import json
from uuid import uuid4
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import Mock, patch, MagicMock
from django.conf import settings

# Try to import JWT token generator, fall back if not available
try:
    from rest_framework_simplejwt.tokens import AccessToken
except ImportError:
    # If simplejwt not available, create a mock
    class AccessToken:
        @classmethod
        def for_user(cls, user):
            # Return a mock token object
            token = Mock()
            token.__str__ = lambda self: f'mock_token_for_{user.username}'
            return token

User = get_user_model()


# ===== PYTEST CONFIGURATION =====

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers",
        "e2e: marks tests as end-to-end tests"
    )


@pytest.fixture(scope='session')
def django_db_setup():
    """Configure test database and cache."""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'ATOMIC_REQUESTS': True,
        'CONN_MAX_AGE': 0,
    }
    
    # Use in-memory cache for tests instead of Redis
    settings.CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }


# ===== AUTOUSE FIXTURES =====

@pytest.fixture(autouse=True)
def reset_django_signals(db):
    """
    Reset Django signal handlers between tests to avoid test pollution.
    
    Some tests may disconnect signals, so we ensure they're reset.
    """
    yield
    # No need to reconnect signals - Django handles this automatically


@pytest.fixture(autouse=True)
def clear_cache(db):
    """Clear cache between tests to ensure test isolation."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


# ===== USER/AUTHENTICATION FIXTURES =====

@pytest.fixture
def admin_user(db):
    """Create an admin user for testing."""
    return User.objects.create_user(
        username='admin_test_user',
        email='admin@test.local',
        password='test_secure_password_123',
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


@pytest.fixture
def regular_user(db):
    """Create a regular non-admin user for testing."""
    return User.objects.create_user(
        username='regular_test_user',
        email='user@test.local',
        password='test_secure_password_123',
        is_active=True,
    )


@pytest.fixture
def publisher_user(db):
    """Create a publisher user (has publish permissions)."""
    user = User.objects.create_user(
        username='publisher_test_user',
        email='publisher@test.local',
        password='test_secure_password_123',
        is_active=True,
    )
    # Note: Assign publisher group/permissions if your app has them
    return user


@pytest.fixture
def approver_user(db):
    """Create an approver user (has approval permissions)."""
    user = User.objects.create_user(
        username='approver_test_user',
        email='approver@test.local',
        password='test_secure_password_123',
        is_active=True,
    )
    return user


@pytest.fixture
def authenticated_user(admin_user):
    """Alias for admin_user - represents the currently authenticated user."""
    return admin_user


@pytest.fixture
def jwt_token(admin_user):
    """Generate a valid JWT token for authenticated requests."""
    token = AccessToken.for_user(admin_user)
    return str(token)


@pytest.fixture
def jwt_token_regular(regular_user):
    """Generate a JWT token for regular user."""
    token = AccessToken.for_user(regular_user)
    return str(token)


@pytest.fixture
def invalid_jwt_token():
    """Return an invalid JWT token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"


# ===== API CLIENT FIXTURES =====

@pytest.fixture
def api_client():
    """Return a REST API client without authentication."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, admin_user):
    """Return an API client authenticated as admin_user using force_authenticate."""
    # Use force_authenticate for DRF test client instead of Bearer token
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_client_regular(api_client, regular_user):
    """Return an API client authenticated as regular_user."""
    api_client.force_authenticate(user=regular_user)
    return api_client


@pytest.fixture
def django_client():
    """Return a standard Django test client."""
    return Client()


# ===== MODEL FACTORY FIXTURES =====

@pytest.fixture
def sample_application(db):
    """Create a sample application for testing (placeholder fixture)."""
    # Note: Application model doesn't exist yet; this is a placeholder
    # In actual tests, we use app_name string directly
    class MockApplication:
        name = 'test-app'
        display_name = 'Test Application'
        description = 'Test application for testing'
        owner = 'test-team'
        criticality = 'MEDIUM'
        environment = 'test'
    return MockApplication()


@pytest.fixture
def sample_deployment_intent(db, regular_user, sample_application):
    """Create a sample deployment intent."""
    from apps.deployment_intents.models import DeploymentIntent
    
    return DeploymentIntent.objects.create(
        correlation_id=uuid4(),
        app_name=sample_application.name,
        version='1.0.0',
        target_ring='LAB',
        submitter=regular_user,
        status='PENDING',
        risk_score=25,
        requires_cab_approval=False,
        evidence_pack_id=uuid4(),
        is_demo=True,  # Mark as demo data so it works with demo filtering
    )


@pytest.fixture
def sample_cab_request(db, regular_user, sample_deployment_intent):
    """Create a sample CAB Approval (used in tests as CAB request)."""
    from apps.cab_workflow.models import CABApproval
    
    return CABApproval.objects.create(
        deployment_intent=sample_deployment_intent,
        decision='PENDING',
        approver=regular_user,
        comments='Test approval',
        reviewed_at=timezone.now(),
    )


@pytest.fixture
def sample_evidence_pack(db, sample_deployment_intent):
    """Create a sample evidence pack."""
    from apps.evidence_store.models import EvidencePack
    
    return EvidencePack.objects.create(
        app_name='TestApp',
        version='1.0.0',
        artifact_hash='a' * 64,  # SHA-256 hash (64 hex chars)
        artifact_path='artifacts/TestApp/1.0.0/test.msi',
        sbom_data={
            'packages': [{'name': 'test-package', 'version': '1.0.0'}]
        },
        vulnerability_scan_results={
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
        },
        rollback_plan='Test rollback plan with sufficient detail to pass validation' * 2,
        is_validated=True,
        is_demo=True,  # Mark as demo so it passes demo filtering
    )


@pytest.fixture
def sample_event(db, sample_deployment_intent):
    """Create a sample event store entry."""
    from apps.event_store.models import DeploymentEvent
    
    return DeploymentEvent.objects.create(
        correlation_id=sample_deployment_intent.correlation_id,
        event_type='DEPLOYMENT_CREATED',
        event_data={
            'app_name': sample_deployment_intent.app_name,
            'version': sample_deployment_intent.version,
            'ring': sample_deployment_intent.target_ring,
        },
        actor='testuser',
        is_demo=True,  # Mark as demo so it passes demo filtering
    )


# ===== EXTERNAL SERVICE MOCK FIXTURES =====

@pytest.fixture
def mock_http_session():
    """Create a mock HTTP session for testing HTTP requests."""
    session = MagicMock()
    
    # Mock successful response
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {'status': 'ok'}
    response.text = '{"status": "ok"}'
    response.headers = {'Content-Type': 'application/json'}
    response.elapsed = timedelta(milliseconds=100)
    
    session.get.return_value = response
    session.post.return_value = response
    session.put.return_value = response
    session.patch.return_value = response
    session.delete.return_value = response
    
    return session


@pytest.fixture
def mock_circuit_breaker():
    """Create a mock circuit breaker for testing."""
    breaker = MagicMock()
    breaker.state = 'CLOSED'
    breaker.is_open.return_value = False
    breaker.is_half_open.return_value = False
    breaker.is_closed.return_value = True
    breaker.call.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)
    return breaker


@pytest.fixture
def mock_entra_id():
    """Mock Entra ID authentication service."""
    with patch('apps.authentication.services.EntraIDService') as mock:
        instance = MagicMock()
        instance.validate_token.return_value = {
            'oid': uuid4(),
            'email': 'test@example.com',
            'name': 'Test User',
            'roles': ['user'],
        }
        instance.get_token.return_value = 'mock_access_token'
        mock.return_value = instance
        yield mock


@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution."""
    with patch('celery.app.task.Task.apply_async') as mock:
        result = MagicMock()
        result.id = str(uuid4())
        result.status = 'PENDING'
        result.result = None
        mock.return_value = result
        yield mock


@pytest.fixture
def mock_connector_service():
    """Mock connector service (Intune, SCCM, etc.)."""
    service = MagicMock()
    service.health_check.return_value = {
        'status': 'HEALTHY',
        'response_time_ms': 100,
    }
    service.publish.return_value = {
        'status': 'SUCCESS',
        'asset_id': str(uuid4()),
        'timestamp': timezone.now().isoformat(),
    }
    service.query.return_value = {
        'total': 100,
        'installed': 95,
        'failed': 5,
    }
    service.remediate.return_value = {
        'status': 'SUCCESS',
        'remediated_count': 5,
    }
    return service


# ===== PARAMETRIZED FIXTURES =====

@pytest.fixture(params=['LAB', 'CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL'])
def all_rings(request):
    """Parametrized fixture for all deployment rings."""
    return request.param


@pytest.fixture(params=['PENDING', 'APPROVED', 'EXECUTING', 'COMPLETED', 'FAILED'])
def all_deployment_statuses(request):
    """Parametrized fixture for all deployment statuses."""
    return request.param


@pytest.fixture(params=['PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'])
def all_cab_statuses(request):
    """Parametrized fixture for CAB request statuses."""
    return request.param


# ===== CONTEXT/STATE FIXTURES =====

@pytest.fixture
def correlation_id():
    """Return a unique correlation ID for tracing."""
    return str(uuid4())


@pytest.fixture
def trace_context(correlation_id):
    """Return a trace context dictionary for testing."""
    return {
        'correlation_id': correlation_id,
        'trace_id': str(uuid4()),
        'span_id': str(uuid4()),
        'user_id': str(uuid4()),
        'timestamp': timezone.now().isoformat(),
    }


@pytest.fixture
def request_headers(jwt_token, correlation_id):
    """Return HTTP headers for an authenticated request with correlation ID."""
    return {
        'HTTP_AUTHORIZATION': f'Bearer {jwt_token}',
        'HTTP_X_CORRELATION_ID': correlation_id,
        'HTTP_CONTENT_TYPE': 'application/json',
    }


# ===== DATABASE/TRANSACTION FIXTURES =====

@pytest.fixture
def with_db_transaction(db):
    """
    Fixture for tests that require database transaction control.
    
    Use in tests that need to test transactional behavior.
    """
    from django.db import transaction
    yield transaction


# ===== CLEANUP/TEARDOWN FIXTURES =====

@pytest.fixture
def cleanup_files():
    """
    Fixture to clean up test files after test execution.
    
    Useful for tests that create temporary files or S3 objects.
    """
    files = []
    yield files
    
    import os
    for filepath in files:
        if os.path.exists(filepath):
            os.remove(filepath)


# ===== HELPER FUNCTIONS =====

def create_test_user(username, **kwargs):
    """
    Helper function to create a test user with custom attributes.
    
    Usage:
        user = create_test_user('test_user', is_staff=True)
    """
    defaults = {
        'email': f'{username}@test.local',
        'password': 'test_secure_password_123',
        'is_active': True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(username=username, **defaults)


def create_test_deployment(app_name, **kwargs):
    """
    Helper function to create a test deployment intent.
    
    Usage:
        deployment = create_test_deployment('my-app', version='2.0.0')
    """
    from apps.deployment_intents.models import DeploymentIntent
    
    defaults = {
        'correlation_id': uuid4(),
        'version': '1.0.0',
        'target_ring': 'LAB',
        'status': 'PENDING',
        'risk_score': 25,
        'requires_cab': False,
    }
    defaults.update(kwargs)
    
    # Get or create submitter
    if 'submitter' not in defaults:
        defaults['submitter'] = create_test_user('deployment_submitter')
    
    return DeploymentIntent.objects.create(
        app_name=app_name,
        **defaults
    )


# ===== PYTEST-DJANGO SETTINGS =====

# Force Django database mode for all tests
pytestmark = pytest.mark.django_db(database='default', transaction=True)
