# Phase P2: Resilience & Reliability — Implementation Specification

**SPDX-License-Identifier: Apache-2.0**  
**Copyright (c) 2026 BuildWorks.AI**

**Document Status**: IMPLEMENTATION SPEC  
**Phase**: P2  
**Duration**: 1 week  
**Prerequisites**: P0 (Security) ✅, P1 (Database) ✅  
**Owner**: Backend Lead + SRE

---

## Objective

Make the system survive failures gracefully. External service outages, transient errors, and resource exhaustion MUST NOT cascade into system-wide failures.

**This phase answers:** "What happens when things go wrong?"

---

## Business Justification (From Customer Requirements)

| Requirement Source | Requirement |
|--------------------|-------------|
| Technical Architecture Spec §13 | "Retry with exponential backoff, Circuit breakers" |
| Platform Operating Model §3 | "Self-Healing Where Safe" |
| Platform Operating Model §5.2 | "KPIs: MTTR ≤4 hours (manual), ≤2 hours (AI-assisted)" |
| PRD §6 (Non-Functional) | "99.5% uptime" |

**Without this phase, a single external service failure crashes your entire platform.**

---

## Deliverables

| ID | Deliverable | Priority | Effort |
|----|-------------|----------|--------|
| P2.1 | Celery async tasks for heavy operations | CRITICAL | 2d |
| P2.2 | Circuit breakers for external services | CRITICAL | 1d |
| P2.3 | Retry logic with exponential backoff | HIGH | 1d |
| P2.4 | Request timeouts everywhere | HIGH | 0.5d |
| P2.5 | Task status API | MEDIUM | 0.5d |
| P2.6 | Tests with ≥90% coverage | MANDATORY | 1d |

---

## P2.1: Celery Async Tasks

### Problem Statement
Synchronous operations block Gunicorn worker threads. If a connector call takes 5 minutes, that worker is unavailable. Under load, this exhausts workers and the entire API becomes unresponsive.

### Current State
| Operation | Location | Blocking Time | Workers Blocked |
|-----------|----------|---------------|-----------------|
| Connector deploy | `connectors/services.py` | Up to 5 min | 1 per request |
| Risk score calculation | `policy_engine/services.py` | 1-10s | 1 per request |
| AI chat completion | `ai_agents/views.py` | 10-60s | 1 per request |
| Integration sync | `integrations/tasks.py` | Already async ✓ | N/A |

### Required Implementation

**File: `backend/apps/connectors/tasks.py` (CREATE)**
```python
"""
Async Celery tasks for connector operations.

All connector operations MUST be executed asynchronously to prevent
blocking API worker threads during long-running operations.
"""
import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from apps.connectors.services import get_connector_service
from apps.connectors.models import ConnectorExecution
from apps.event_store.services import emit_event
from apps.core.exceptions import TransientError, PermanentError

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(TransientError,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def execute_connector_deploy(
    self,
    connector_type: str,
    payload: dict,
    correlation_id: str,
    user_id: int
) -> dict:
    """
    Execute connector deployment asynchronously.
    
    Args:
        connector_type: Type of connector (intune, jamf, sccm, landscape, ansible)
        payload: Deployment payload
        correlation_id: Unique correlation ID for audit trail
        user_id: ID of user who initiated the deployment
        
    Returns:
        dict with execution result
        
    Raises:
        PermanentError: For non-retryable failures
        TransientError: For retryable failures (triggers retry)
    """
    logger.info(
        "Starting connector deployment",
        extra={
            'correlation_id': correlation_id,
            'connector_type': connector_type,
            'task_id': self.request.id,
            'retry_count': self.request.retries,
        }
    )
    
    # Create execution record for tracking
    execution = ConnectorExecution.objects.create(
        task_id=self.request.id,
        connector_type=connector_type,
        correlation_id=correlation_id,
        status='RUNNING',
        user_id=user_id,
    )
    
    try:
        service = get_connector_service(connector_type)
        result = service.deploy(payload, correlation_id)
        
        # Update execution record
        with transaction.atomic():
            execution.status = 'SUCCESS'
            execution.result = result
            execution.save()
            
            emit_event(
                event_type='CONNECTOR_DEPLOY_SUCCESS',
                correlation_id=correlation_id,
                data={'connector_type': connector_type, 'result': result}
            )
        
        logger.info(
            "Connector deployment succeeded",
            extra={'correlation_id': correlation_id, 'task_id': self.request.id}
        )
        return {'status': 'success', 'result': result}
        
    except TransientError as e:
        logger.warning(
            f"Transient error in connector deployment: {e}",
            extra={'correlation_id': correlation_id, 'task_id': self.request.id}
        )
        execution.status = 'RETRYING'
        execution.last_error = str(e)
        execution.save()
        raise  # Celery will retry
        
    except PermanentError as e:
        logger.error(
            f"Permanent error in connector deployment: {e}",
            extra={'correlation_id': correlation_id, 'task_id': self.request.id}
        )
        execution.status = 'FAILED'
        execution.last_error = str(e)
        execution.save()
        
        emit_event(
            event_type='CONNECTOR_DEPLOY_FAILED',
            correlation_id=correlation_id,
            data={'connector_type': connector_type, 'error': str(e)}
        )
        return {'status': 'failed', 'error': str(e)}
        
    except Exception as e:
        logger.exception(
            "Unexpected error in connector deployment",
            extra={'correlation_id': correlation_id, 'task_id': self.request.id}
        )
        execution.status = 'FAILED'
        execution.last_error = str(e)
        execution.save()
        raise


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def calculate_risk_score_async(
    self,
    deployment_intent_id: int,
    correlation_id: str
) -> dict:
    """
    Calculate risk score asynchronously.
    
    Args:
        deployment_intent_id: ID of the deployment intent
        correlation_id: Correlation ID for audit trail
        
    Returns:
        dict with risk score and factors
    """
    from apps.policy_engine.services import calculate_risk_score
    from apps.deployment_intents.models import DeploymentIntent
    
    logger.info(
        "Calculating risk score",
        extra={
            'correlation_id': correlation_id,
            'deployment_intent_id': deployment_intent_id,
            'task_id': self.request.id,
        }
    )
    
    try:
        deployment = DeploymentIntent.objects.get(id=deployment_intent_id)
        result = calculate_risk_score(deployment, correlation_id)
        
        # Update deployment with risk score
        deployment.risk_score = result['score']
        deployment.risk_factors = result['factors']
        deployment.save()
        
        return result
        
    except Exception as e:
        logger.exception(
            "Error calculating risk score",
            extra={'correlation_id': correlation_id, 'task_id': self.request.id}
        )
        raise self.retry(exc=e)
```

**File: `backend/apps/ai_agents/tasks.py` (MODIFY)**
```python
"""
Async Celery tasks for AI operations.
"""
import logging
from celery import shared_task
from django.utils import timezone

from apps.ai_agents.models import AIConversation, AIMessage
from apps.ai_agents.services import get_ai_provider
from apps.event_store.services import emit_event

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2)
def process_ai_chat_async(
    self,
    conversation_id: int,
    message_content: str,
    user_id: int,
    correlation_id: str
) -> dict:
    """
    Process AI chat message asynchronously.
    
    This task handles LLM API calls which can take 10-60 seconds.
    Running synchronously would block API workers.
    
    Args:
        conversation_id: ID of the conversation
        message_content: User's message content
        user_id: ID of the user
        correlation_id: Correlation ID for audit trail
        
    Returns:
        dict with AI response
    """
    logger.info(
        "Processing AI chat",
        extra={
            'correlation_id': correlation_id,
            'conversation_id': conversation_id,
            'task_id': self.request.id,
        }
    )
    
    try:
        conversation = AIConversation.objects.get(id=conversation_id)
        
        # Create user message record
        user_message = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message_content,
        )
        
        # Get AI response
        provider = get_ai_provider()
        response = provider.complete(
            message=message_content,
            conversation_history=conversation.get_history(),
            correlation_id=correlation_id,
        )
        
        # Create AI message record
        ai_message = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=response['content'],
            metadata={
                'model': response.get('model'),
                'tokens': response.get('tokens'),
                'confidence': response.get('confidence'),
            }
        )
        
        # Update conversation
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        emit_event(
            event_type='AI_CHAT_COMPLETED',
            correlation_id=correlation_id,
            data={
                'conversation_id': conversation_id,
                'response_id': ai_message.id,
            }
        )
        
        return {
            'status': 'success',
            'message_id': ai_message.id,
            'content': response['content'],
            'metadata': ai_message.metadata,
        }
        
    except Exception as e:
        logger.exception(
            "Error processing AI chat",
            extra={'correlation_id': correlation_id, 'task_id': self.request.id}
        )
        
        emit_event(
            event_type='AI_CHAT_FAILED',
            correlation_id=correlation_id,
            data={'conversation_id': conversation_id, 'error': str(e)}
        )
        
        raise self.retry(exc=e)
```

**File: `backend/apps/connectors/models.py` (ADD)**
```python
class ConnectorExecution(models.Model):
    """Track async connector execution status."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        RETRYING = 'RETRYING', 'Retrying'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
    
    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    connector_type = models.CharField(max_length=50)
    correlation_id = models.UUIDField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    user = models.ForeignKey(
        'authentication.User',
        on_delete=models.SET_NULL,
        null=True
    )
    result = models.JSONField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['correlation_id', '-created_at']),
        ]
```

### API Response Pattern
For async operations, return 202 Accepted with task ID:
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_deployment(request):
    correlation_id = generate_correlation_id()
    
    task = execute_connector_deploy.delay(
        connector_type=request.data['connector_type'],
        payload=request.data['payload'],
        correlation_id=str(correlation_id),
        user_id=request.user.id,
    )
    
    return Response(
        {
            'task_id': task.id,
            'correlation_id': str(correlation_id),
            'status': 'accepted',
            'status_url': f'/api/v1/tasks/{task.id}/status/',
        },
        status=202
    )
```

### Acceptance Criteria
- [ ] No view function blocks for >5 seconds
- [ ] Connector operations execute asynchronously
- [ ] AI chat operations execute asynchronously
- [ ] Risk calculation executes asynchronously
- [ ] 202 Accepted returned with task ID
- [ ] Task status queryable via API

---

## P2.2: Circuit Breakers

### Problem Statement
When ServiceNow is down, every API call that touches ServiceNow will timeout. If ServiceNow takes 30s to timeout and you have 8 workers, 8 requests exhaust all workers for 30s each. Your entire API becomes unresponsive because of one external dependency.

### Required Implementation

**Add Dependency to `pyproject.toml`:**
```toml
[project]
dependencies = [
    # ... existing deps
    "pybreaker>=1.0.1,<2.0.0",
]
```

**File: `backend/apps/integrations/circuit_breakers.py` (CREATE)**
```python
"""
Circuit breakers for external service calls.

Circuit breakers prevent cascading failures when external services are down.
When a breaker opens, requests fail fast instead of waiting for timeout.

Configuration per CLAUDE.md:
- fail_max: 5 consecutive failures opens breaker
- reset_timeout: 60 seconds before attempting recovery
"""
import logging
from functools import wraps
from typing import Callable, Any

from pybreaker import CircuitBreaker, CircuitBreakerError

logger = logging.getLogger(__name__)


class CircuitBreakerListener:
    """Listener for circuit breaker state changes."""
    
    def __init__(self, name: str):
        self.name = name
    
    def state_change(self, cb, old_state, new_state):
        logger.warning(
            f"Circuit breaker '{self.name}' state changed: {old_state.name} -> {new_state.name}",
            extra={
                'circuit_breaker': self.name,
                'old_state': old_state.name,
                'new_state': new_state.name,
            }
        )
    
    def failure(self, cb, exc):
        logger.warning(
            f"Circuit breaker '{self.name}' recorded failure: {exc}",
            extra={
                'circuit_breaker': self.name,
                'failure_count': cb.fail_counter,
            }
        )
    
    def success(self, cb):
        logger.debug(
            f"Circuit breaker '{self.name}' recorded success",
            extra={'circuit_breaker': self.name}
        )


def create_circuit_breaker(name: str, fail_max: int = 5, reset_timeout: int = 60) -> CircuitBreaker:
    """
    Create a circuit breaker with standard configuration.
    
    Args:
        name: Name of the circuit breaker (for logging)
        fail_max: Number of failures before opening (default: 5)
        reset_timeout: Seconds before attempting recovery (default: 60)
        
    Returns:
        Configured CircuitBreaker instance
    """
    listener = CircuitBreakerListener(name)
    return CircuitBreaker(
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        listeners=[listener],
        name=name,
    )


# Pre-configured circuit breakers for each external service
servicenow_breaker = create_circuit_breaker('servicenow')
jira_breaker = create_circuit_breaker('jira')
intune_breaker = create_circuit_breaker('intune')
jamf_breaker = create_circuit_breaker('jamf')
sccm_breaker = create_circuit_breaker('sccm')
landscape_breaker = create_circuit_breaker('landscape')
ansible_breaker = create_circuit_breaker('ansible')


def get_breaker_for_service(service_type: str) -> CircuitBreaker:
    """Get the circuit breaker for a service type."""
    breakers = {
        'servicenow': servicenow_breaker,
        'jira': jira_breaker,
        'intune': intune_breaker,
        'jamf': jamf_breaker,
        'sccm': sccm_breaker,
        'landscape': landscape_breaker,
        'ansible': ansible_breaker,
    }
    return breakers.get(service_type.lower())


def get_all_breaker_status() -> dict:
    """Get status of all circuit breakers for health check."""
    breakers = [
        ('servicenow', servicenow_breaker),
        ('jira', jira_breaker),
        ('intune', intune_breaker),
        ('jamf', jamf_breaker),
        ('sccm', sccm_breaker),
        ('landscape', landscape_breaker),
        ('ansible', ansible_breaker),
    ]
    
    return {
        name: {
            'state': breaker.current_state.name,
            'fail_counter': breaker.fail_counter,
            'is_open': breaker.current_state.name == 'open',
        }
        for name, breaker in breakers
    }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Circuit breaker for '{service_name}' is open. Service unavailable.")
```

**File: `backend/apps/integrations/services/base.py` (MODIFY)**
```python
"""
Base service with circuit breaker and retry logic.
"""
from abc import ABC, abstractmethod
from typing import Optional

from pybreaker import CircuitBreakerError

from apps.integrations.circuit_breakers import (
    get_breaker_for_service,
    CircuitBreakerOpenError,
)


class BaseIntegrationService(ABC):
    """Base class for all integration services."""
    
    service_type: str = None  # Must be set by subclass
    
    def __init__(self):
        self.breaker = get_breaker_for_service(self.service_type)
        if not self.breaker:
            raise ValueError(f"No circuit breaker configured for {self.service_type}")
    
    def execute_with_breaker(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
        """
        try:
            return self.breaker.call(func, *args, **kwargs)
        except CircuitBreakerError:
            raise CircuitBreakerOpenError(self.service_type)
    
    @abstractmethod
    def sync(self, system, correlation_id: str):
        """Sync data with external system."""
        pass
```

### Acceptance Criteria
- [ ] Circuit breaker on all external service calls
- [ ] Breaker opens after 5 consecutive failures
- [ ] Breaker resets after 60 seconds
- [ ] State changes logged
- [ ] Health check includes breaker status

---

## P2.3: Retry Logic with Exponential Backoff

### Required Implementation

**Add Dependency to `pyproject.toml`:**
```toml
[project]
dependencies = [
    # ... existing deps
    "tenacity>=8.2.3,<9.0.0",
]
```

**File: `backend/apps/integrations/services/http_client.py` (CREATE)**
```python
"""
HTTP client with retry logic and exponential backoff.

All external HTTP calls MUST use this client to ensure consistent
retry behavior and error handling.
"""
import logging
from typing import Optional, Dict, Any

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from apps.core.exceptions import TransientError, PermanentError

logger = logging.getLogger(__name__)


class RetryableHTTPClient:
    """HTTP client with retry logic for transient failures."""
    
    DEFAULT_TIMEOUT = 30  # seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TransientError),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def request(
        self,
        method: str,
        url: str,
        correlation_id: str,
        timeout: int = None,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            correlation_id: Correlation ID for logging
            timeout: Request timeout in seconds (default: 30)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            TransientError: For retryable failures (5xx, timeout)
            PermanentError: For non-retryable failures (4xx)
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        logger.debug(
            f"HTTP {method} {url}",
            extra={
                'correlation_id': correlation_id,
                'method': method,
                'url': url,
            }
        )
        
        try:
            response = requests.request(
                method,
                url,
                timeout=timeout,
                **kwargs
            )
            
            # Classify response
            if response.status_code >= 500:
                logger.warning(
                    f"Server error {response.status_code}: {url}",
                    extra={'correlation_id': correlation_id}
                )
                raise TransientError(
                    f"Server error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text[:500]
                )
            
            if response.status_code >= 400:
                logger.error(
                    f"Client error {response.status_code}: {url}",
                    extra={'correlation_id': correlation_id}
                )
                raise PermanentError(
                    f"Client error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text[:500]
                )
            
            return response
            
        except requests.Timeout as e:
            logger.warning(
                f"Request timeout: {url}",
                extra={'correlation_id': correlation_id}
            )
            raise TransientError(f"Request timeout: {e}")
            
        except requests.ConnectionError as e:
            logger.warning(
                f"Connection error: {url}",
                extra={'correlation_id': correlation_id}
            )
            raise TransientError(f"Connection error: {e}")
    
    def get(self, url: str, correlation_id: str, **kwargs) -> requests.Response:
        """Make GET request."""
        return self.request('GET', url, correlation_id, **kwargs)
    
    def post(self, url: str, correlation_id: str, **kwargs) -> requests.Response:
        """Make POST request."""
        return self.request('POST', url, correlation_id, **kwargs)
    
    def put(self, url: str, correlation_id: str, **kwargs) -> requests.Response:
        """Make PUT request."""
        return self.request('PUT', url, correlation_id, **kwargs)
    
    def delete(self, url: str, correlation_id: str, **kwargs) -> requests.Response:
        """Make DELETE request."""
        return self.request('DELETE', url, correlation_id, **kwargs)


# Singleton instance
http_client = RetryableHTTPClient()
```

**File: `backend/apps/core/exceptions.py` (CREATE)**
```python
"""
Custom exceptions for error classification.

Errors are classified as:
- TransientError: Retryable (5xx, timeout, connection error)
- PermanentError: Non-retryable (4xx, business logic errors)
"""


class TransientError(Exception):
    """
    Transient error that should trigger retry.
    
    Examples:
    - HTTP 5xx responses
    - Network timeouts
    - Connection errors
    - Rate limiting (429)
    """
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class PermanentError(Exception):
    """
    Permanent error that should NOT be retried.
    
    Examples:
    - HTTP 4xx responses (except 429)
    - Authentication failures
    - Authorization failures
    - Invalid input
    """
    
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
```

### Acceptance Criteria
- [ ] All HTTP calls use RetryableHTTPClient
- [ ] Transient errors (5xx, timeout) trigger retry
- [ ] Permanent errors (4xx) fail immediately
- [ ] Max 3 retries with 1-10s exponential backoff
- [ ] Retry attempts logged

---

## P2.4: Request Timeouts

### Required Changes

**File: `backend/config/settings/base.py` (MODIFY)**
```python
# Database timeout
DATABASES = {
    'default': {
        # ... existing config
        'OPTIONS': {
            'options': '-c statement_timeout=30000',  # 30 seconds
        },
    }
}

# Redis timeout
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_TIMEOUT': 5,
            'SOCKET_CONNECT_TIMEOUT': 5,
        }
    }
}

# Celery timeouts
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 360  # 6 minutes (hard limit)
```

### Acceptance Criteria
- [ ] All HTTP calls have explicit timeout (max 30s)
- [ ] Database statement timeout configured (30s)
- [ ] Redis timeout configured (5s)
- [ ] Celery task timeout configured
- [ ] No operation can hang indefinitely

---

## P2.5: Task Status API

**File: `backend/apps/core/views.py` (ADD)**
```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from celery.result import AsyncResult

from apps.connectors.models import ConnectorExecution


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    """
    Get status of an async task.
    
    Returns:
        200: Task status
        404: Task not found
    """
    # Try Celery result first
    result = AsyncResult(task_id)
    
    if result.state == 'PENDING':
        # Check if we have a connector execution record
        try:
            execution = ConnectorExecution.objects.get(task_id=task_id)
            return Response({
                'task_id': task_id,
                'status': execution.status,
                'result': execution.result,
                'error': execution.last_error,
                'created_at': execution.created_at.isoformat(),
                'updated_at': execution.updated_at.isoformat(),
            })
        except ConnectorExecution.DoesNotExist:
            pass
    
    # Return Celery state
    response = {
        'task_id': task_id,
        'status': result.state,
    }
    
    if result.state == 'SUCCESS':
        response['result'] = result.result
    elif result.state == 'FAILURE':
        response['error'] = str(result.result)
    
    return Response(response)
```

---

## Testing Requirements

### Unit Tests Required

**File: `backend/apps/connectors/tests/test_tasks.py`**
```python
import pytest
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry

from apps.connectors.tasks import execute_connector_deploy
from apps.core.exceptions import TransientError, PermanentError


class TestExecuteConnectorDeploy:
    """Tests for execute_connector_deploy task."""
    
    @pytest.fixture
    def mock_service(self):
        with patch('apps.connectors.tasks.get_connector_service') as mock:
            yield mock
    
    def test_successful_deployment(self, mock_service, db):
        """Test successful deployment creates success record."""
        mock_service.return_value.deploy.return_value = {'status': 'deployed'}
        
        result = execute_connector_deploy(
            connector_type='intune',
            payload={'app_id': '123'},
            correlation_id='test-correlation-id',
            user_id=1,
        )
        
        assert result['status'] == 'success'
        assert result['result'] == {'status': 'deployed'}
    
    def test_transient_error_triggers_retry(self, mock_service, db):
        """Test transient error triggers Celery retry."""
        mock_service.return_value.deploy.side_effect = TransientError('timeout')
        
        with pytest.raises(TransientError):
            execute_connector_deploy(
                connector_type='intune',
                payload={'app_id': '123'},
                correlation_id='test-correlation-id',
                user_id=1,
            )
    
    def test_permanent_error_does_not_retry(self, mock_service, db):
        """Test permanent error does not trigger retry."""
        mock_service.return_value.deploy.side_effect = PermanentError('invalid input')
        
        result = execute_connector_deploy(
            connector_type='intune',
            payload={'app_id': '123'},
            correlation_id='test-correlation-id',
            user_id=1,
        )
        
        assert result['status'] == 'failed'
```

**File: `backend/apps/integrations/tests/test_circuit_breakers.py`**
```python
import pytest
from pybreaker import CircuitBreakerError

from apps.integrations.circuit_breakers import (
    create_circuit_breaker,
    get_all_breaker_status,
    CircuitBreakerOpenError,
)


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""
    
    def test_breaker_opens_after_failures(self):
        """Test circuit breaker opens after fail_max failures."""
        breaker = create_circuit_breaker('test', fail_max=3, reset_timeout=60)
        
        def failing_func():
            raise Exception("Service down")
        
        # First 3 calls should raise the original exception
        for _ in range(3):
            with pytest.raises(Exception, match="Service down"):
                breaker.call(failing_func)
        
        # 4th call should raise CircuitBreakerError (breaker is open)
        with pytest.raises(CircuitBreakerError):
            breaker.call(failing_func)
    
    def test_breaker_allows_success(self):
        """Test circuit breaker allows successful calls."""
        breaker = create_circuit_breaker('test', fail_max=3, reset_timeout=60)
        
        def successful_func():
            return "success"
        
        result = breaker.call(successful_func)
        assert result == "success"
    
    def test_get_all_breaker_status(self):
        """Test getting status of all circuit breakers."""
        status = get_all_breaker_status()
        
        assert 'servicenow' in status
        assert 'jira' in status
        assert 'intune' in status
        assert status['servicenow']['state'] == 'closed'
```

### Coverage Requirement
- Target: ≥90% on all new code
- Focus areas: error paths, retry logic, circuit breaker state transitions

---

## Definition of Done

- [ ] All deliverables implemented
- [ ] All acceptance criteria met
- [ ] ≥90% test coverage on new code
- [ ] No new type errors (mypy passes)
- [ ] No new linting warnings (flake8 passes)
- [ ] Dependencies added to pyproject.toml
- [ ] Documentation updated
- [ ] Runbook created: `docs/runbooks/circuit-breaker-operations.md`
- [ ] Deployed to staging
- [ ] Verified in staging: circuit breakers work, retries work, timeouts work
- [ ] Phase sign-off from Tech Lead

---

## Files Created/Modified Summary

### New Files
- `backend/apps/connectors/tasks.py`
- `backend/apps/integrations/circuit_breakers.py`
- `backend/apps/integrations/services/http_client.py`
- `backend/apps/core/exceptions.py`
- `backend/apps/connectors/tests/test_tasks.py`
- `backend/apps/integrations/tests/test_circuit_breakers.py`
- `docs/runbooks/circuit-breaker-operations.md`

### Modified Files
- `backend/apps/ai_agents/tasks.py`
- `backend/apps/connectors/models.py`
- `backend/apps/integrations/services/base.py`
- `backend/apps/core/views.py`
- `backend/config/settings/base.py`
- `pyproject.toml`
