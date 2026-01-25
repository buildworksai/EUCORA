# EUCORA Production Readiness: Phased Implementation Plan

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Status**: MANDATORY
**Created**: 2026-01-21
**Authority**: Engineering Leadership

---

## Executive Summary

This document defines the **non-negotiable** improvements required to bring EUCORA from MVP to production-grade. Each phase has clear acceptance criteria. **No phase is optional. No shortcuts allowed.**

Demo data seeding remains for customer demonstrations, but **demo functionality must NEVER compromise production security or performance**.

---

## Phase Overview

| Phase | Focus | Duration | Risk if Skipped |
|-------|-------|----------|-----------------|
| **P0** | Critical Security | 1 week | Data breach, system compromise |
| **P1** | Database & Performance | 1 week | System crash under load |
| **P2** | Resilience & Reliability | 1 week | Cascading failures |
| **P3** | Observability & Operations | 1 week | Blind to production issues |
| **P4** | Testing & Quality | 2 weeks | Unknown bugs in production |
| **P5** | Scale & Hardening | 1 week | Growth ceiling |
| **P6** | Final Validation | 1 week | GO/NO-GO decision |
| **P7** | Self-Hosted Branding | 1 week | No customer customization |
| **P8** | Marketing & Public Pages | 1 week | No public presence |

**Total Timeline**: 10 weeks minimum. No compression without executive risk acceptance.

---

## Phase 0: Critical Security Fixes

**Timeline**: Week 1
**Status**: 🔴 BLOCKING - Cannot ship without completion
**Owner**: Security + Backend Lead

### P0.1: Remove Default Secrets

**Problem**: Application starts with insecure defaults if environment variables are missing.

**Files to Fix**:
- `backend/config/settings/base.py`
- `backend/config/settings/development.py`

**Current (DANGEROUS)**:
```python
SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-secret-key-change-in-production')
'PASSWORD': config('POSTGRES_PASSWORD', default='eucora_dev_password'),
MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY', default='minioadmin')
MINIO_SECRET_KEY = config('MINIO_SECRET_KEY', default='minioadmin')
```

**Required Change**:
```python
# base.py - NO DEFAULTS for secrets
SECRET_KEY = config('DJANGO_SECRET_KEY')  # Will crash if not set - GOOD
MINIO_ACCESS_KEY = config('MINIO_ACCESS_KEY')
MINIO_SECRET_KEY = config('MINIO_SECRET_KEY')

# Database password - no default
'PASSWORD': config('POSTGRES_PASSWORD'),
```

**For development.py ONLY** (never used in production):
```python
# Explicit development-only overrides
SECRET_KEY = config('DJANGO_SECRET_KEY', default='dev-only-not-for-production')
```

**Acceptance Criteria**:
- [ ] Production settings have ZERO default secrets
- [ ] Application fails to start if secrets missing
- [ ] Development settings clearly marked as dev-only
- [ ] CI/CD validates required env vars before deployment

---

### P0.2: Isolate Demo Credentials from Production Code

**Problem**: Hardcoded `admin@134` password appears 10 times in codebase, visible in frontend.

**Files to Fix**:
- `backend/apps/core/demo_data.py`
- `frontend/src/routes/Login.tsx`
- `frontend/src/types/auth.ts`

**Required Changes**:

1. **Backend Demo Data** - Use environment variable:
```python
# demo_data.py
DEMO_PASSWORD = config('DEMO_USER_PASSWORD', default='change-me-in-production')

def _get_or_create_demo_admin():
    # Use DEMO_PASSWORD variable, not hardcoded string
    password=DEMO_PASSWORD
```

2. **Frontend Login Page** - Conditional rendering:
```typescript
// Login.tsx - Only show demo credentials in demo mode
{import.meta.env.VITE_DEMO_MODE === 'true' && (
  <DemoCredentialsHint />
)}
```

3. **Remove from auth.ts mock users entirely** - Mock users should not have real passwords:
```typescript
// MOCK_USERS should use tokens, not passwords
export const MOCK_USERS = {
  demo: { token: 'demo-session-token', role: 'demo' },
  admin: { token: 'admin-session-token', role: 'admin' },
};
```

**Acceptance Criteria**:
- [ ] No hardcoded passwords in source code
- [ ] Demo credentials only visible when VITE_DEMO_MODE=true
- [ ] Password sourced from environment variable
- [ ] Security scan passes with no credential findings

---

### P0.3: Add Rate Limiting

**Problem**: Zero throttling = brute force, DoS, credential stuffing all possible.

**File to Fix**: `backend/config/settings/base.py`

**Required Addition**:
```python
REST_FRAMEWORK = {
    # ... existing config ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    }
}
```

**Additional**: Create custom throttle for login:
```python
# backend/apps/authentication/throttles.py
class LoginRateThrottle(AnonRateThrottle):
    rate = '5/minute'
```

**Acceptance Criteria**:
- [ ] Anonymous users limited to 100 requests/hour
- [ ] Authenticated users limited to 1000 requests/hour
- [ ] Login endpoint limited to 5 attempts/minute
- [ ] Throttle responses return proper 429 status

---

### P0.4: Fix Authentication on Sensitive Endpoints

**Problem**: AllowAny exposes deployment data to unauthenticated users.

**Files to Fix**:
- `backend/apps/deployment_intents/views.py`
- `backend/apps/core/views_demo.py`

**Endpoints Requiring Authentication**:
| Endpoint | Current | Required |
|----------|---------|----------|
| `/api/v1/deployments/list` | AllowAny | IsAuthenticated |
| `/api/v1/deployments/applications` | AllowAny | IsAuthenticated |
| `/api/v1/admin/demo-data/stats` | AllowAny | IsAdminUser |
| `/api/v1/admin/demo-data/seed` | AllowAny | IsAdminUser |
| `/api/v1/admin/demo-data/clear` | AllowAny | IsAdminUser |

**Exception**: Health check endpoints remain AllowAny for load balancer probes.

**Acceptance Criteria**:
- [ ] All data endpoints require authentication
- [ ] Admin endpoints require IsAdminUser
- [ ] Only health probes are AllowAny
- [ ] 401/403 returned for unauthorized access

---

### P0.5: Secure AI API Key Storage

**Problem**: `api_key_dev` field stores plaintext API keys in database.

**File to Fix**: `backend/apps/ai_agents/models.py`

**Required Changes**:
1. Encrypt `api_key_dev` field or remove it entirely
2. Force production to use `api_key_vault_ref` (Key Vault reference)
3. Add migration to encrypt existing keys

```python
# Option 1: Remove dev field, require vault
class AIModelProvider(models.Model):
    api_key_vault_ref = models.CharField(...)  # Required in production
    # REMOVE: api_key_dev field

# Option 2: Encrypt at rest
from django_cryptography.fields import encrypt
api_key_dev = encrypt(models.CharField(...))
```

**Acceptance Criteria**:
- [ ] No plaintext API keys in database
- [ ] Production requires vault references
- [ ] Existing keys migrated to encrypted storage
- [ ] Key retrieval audited

---

### P0.6: Fix Bare Except Clauses

**Problem**: Silent failures hide production errors.

**Files to Fix**:
- `backend/apps/core/views_demo.py` (line 244)
- `backend/apps/integrations/tasks.py` (line 99)

**Current (DANGEROUS)**:
```python
except:
    pass
```

**Required Change**:
```python
except OSError as e:
    logger.warning(f'Cleanup failed: {e}', extra={'correlation_id': correlation_id})
```

**Acceptance Criteria**:
- [ ] Zero bare except clauses in codebase
- [ ] All exceptions logged with correlation ID
- [ ] Specific exception types caught

---

## Phase 1: Database & Performance

**Timeline**: Week 2
**Status**: 🔴 BLOCKING - System will crash under load
**Owner**: Backend Lead + DBA

### P1.1: Fix N+1 Query Problems

**Problem**: Only 1 view uses select_related. Every list endpoint is a database killer.

**Files to Fix**:
- `backend/apps/deployment_intents/views.py`
- `backend/apps/cab_workflow/views.py`
- `backend/apps/integrations/views.py`
- `backend/apps/ai_agents/views.py`
- `backend/apps/event_store/views.py`

**Pattern to Apply**:
```python
# BEFORE (N+1)
queryset = DeploymentIntent.objects.all()
for d in queryset:
    print(d.submitter.username)  # Query per iteration

# AFTER (Optimized)
queryset = DeploymentIntent.objects.select_related('submitter').all()
```

**Specific Fixes Required**:
| View | Missing Optimization |
|------|---------------------|
| `list_applications_with_versions` | `select_related('submitter')` |
| `list_deployments` | `select_related('submitter')` |
| `cab_approval_list` | Already has it ✓ |
| `integration_sync_logs` | `select_related('system')` |
| `ai_task_list` | `select_related('user', 'provider')` |

**Acceptance Criteria**:
- [ ] All list views use select_related/prefetch_related
- [ ] Query count verified with django-debug-toolbar
- [ ] No endpoint exceeds 5 queries regardless of result size

---

### P1.2: Implement Real Pagination

**Problem**: Endpoints load entire tables into memory, then slice.

**Files to Fix**:
- `backend/apps/deployment_intents/views.py` - `list_applications_with_versions`

**Current (MEMORY BOMB)**:
```python
queryset = DeploymentIntent.objects.all()  # Loads ALL
applications = {}
for deployment in queryset:  # Iterates ALL
    # Build dict in memory
```

**Required Change**: Use cursor pagination for large datasets:
```python
from rest_framework.pagination import CursorPagination

class DeploymentCursorPagination(CursorPagination):
    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'

# In view
paginator = DeploymentCursorPagination()
page = paginator.paginate_queryset(queryset, request)
```

**For `list_applications_with_versions`**: Rewrite with database aggregation:
```python
from django.db.models import Count, Max

# Use database aggregation instead of Python loops
applications = DeploymentIntent.objects.values('app_name').annotate(
    deployment_count=Count('id'),
    latest_created=Max('created_at')
).order_by('app_name')[:50]  # Paginated
```

**Acceptance Criteria**:
- [ ] No endpoint loads more than 100 records into memory
- [ ] Cursor pagination on all list endpoints
- [ ] Response time < 500ms for 100K record tables

---

### P1.3: Add Missing Database Indexes

**Files to Fix**: Create new migration

```python
# backend/apps/deployment_intents/migrations/0002_add_indexes.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('deployment_intents', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='deploymentintent',
            index=models.Index(fields=['app_name', '-created_at'], name='deploy_app_created_idx'),
        ),
        migrations.AddIndex(
            model_name='deploymentintent',
            index=models.Index(fields=['status', '-created_at'], name='deploy_status_created_idx'),
        ),
    ]
```

**Additional Indexes Required**:
| Model | Fields | Rationale |
|-------|--------|-----------|
| EvidencePack | `correlation_id` | Lookup by correlation |
| AIConversation | `title` | Search by title |
| AIModelUsage | `model_name` | Analytics queries |
| AITask | `task_type` | Filter by type |
| RiskAssessment | `requires_cab_approval` | Filter CAB queue |

**Acceptance Criteria**:
- [ ] All frequently filtered fields indexed
- [ ] Query EXPLAIN shows index usage
- [ ] No full table scans on filtered queries

---

### P1.4: Add Database Constraints

**Problem**: Invalid data can be stored (risk_score > 100, negative counts).

**File to Fix**: Create migration with CheckConstraints

```python
from django.db.models import CheckConstraint, Q

class Migration(migrations.Migration):
    operations = [
        migrations.AddConstraint(
            model_name='deploymentintent',
            constraint=CheckConstraint(
                check=Q(risk_score__gte=0) & Q(risk_score__lte=100),
                name='valid_risk_score'
            ),
        ),
        migrations.AddConstraint(
            model_name='ringdeployment',
            constraint=CheckConstraint(
                check=Q(success_rate__gte=0) & Q(success_rate__lte=1),
                name='valid_success_rate'
            ),
        ),
    ]
```

**Acceptance Criteria**:
- [ ] All percentage/score fields have 0-100 constraints
- [ ] All rate fields have 0-1 constraints
- [ ] All count fields have >= 0 constraints
- [ ] Database rejects invalid data

---

### P1.5: Add Transaction Handling

**Problem**: Multi-model updates can leave inconsistent state on failure.

**Files to Fix**:
- `backend/apps/cab_workflow/views.py`
- `backend/apps/deployment_intents/views.py`
- `backend/apps/ai_agents/views.py`

**Pattern to Apply**:
```python
from django.db import transaction

@api_view(['POST'])
def approve_deployment(request, pk):
    with transaction.atomic():
        approval = CABApproval.objects.select_for_update().get(pk=pk)
        approval.decision = 'APPROVED'
        approval.save()

        deployment = approval.deployment_intent
        deployment.status = 'APPROVED'
        deployment.save()

        # Event creation inside same transaction
        DeploymentEvent.objects.create(...)
```

**Acceptance Criteria**:
- [ ] All multi-model updates wrapped in atomic transactions
- [ ] select_for_update used for concurrent access
- [ ] Rollback tested for mid-operation failures

---

## Phase 2: Resilience & Reliability

**Timeline**: Week 3
**Status**: 🟠 HIGH - Cascading failures without this
**Owner**: Backend Lead + SRE

### P2.1: Move Heavy Operations to Celery

**Problem**: Synchronous operations block worker threads.

**Operations to Make Async**:
| Operation | Current Location | Blocking Time |
|-----------|-----------------|---------------|
| PowerShell connector calls | `connectors/services.py` | Up to 5 min |
| Risk score calculation | `policy_engine/services.py` | Variable |
| AI chat completion | `ai_agents/views.py` | 10-60s |
| Integration sync | Already async ✓ | N/A |

**Required New Tasks**:
```python
# backend/apps/connectors/tasks.py
@shared_task(bind=True, max_retries=3)
def execute_connector_deploy(self, connector_type, payload, correlation_id):
    """Async connector deployment execution."""
    try:
        service = get_connector_service(connector_type)
        return service.deploy(payload)
    except TransientError as e:
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

# backend/apps/ai_agents/tasks.py
@shared_task(bind=True)
def process_ai_chat(self, conversation_id, message, user_id):
    """Async AI chat processing."""
    # Process and store response
```

**Acceptance Criteria**:
- [ ] No view function blocks for > 5 seconds
- [ ] Long operations return 202 Accepted with task ID
- [ ] Task status queryable via API
- [ ] Worker threads remain available under load

---

### P2.2: Add Circuit Breakers

**Problem**: External service failures cause cascading failures.

**Add Dependency**: `requirements/base.txt`
```
pybreaker~=1.0.1
```

**Implementation**:
```python
# backend/apps/integrations/circuit_breakers.py
from pybreaker import CircuitBreaker

# Per-service circuit breakers
servicenow_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name='servicenow'
)

jira_breaker = CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    name='jira'
)

# Usage in service
class ServiceNowService:
    @servicenow_breaker
    def sync(self, system, correlation_id):
        # External call protected by circuit breaker
```

**Acceptance Criteria**:
- [ ] Circuit breaker on all external service calls
- [ ] Breaker opens after 5 consecutive failures
- [ ] Breaker resets after 60 seconds
- [ ] Graceful fallback when breaker is open

---

### P2.3: Add Retry Logic with Backoff

**Problem**: Transient failures cause permanent errors.

**Add Dependency**: `requirements/base.txt`
```
tenacity~=8.2.3
```

**Implementation**:
```python
# backend/apps/integrations/services/base.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class BaseIntegrationService:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TransientError)
    )
    def _make_request(self, method, url, **kwargs):
        response = requests.request(method, url, timeout=30, **kwargs)
        if response.status_code >= 500:
            raise TransientError(f'Server error: {response.status_code}')
        return response
```

**Acceptance Criteria**:
- [ ] All HTTP calls have retry with exponential backoff
- [ ] Transient errors (5xx, timeout) trigger retry
- [ ] Permanent errors (4xx) fail immediately
- [ ] Max 3 retries with 1-10s backoff

---

### P2.4: Add Request Timeouts Everywhere

**Problem**: Missing timeouts can hang worker threads forever.

**Files to Audit and Fix**:
- All `requests.get/post` calls must have `timeout=` parameter
- Database statement timeout
- Redis operation timeout

**Database Timeout**:
```python
# backend/config/settings/base.py
DATABASES['default']['OPTIONS'] = {
    'options': '-c statement_timeout=30000',  # 30 seconds
}
```

**Acceptance Criteria**:
- [ ] All HTTP calls have explicit timeout (max 30s)
- [ ] Database statement timeout configured
- [ ] No operation can hang indefinitely

---

## Phase 3: Observability & Operations

**Timeline**: Week 4
**Status**: 🟠 HIGH - Blind to production issues
**Owner**: SRE + Backend Lead

### P3.1: Structured Logging

**Problem**: Inconsistent logging, missing correlation IDs.

**Standard Log Format**:
```python
# backend/config/settings/base.py
LOGGING = {
    'version': 1,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(correlation_id)s %(message)s'
        }
    },
    # ... handlers and loggers
}
```

**Every Log Must Include**:
- `correlation_id`
- `timestamp`
- `level`
- `service_name`
- `user_id` (if authenticated)

**Acceptance Criteria**:
- [ ] All logs in JSON format
- [ ] Correlation ID in every log entry
- [ ] No print() statements in production code
- [ ] Log aggregation configured (ELK/Datadog)

---

### P3.2: Remove Console Statements

**Problem**: 16 console.log/error statements not captured by logging.

**Files to Fix**:
- `frontend/src/lib/api/client.ts`
- `frontend/src/routes/Login.tsx`
- `frontend/src/components/admin/AIAssistant/AIAssistant.tsx`
- `frontend/src/context/AuthContext.tsx`
- Plus others identified in audit

**Replace With**:
```typescript
// frontend/src/lib/logger.ts
export const logger = {
  error: (message: string, context?: object) => {
    if (import.meta.env.PROD) {
      // Send to logging service (Sentry, LogRocket)
      Sentry.captureMessage(message, { extra: context });
    } else {
      console.error(message, context);
    }
  },
  // ... info, warn, debug
};
```

**Acceptance Criteria**:
- [ ] Zero console.log in production builds
- [ ] Frontend logging service configured
- [ ] Errors captured in monitoring system

---

### P3.3: Error Response Sanitization

**Problem**: Internal error details exposed to users.

**Files to Fix**:
- `backend/apps/telemetry/views.py`
- `backend/apps/evidence_store/views.py`
- `backend/apps/policy_engine/views.py`

**Current (DANGEROUS)**:
```python
return Response({'error': str(e)})  # Exposes stack trace
```

**Required Pattern**:
```python
except Exception as e:
    logger.error(f'Operation failed: {e}', exc_info=True, extra={'correlation_id': ...})
    return Response(
        {'error': 'Internal server error', 'correlation_id': str(correlation_id)},
        status=500
    )
```

**Acceptance Criteria**:
- [ ] No internal details in error responses
- [ ] Correlation ID returned for support lookup
- [ ] All errors logged with full context server-side

---

### P3.4: Health Check Enhancement

**Problem**: Basic health checks don't verify all dependencies.

**File to Enhance**: `backend/apps/telemetry/views.py`

**Required Checks**:
```python
def health_check(request):
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery_workers(),
        'minio': check_minio(),
        'external_services': check_external_services(),  # Circuit breaker status
    }

    all_healthy = all(c['status'] == 'healthy' for c in checks.values())
    return Response(checks, status=200 if all_healthy else 503)
```

**Acceptance Criteria**:
- [ ] Health check verifies ALL dependencies
- [ ] Returns 503 if any critical dependency unhealthy
- [ ] Circuit breaker status included
- [ ] Suitable for load balancer health probes

---

## Phase 4: Testing & Quality

**Timeline**: Weeks 5-6
**Status**: 🟡 MEDIUM - Unknown bugs in production
**Owner**: QA Lead + All Engineers

### P4.1: API Endpoint Test Coverage

**Problem**: Unknown if APIs actually work correctly.

**Required Tests Per App**:
| App | Endpoints | Required Tests |
|-----|-----------|----------------|
| deployment_intents | 4 | Create, List, Get, Applications |
| cab_workflow | 5 | List, Approve, Reject, Stats, Pending |
| integrations | 4 | List, Sync, Logs, Configure |
| ai_agents | 6 | Providers, Chat, Tasks, Stats |
| evidence_store | 3 | Upload, Get, List |
| policy_engine | 3 | Calculate, Models, Assess |

**Test Pattern**:
```python
# backend/apps/deployment_intents/tests/test_views.py
class TestDeploymentEndpoints(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.client.force_authenticate(user=self.user)

    def test_list_applications_returns_grouped_data(self):
        # Create test data
        DeploymentIntent.objects.create(app_name='App1', version='1.0', ...)
        DeploymentIntent.objects.create(app_name='App1', version='2.0', ...)

        response = self.client.get('/api/v1/deployments/applications')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['applications']), 1)
        self.assertEqual(len(response.data['applications'][0]['versions']), 2)

    def test_list_applications_requires_auth(self):
        self.client.logout()
        response = self.client.get('/api/v1/deployments/applications')
        self.assertEqual(response.status_code, 401)
```

**Acceptance Criteria**:
- [ ] Every endpoint has positive and negative test cases
- [ ] Authentication/authorization tested
- [ ] Edge cases covered (empty data, invalid input)
- [ ] 80%+ line coverage on views

---

### P4.2: Integration Test Suite

**Problem**: Unit tests don't catch integration issues.

**Required Integration Tests**:
```python
# backend/tests/integration/test_deployment_flow.py
class TestDeploymentFlow(TransactionTestCase):
    """End-to-end deployment flow test."""

    def test_full_deployment_lifecycle(self):
        # 1. Create deployment intent
        # 2. Verify risk assessment triggered
        # 3. If CAB required, verify CAB approval created
        # 4. Approve CAB
        # 5. Verify deployment status updated
        # 6. Verify event store has all events
        pass

    def test_deployment_with_connector(self):
        # Test actual connector integration (mocked external)
        pass
```

**Acceptance Criteria**:
- [ ] Critical user flows have integration tests
- [ ] External services mocked at HTTP level (not service level)
- [ ] Database transactions tested
- [ ] Celery tasks tested with eager mode

---

### P4.3: Load Testing

**Problem**: No idea how system performs under load.

**Required Load Tests** (using locust or k6):
```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class EUCORAUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_applications(self):
        self.client.get('/api/v1/deployments/applications')

    @task(1)
    def create_deployment(self):
        self.client.post('/api/v1/deployments/', json={...})
```

**Performance Targets**:
| Endpoint | Target p95 | Max Concurrent |
|----------|-----------|----------------|
| List applications | < 500ms | 100 users |
| Create deployment | < 1s | 50 users |
| Health check | < 100ms | 200 users |

**Acceptance Criteria**:
- [ ] Load test suite created
- [ ] Performance baseline established
- [ ] CI runs load tests on staging
- [ ] Alerts if performance degrades > 20%

---

### P4.4: Fix TODO/FIXME Items

**Problem**: 4 incomplete implementations in critical paths.

**Items to Complete**:
1. `deployment_intents/tasks.py:50` - Implement state comparison logic
2. `ai_agents/views.py:55` - Add proper permission check
3. `ai_agents/views.py:115` - Implement proper audit logging
4. `frontend/src/types/api.ts:50` - Fix unknown logic error

**Acceptance Criteria**:
- [ ] Zero TODO/FIXME in production code paths
- [ ] Each item either completed or converted to tracked issue
- [ ] Code review required for each completion

---

## Phase 5: Scale & Hardening

**Timeline**: Week 7
**Status**: 🟡 MEDIUM - Growth ceiling
**Owner**: SRE + Architect

### P5.1: Application-Level Caching

**Problem**: Every request hits database.

**Implementation**:
```python
# backend/apps/policy_engine/services.py
from django.core.cache import cache

def get_active_risk_model():
    cache_key = 'active_risk_model'
    model = cache.get(cache_key)
    if model is None:
        model = RiskModel.objects.filter(is_active=True).first()
        cache.set(cache_key, model, 300)  # 5 minutes
    return model

# Invalidate on update
@receiver(post_save, sender=RiskModel)
def invalidate_risk_model_cache(sender, **kwargs):
    cache.delete('active_risk_model')
```

**Cache Strategy**:
| Data | TTL | Invalidation |
|------|-----|--------------|
| Active risk model | 5 min | On model change |
| Provider list | 5 min | On provider change |
| Static lookups | 1 hour | On deployment |
| User permissions | 1 min | On permission change |

**Acceptance Criteria**:
- [ ] Frequently accessed data cached
- [ ] Cache invalidation implemented
- [ ] Cache hit rate > 80% for read endpoints
- [ ] No stale data issues

---

### P5.2: Redis High Availability

**Problem**: Single Redis instance is SPOF.

**Required Configuration**:
```python
# backend/config/settings/production.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': [
            'redis://redis-sentinel-1:26379/0',
            'redis://redis-sentinel-2:26379/0',
            'redis://redis-sentinel-3:26379/0',
        ],
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.SentinelClient',
            'SENTINEL_KWARGS': {'password': config('REDIS_SENTINEL_PASSWORD')},
            'PASSWORD': config('REDIS_PASSWORD'),
        }
    }
}
```

**Acceptance Criteria**:
- [ ] Redis Sentinel configured for production
- [ ] Automatic failover tested
- [ ] Session persistence during failover
- [ ] Monitoring alerts on Redis health

---

### P5.3: Distributed Locking

**Problem**: Race conditions on concurrent operations.

**Implementation**:
```python
# backend/apps/core/locks.py
from django.core.cache import cache
from contextlib import contextmanager

@contextmanager
def distributed_lock(lock_name, timeout=30):
    lock_key = f'lock:{lock_name}'
    acquired = cache.add(lock_key, '1', timeout)
    if not acquired:
        raise LockNotAcquired(f'Could not acquire lock: {lock_name}')
    try:
        yield
    finally:
        cache.delete(lock_key)

# Usage
with distributed_lock(f'deployment:{deployment_id}'):
    # Only one worker can process this deployment
    process_deployment(deployment_id)
```

**Acceptance Criteria**:
- [ ] Critical operations protected by distributed locks
- [ ] Lock timeout prevents deadlocks
- [ ] Lock contention monitored

---

### P5.4: Horizontal Scaling Validation

**Problem**: Unknown blockers to running multiple instances.

**Validation Checklist**:
- [ ] No local filesystem storage (use S3/MinIO)
- [ ] No in-memory state between requests
- [ ] Sessions in Redis (not local)
- [ ] Celery tasks don't assume local execution
- [ ] Database migrations safe for rolling deployment

**Test Procedure**:
1. Run 3 backend instances behind load balancer
2. Run full test suite
3. Verify no session issues
4. Verify no race conditions
5. Verify even load distribution

**Acceptance Criteria**:
- [ ] Application runs correctly with 3+ instances
- [ ] No sticky sessions required
- [ ] Zero state in application servers

---

## Phase 6: Final Validation

**Timeline**: Week 8
**Status**: Gate to Production
**Owner**: Engineering Leadership + Security

### P6.1: Security Penetration Test

**Scope**:
- Authentication bypass attempts
- SQL injection testing
- XSS testing
- CSRF validation
- Rate limit bypass
- Privilege escalation

**Acceptance Criteria**:
- [ ] No critical/high vulnerabilities
- [ ] All medium vulnerabilities have mitigation plan
- [ ] Pen test report signed off by Security

---

### P6.2: Performance Baseline

**Requirements**:
| Metric | Target |
|--------|--------|
| p50 response time | < 200ms |
| p95 response time | < 500ms |
| p99 response time | < 1s |
| Error rate | < 0.1% |
| Concurrent users | 100+ |

**Acceptance Criteria**:
- [ ] Performance targets met under load
- [ ] No memory leaks over 24h test
- [ ] Database connection pool stable

---

### P6.3: Disaster Recovery Test

**Test Scenarios**:
1. Database failover
2. Redis failover
3. Celery worker restart
4. Full application restart
5. Restore from backup

**Acceptance Criteria**:
- [ ] RTO < 15 minutes for each scenario
- [ ] RPO < 5 minutes for data
- [ ] Runbooks documented and tested

---

### P6.4: Production Readiness Checklist

**Final Sign-off Requirements**:
- [ ] All P0-P5 phases completed
- [ ] Security pen test passed
- [ ] Performance targets met
- [ ] DR test completed
- [ ] Monitoring and alerting configured
- [ ] On-call rotation established
- [ ] Incident response runbook documented
- [ ] Rollback procedure tested

---

## Appendix A: Demo Mode Architecture

**Principle**: Demo functionality must be completely isolated from production code paths.

**Architecture**:
```
┌─────────────────────────────────────────┐
│           Request Handler               │
├─────────────────────────────────────────┤
│  if DEMO_MODE:                          │
│    → Demo Authentication (mock)         │
│    → Demo Data Filter (is_demo=True)    │
│  else:                                  │
│    → Production Authentication (Entra)  │
│    → Production Data Filter             │
└─────────────────────────────────────────┘
```

**Rules**:
1. Demo mode ONLY enabled via environment variable
2. Demo credentials NEVER in source code
3. Demo data ALWAYS has `is_demo=True` flag
4. Demo data NEVER visible when demo mode disabled
5. Demo endpoints NEVER bypass security in production

---

## Appendix B: Environment Variable Requirements

**Production Required Variables** (no defaults):
```bash
# Secrets - MUST be set
DJANGO_SECRET_KEY=<random-64-char>
POSTGRES_PASSWORD=<strong-password>
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<secret-key>
REDIS_PASSWORD=<strong-password>

# Service URLs - MUST be set
DATABASE_URL=postgres://...
REDIS_URL=redis://...
MINIO_ENDPOINT=https://...

# Authentication - MUST be set
ENTRA_CLIENT_ID=<azure-app-id>
ENTRA_TENANT_ID=<azure-tenant-id>
ENTRA_CLIENT_SECRET=<azure-secret>
```

**Optional with Safe Defaults**:
```bash
LOG_LEVEL=INFO
PAGE_SIZE=100
CACHE_TTL=300
```

---

## Appendix C: Dependency Additions

**Add to `requirements/base.txt`**:
```
# Resilience
pybreaker~=1.0.1
tenacity~=8.2.3

# Monitoring
sentry-sdk~=1.40.0

# Logging
python-json-logger~=2.0.7

# Security
django-cryptography~=1.1
```

**Add to `package.json`**:
```json
{
  "dependencies": {
    "@sentry/react": "^7.100.0"
  }
}
```

---

**Document End**

---

## Phase 7: Self-Hosted Branding & Customization

**Timeline**: Week 9 (1 week - SIMPLIFIED)
**Status**: 🟡 FEATURE - Required for customer customization
**Owner**: Full-Stack Lead + Designer

### ARCHITECTURE: SINGLE-TENANT SELF-HOSTED

This is **dramatically simpler** than multi-tenant SaaS:
- One deployment = one customer
- No organization FKs on every model
- No org-scoped queries
- Just a **SiteSettings** singleton model for branding
- Logo + colors configured once, applied globally
- Users registered by admin or invited

**What we DON'T need:**
- ❌ Organization model with FKs everywhere
- ❌ Organization middleware
- ❌ Org-scoped query managers
- ❌ Subdomain/path-based org detection
- ❌ Self-service organization registration

---

### P7.1: SiteSettings Model (Singleton)

**Problem**: No place to store site-wide branding configuration.

**Solution**: Single-row settings model.

```python
# backend/apps/core/models.py
from django.core.validators import RegexValidator
from django.db import models

class SiteSettings(models.Model):
    """
    Singleton model for site-wide branding configuration.
    Only one row should ever exist (enforced by save()).
    """
    # Identity
    site_name = models.CharField(max_length=255, default='EUCORA')
    site_tagline = models.CharField(max_length=500, blank=True, default='Enterprise Application Packaging & Deployment')

    # Logo
    logo_url = models.URLField(blank=True, null=True, help_text='URL to uploaded logo')
    favicon_url = models.URLField(blank=True, null=True, help_text='URL to favicon')

    # Primary Brand Colors
    color_primary = models.CharField(
        max_length=7, default='#3B82F6',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Must be hex color (#RRGGBB)')]
    )
    color_primary_light = models.CharField(max_length=7, default='#60A5FA')
    color_primary_dark = models.CharField(max_length=7, default='#1D4ED8')

    # Secondary Brand Colors
    color_secondary = models.CharField(max_length=7, default='#8B5CF6')
    color_secondary_light = models.CharField(max_length=7, default='#A78BFA')
    color_secondary_dark = models.CharField(max_length=7, default='#6D28D9')

    # Accent Color (for highlights, CTAs)
    color_accent = models.CharField(max_length=7, default='#F59E0B')
    color_accent_light = models.CharField(max_length=7, default='#FBBF24')
    color_accent_dark = models.CharField(max_length=7, default='#D97706')

    # Semantic Colors
    color_success = models.CharField(max_length=7, default='#10B981')
    color_warning = models.CharField(max_length=7, default='#F59E0B')
    color_error = models.CharField(max_length=7, default='#EF4444')
    color_info = models.CharField(max_length=7, default='#3B82F6')

    # Background Colors
    color_background = models.CharField(max_length=7, default='#F9FAFB')
    color_surface = models.CharField(max_length=7, default='#FFFFFF')
    color_surface_elevated = models.CharField(max_length=7, default='#FFFFFF')

    # Text Colors
    color_text_primary = models.CharField(max_length=7, default='#111827')
    color_text_secondary = models.CharField(max_length=7, default='#6B7280')
    color_text_muted = models.CharField(max_length=7, default='#9CA3AF')
    color_text_inverse = models.CharField(max_length=7, default='#FFFFFF')

    # Border Colors
    color_border = models.CharField(max_length=7, default='#E5E7EB')
    color_border_light = models.CharField(max_length=7, default='#F3F4F6')

    # Sidebar/Navigation Colors
    color_sidebar_bg = models.CharField(max_length=7, default='#1F2937')
    color_sidebar_text = models.CharField(max_length=7, default='#F9FAFB')
    color_sidebar_active = models.CharField(max_length=7, default='#3B82F6')

    # Header Colors
    color_header_bg = models.CharField(max_length=7, default='#FFFFFF')
    color_header_text = models.CharField(max_length=7, default='#111827')

    # Footer (for marketing page)
    color_footer_bg = models.CharField(max_length=7, default='#111827')
    color_footer_text = models.CharField(max_length=7, default='#9CA3AF')

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        db_table = 'site_settings'
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        # Enforce singleton: always use pk=1
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Site Settings - {self.site_name}"
```

**Acceptance Criteria**:
- [ ] SiteSettings model created with all color fields
- [ ] Singleton pattern enforced (only pk=1)
- [ ] Migration created and tested
- [ ] Default values match current Tailwind theme

---

### P7.2: Settings API Endpoints

**Problem**: Frontend needs to fetch branding, admin needs to update it.

**Public Endpoint** (no auth - needed for login page):
```python
# backend/apps/core/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])  # Public - needed before login
def get_site_branding(request):
    """
    Public endpoint to fetch site branding for theming.
    Called on app initialization and login page.
    """
    settings = SiteSettings.get_settings()
    return Response({
        'siteName': settings.site_name,
        'siteTagline': settings.site_tagline,
        'logoUrl': settings.logo_url,
        'faviconUrl': settings.favicon_url,
        'colors': {
            'primary': settings.color_primary,
            'primaryLight': settings.color_primary_light,
            'primaryDark': settings.color_primary_dark,
            'secondary': settings.color_secondary,
            'secondaryLight': settings.color_secondary_light,
            'secondaryDark': settings.color_secondary_dark,
            'accent': settings.color_accent,
            'accentLight': settings.color_accent_light,
            'accentDark': settings.color_accent_dark,
            'success': settings.color_success,
            'warning': settings.color_warning,
            'error': settings.color_error,
            'info': settings.color_info,
            'background': settings.color_background,
            'surface': settings.color_surface,
            'surfaceElevated': settings.color_surface_elevated,
            'textPrimary': settings.color_text_primary,
            'textSecondary': settings.color_text_secondary,
            'textMuted': settings.color_text_muted,
            'textInverse': settings.color_text_inverse,
            'border': settings.color_border,
            'borderLight': settings.color_border_light,
            'sidebarBg': settings.color_sidebar_bg,
            'sidebarText': settings.color_sidebar_text,
            'sidebarActive': settings.color_sidebar_active,
            'headerBg': settings.color_header_bg,
            'headerText': settings.color_header_text,
            'footerBg': settings.color_footer_bg,
            'footerText': settings.color_footer_text,
        },
    })
```

**Admin Endpoint** (auth required):
```python
@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def manage_site_settings(request):
    """
    Admin endpoint to view/update all site settings.
    """
    settings = SiteSettings.get_settings()

    if request.method == 'GET':
        serializer = SiteSettingsSerializer(settings)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SiteSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)
```

**Serializer**:
```python
class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        exclude = ['id', 'updated_by']
        read_only_fields = ['updated_at']
```

**Acceptance Criteria**:
- [ ] Public branding endpoint returns all colors
- [ ] Admin endpoint allows full CRUD
- [ ] updated_by tracks who changed settings
- [ ] Validation on hex color format

---

### P7.3: Logo Upload

**Problem**: Admin needs to upload custom logo.

**Upload Endpoint**:
```python
# backend/apps/core/views.py
from rest_framework.parsers import MultiPartParser
from PIL import Image
import io

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
@parser_classes([MultiPartParser])
def upload_logo(request):
    """
    Upload site logo. Stored in MinIO, URL saved to SiteSettings.
    """
    logo_file = request.FILES.get('logo')
    logo_type = request.data.get('type', 'logo')  # 'logo' or 'favicon'

    if not logo_file:
        return Response({'error': 'No file provided'}, status=400)

    # Validate file size (2MB for logo, 256KB for favicon)
    max_size = 256 * 1024 if logo_type == 'favicon' else 2 * 1024 * 1024
    if logo_file.size > max_size:
        return Response({
            'error': f'File too large (max {max_size // 1024}KB)'
        }, status=400)

    # Validate file type
    allowed_types = ['image/png', 'image/jpeg', 'image/svg+xml', 'image/x-icon']
    if logo_file.content_type not in allowed_types:
        return Response({
            'error': 'Invalid file type. Allowed: PNG, JPEG, SVG, ICO'
        }, status=400)

    # Process image (resize if needed, except SVG)
    if logo_file.content_type != 'image/svg+xml':
        max_dimension = 64 if logo_type == 'favicon' else 512
        processed = process_image(logo_file, max_dimension)
    else:
        processed = logo_file.read()

    # Upload to MinIO
    extension = logo_file.content_type.split('/')[-1].replace('x-icon', 'ico')
    key = f'branding/{logo_type}.{extension}'
    url = upload_to_minio(
        bucket='eucora-public',
        key=key,
        data=processed,
        content_type=logo_file.content_type,
        public=True
    )

    # Update settings
    settings = SiteSettings.get_settings()
    if logo_type == 'favicon':
        settings.favicon_url = url
    else:
        settings.logo_url = url
    settings.updated_by = request.user
    settings.save()

    return Response({
        'url': url,
        'type': logo_type,
        'message': f'{logo_type.title()} uploaded successfully'
    })


def process_image(file, max_dimension):
    """Resize image if larger than max_dimension, preserve aspect ratio."""
    img = Image.open(file)

    # Convert to RGB if necessary (for JPEG compatibility)
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGBA')

    # Resize if needed
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Save to bytes
    buffer = io.BytesIO()
    img_format = 'PNG' if img.mode == 'RGBA' else 'JPEG'
    img.save(buffer, format=img_format, quality=90)
    buffer.seek(0)
    return buffer.read()
```

**Acceptance Criteria**:
- [ ] Logo upload (max 2MB, 512x512)
- [ ] Favicon upload (max 256KB, 64x64)
- [ ] PNG, JPEG, SVG, ICO supported
- [ ] Automatic resize with aspect ratio preservation
- [ ] Stored in MinIO public bucket
- [ ] URL saved to SiteSettings

---

### P7.4: Frontend Theme System

**Problem**: Apply branding colors throughout the app at runtime.

**Theme Types**:
```typescript
// frontend/src/types/theme.ts
export interface SiteBranding {
  siteName: string;
  siteTagline: string;
  logoUrl: string | null;
  faviconUrl: string | null;
  colors: ThemeColors;
}

export interface ThemeColors {
  primary: string;
  primaryLight: string;
  primaryDark: string;
  secondary: string;
  secondaryLight: string;
  secondaryDark: string;
  accent: string;
  accentLight: string;
  accentDark: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  background: string;
  surface: string;
  surfaceElevated: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textInverse: string;
  border: string;
  borderLight: string;
  sidebarBg: string;
  sidebarText: string;
  sidebarActive: string;
  headerBg: string;
  headerText: string;
  footerBg: string;
  footerText: string;
}
```

**Theme Context**:
```typescript
// frontend/src/context/ThemeContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { SiteBranding, ThemeColors } from '@/types/theme';

const DEFAULT_BRANDING: SiteBranding = {
  siteName: 'EUCORA',
  siteTagline: 'Enterprise Application Packaging & Deployment',
  logoUrl: null,
  faviconUrl: null,
  colors: {
    primary: '#3B82F6',
    primaryLight: '#60A5FA',
    primaryDark: '#1D4ED8',
    secondary: '#8B5CF6',
    secondaryLight: '#A78BFA',
    secondaryDark: '#6D28D9',
    accent: '#F59E0B',
    accentLight: '#FBBF24',
    accentDark: '#D97706',
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
    info: '#3B82F6',
    background: '#F9FAFB',
    surface: '#FFFFFF',
    surfaceElevated: '#FFFFFF',
    textPrimary: '#111827',
    textSecondary: '#6B7280',
    textMuted: '#9CA3AF',
    textInverse: '#FFFFFF',
    border: '#E5E7EB',
    borderLight: '#F3F4F6',
    sidebarBg: '#1F2937',
    sidebarText: '#F9FAFB',
    sidebarActive: '#3B82F6',
    headerBg: '#FFFFFF',
    headerText: '#111827',
    footerBg: '#111827',
    footerText: '#9CA3AF',
  },
};

interface ThemeContextValue {
  branding: SiteBranding;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const ThemeContext = createContext<ThemeContextValue>({
  branding: DEFAULT_BRANDING,
  loading: true,
  error: null,
  refresh: async () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [branding, setBranding] = useState<SiteBranding>(DEFAULT_BRANDING);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBranding = async () => {
    try {
      const response = await fetch('/api/v1/site/branding');
      if (!response.ok) throw new Error('Failed to fetch branding');
      const data = await response.json();
      setBranding(data);
      applyThemeToDOM(data.colors);
      updateFavicon(data.faviconUrl);
      updateDocumentTitle(data.siteName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      // Use defaults on error
      applyThemeToDOM(DEFAULT_BRANDING.colors);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBranding();
  }, []);

  return (
    <ThemeContext.Provider value={{ branding, loading, error, refresh: fetchBranding }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);

function applyThemeToDOM(colors: ThemeColors) {
  const root = document.documentElement;

  // Map all colors to CSS custom properties
  Object.entries(colors).forEach(([key, value]) => {
    // Convert camelCase to kebab-case: primaryLight -> primary-light
    const cssVar = key.replace(/([A-Z])/g, '-$1').toLowerCase();
    root.style.setProperty(`--color-${cssVar}`, value);
  });
}

function updateFavicon(url: string | null) {
  if (!url) return;
  const link = document.querySelector<HTMLLinkElement>("link[rel*='icon']")
    || document.createElement('link');
  link.rel = 'icon';
  link.href = url;
  document.head.appendChild(link);
}

function updateDocumentTitle(siteName: string) {
  // Update base title, but preserve page-specific suffix
  const currentTitle = document.title;
  const separator = ' | ';
  if (currentTitle.includes(separator)) {
    const pagePart = currentTitle.split(separator).pop();
    document.title = `${siteName}${separator}${pagePart}`;
  } else {
    document.title = siteName;
  }
}
```

**Tailwind Config with CSS Variables**:
```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand colors - all use CSS variables with fallbacks
        primary: {
          DEFAULT: 'var(--color-primary, #3B82F6)',
          light: 'var(--color-primary-light, #60A5FA)',
          dark: 'var(--color-primary-dark, #1D4ED8)',
        },
        secondary: {
          DEFAULT: 'var(--color-secondary, #8B5CF6)',
          light: 'var(--color-secondary-light, #A78BFA)',
          dark: 'var(--color-secondary-dark, #6D28D9)',
        },
        accent: {
          DEFAULT: 'var(--color-accent, #F59E0B)',
          light: 'var(--color-accent-light, #FBBF24)',
          dark: 'var(--color-accent-dark, #D97706)',
        },
        // Semantic colors
        success: 'var(--color-success, #10B981)',
        warning: 'var(--color-warning, #F59E0B)',
        error: 'var(--color-error, #EF4444)',
        info: 'var(--color-info, #3B82F6)',
        // Surface colors
        background: 'var(--color-background, #F9FAFB)',
        surface: {
          DEFAULT: 'var(--color-surface, #FFFFFF)',
          elevated: 'var(--color-surface-elevated, #FFFFFF)',
        },
        // Text colors
        'text-primary': 'var(--color-text-primary, #111827)',
        'text-secondary': 'var(--color-text-secondary, #6B7280)',
        'text-muted': 'var(--color-text-muted, #9CA3AF)',
        'text-inverse': 'var(--color-text-inverse, #FFFFFF)',
        // Border colors
        border: {
          DEFAULT: 'var(--color-border, #E5E7EB)',
          light: 'var(--color-border-light, #F3F4F6)',
        },
        // Layout colors
        sidebar: {
          bg: 'var(--color-sidebar-bg, #1F2937)',
          text: 'var(--color-sidebar-text, #F9FAFB)',
          active: 'var(--color-sidebar-active, #3B82F6)',
        },
        header: {
          bg: 'var(--color-header-bg, #FFFFFF)',
          text: 'var(--color-header-text, #111827)',
        },
        footer: {
          bg: 'var(--color-footer-bg, #111827)',
          text: 'var(--color-footer-text, #9CA3AF)',
        },
      },
    },
  },
  plugins: [],
};
```

**Acceptance Criteria**:
- [ ] ThemeProvider fetches branding on app load
- [ ] All CSS variables injected into :root
- [ ] Tailwind classes use CSS variables
- [ ] Favicon dynamically updated
- [ ] Document title uses site name
- [ ] Fallback to defaults if API fails

---

### P7.5: Admin Branding Settings Page

**Problem**: Admin needs UI to customize branding.

```tsx
// frontend/src/routes/admin/BrandingSettings.tsx
import { useState } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { useMutation, useQuery } from '@tanstack/react-query';

export function BrandingSettings() {
  const { refresh } = useTheme();
  const [activeTab, setActiveTab] = useState<'general' | 'colors' | 'preview'>('general');

  const { data: settings, isLoading } = useQuery({
    queryKey: ['admin', 'site-settings'],
    queryFn: () => fetch('/api/v1/admin/site-settings').then(r => r.json()),
  });

  const updateMutation = useMutation({
    mutationFn: (data: Partial<SiteSettings>) =>
      fetch('/api/v1/admin/site-settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      refresh(); // Reload theme throughout app
    },
  });

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Site Branding</h1>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {['general', 'colors', 'preview'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as typeof activeTab)}
            className={`px-4 py-2 capitalize ${
              activeTab === tab
                ? 'border-b-2 border-primary text-primary font-medium'
                : 'text-text-secondary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="space-y-6">
          {/* Site Name */}
          <div>
            <label className="block text-sm font-medium mb-1">Site Name</label>
            <input
              type="text"
              value={settings.site_name}
              onChange={e => updateMutation.mutate({ site_name: e.target.value })}
              className="w-full border rounded px-3 py-2"
            />
          </div>

          {/* Logo Upload */}
          <div>
            <label className="block text-sm font-medium mb-1">Logo</label>
            <div className="flex items-center gap-4">
              {settings.logo_url && (
                <img src={settings.logo_url} alt="Logo" className="h-16" />
              )}
              <LogoUploader
                type="logo"
                onUpload={(url) => refresh()}
              />
            </div>
            <p className="text-sm text-text-muted mt-1">
              PNG, JPEG, or SVG. Max 2MB, 512x512px recommended.
            </p>
          </div>

          {/* Favicon Upload */}
          <div>
            <label className="block text-sm font-medium mb-1">Favicon</label>
            <div className="flex items-center gap-4">
              {settings.favicon_url && (
                <img src={settings.favicon_url} alt="Favicon" className="h-8 w-8" />
              )}
              <LogoUploader
                type="favicon"
                onUpload={(url) => refresh()}
              />
            </div>
          </div>
        </div>
      )}

      {/* Colors Tab */}
      {activeTab === 'colors' && (
        <div className="space-y-8">
          {/* Primary Colors */}
          <ColorSection
            title="Primary Brand Colors"
            colors={[
              { key: 'color_primary', label: 'Primary', value: settings.color_primary },
              { key: 'color_primary_light', label: 'Primary Light', value: settings.color_primary_light },
              { key: 'color_primary_dark', label: 'Primary Dark', value: settings.color_primary_dark },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Secondary Colors */}
          <ColorSection
            title="Secondary Colors"
            colors={[
              { key: 'color_secondary', label: 'Secondary', value: settings.color_secondary },
              { key: 'color_secondary_light', label: 'Secondary Light', value: settings.color_secondary_light },
              { key: 'color_secondary_dark', label: 'Secondary Dark', value: settings.color_secondary_dark },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Accent Colors */}
          <ColorSection
            title="Accent Colors"
            colors={[
              { key: 'color_accent', label: 'Accent', value: settings.color_accent },
              { key: 'color_accent_light', label: 'Accent Light', value: settings.color_accent_light },
              { key: 'color_accent_dark', label: 'Accent Dark', value: settings.color_accent_dark },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Semantic Colors */}
          <ColorSection
            title="Semantic Colors"
            colors={[
              { key: 'color_success', label: 'Success', value: settings.color_success },
              { key: 'color_warning', label: 'Warning', value: settings.color_warning },
              { key: 'color_error', label: 'Error', value: settings.color_error },
              { key: 'color_info', label: 'Info', value: settings.color_info },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Surface Colors */}
          <ColorSection
            title="Background & Surface"
            colors={[
              { key: 'color_background', label: 'Background', value: settings.color_background },
              { key: 'color_surface', label: 'Surface', value: settings.color_surface },
              { key: 'color_surface_elevated', label: 'Elevated Surface', value: settings.color_surface_elevated },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Text Colors */}
          <ColorSection
            title="Text Colors"
            colors={[
              { key: 'color_text_primary', label: 'Primary Text', value: settings.color_text_primary },
              { key: 'color_text_secondary', label: 'Secondary Text', value: settings.color_text_secondary },
              { key: 'color_text_muted', label: 'Muted Text', value: settings.color_text_muted },
              { key: 'color_text_inverse', label: 'Inverse Text', value: settings.color_text_inverse },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Layout Colors */}
          <ColorSection
            title="Layout Colors"
            colors={[
              { key: 'color_sidebar_bg', label: 'Sidebar Background', value: settings.color_sidebar_bg },
              { key: 'color_sidebar_text', label: 'Sidebar Text', value: settings.color_sidebar_text },
              { key: 'color_sidebar_active', label: 'Sidebar Active', value: settings.color_sidebar_active },
              { key: 'color_header_bg', label: 'Header Background', value: settings.color_header_bg },
              { key: 'color_header_text', label: 'Header Text', value: settings.color_header_text },
              { key: 'color_footer_bg', label: 'Footer Background', value: settings.color_footer_bg },
              { key: 'color_footer_text', label: 'Footer Text', value: settings.color_footer_text },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Border Colors */}
          <ColorSection
            title="Border Colors"
            colors={[
              { key: 'color_border', label: 'Border', value: settings.color_border },
              { key: 'color_border_light', label: 'Light Border', value: settings.color_border_light },
            ]}
            onChange={updateMutation.mutate}
          />

          {/* Reset Button */}
          <button
            onClick={() => updateMutation.mutate(DEFAULT_COLORS)}
            className="px-4 py-2 border border-error text-error rounded hover:bg-error hover:text-white"
          >
            Reset to Defaults
          </button>
        </div>
      )}

      {/* Preview Tab */}
      {activeTab === 'preview' && (
        <BrandingPreview settings={settings} />
      )}
    </div>
  );
}

function ColorSection({ title, colors, onChange }) {
  return (
    <div>
      <h3 className="text-lg font-medium mb-3">{title}</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {colors.map(({ key, label, value }) => (
          <div key={key}>
            <label className="block text-sm mb-1">{label}</label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={value}
                onChange={e => onChange({ [key]: e.target.value })}
                className="w-10 h-10 rounded cursor-pointer border"
              />
              <input
                type="text"
                value={value}
                onChange={e => onChange({ [key]: e.target.value })}
                className="flex-1 border rounded px-2 py-1 font-mono text-sm"
                pattern="^#[0-9A-Fa-f]{6}$"
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Admin can edit site name and tagline
- [ ] Admin can upload logo and favicon
- [ ] Admin can customize all 30+ color variables
- [ ] Live preview of changes
- [ ] Reset to defaults option
- [ ] Changes reflect immediately site-wide

---

### P7.6: Refactor Existing Components

**Problem**: Existing components use hardcoded Tailwind colors.

**Migration Pattern**:
```diff
# Before (hardcoded)
- <button className="bg-blue-500 hover:bg-blue-600 text-white">
- <div className="text-gray-600">
- <nav className="bg-gray-800 text-white">

# After (CSS variable-based)
+ <button className="bg-primary hover:bg-primary-dark text-text-inverse">
+ <div className="text-text-secondary">
+ <nav className="bg-sidebar-bg text-sidebar-text">
```

**Components to Refactor** (audit required):
1. **Layout components**: Sidebar, Header, Footer
2. **Form components**: Button, Input, Select, Checkbox
3. **Feedback components**: Alert, Toast, Badge, Tag
4. **Navigation components**: Tabs, Breadcrumbs, Pagination
5. **Data display**: Table, Card, List
6. **All page components**: Login, Dashboard, etc.

**Acceptance Criteria**:
- [ ] All `bg-blue-*` replaced with `bg-primary*`
- [ ] All `bg-gray-*` replaced with semantic colors
- [ ] All `text-gray-*` replaced with `text-text-*`
- [ ] All `border-gray-*` replaced with `border*`
- [ ] Zero hardcoded color values remain
- [ ] Visual regression testing passes

---

## Phase 8: Marketing & Public Pages

**Timeline**: Week 11
**Status**: 🟡 FEATURE - Required for public presence
**Owner**: Frontend Lead + Marketing

### P8.1: Marketing Landing Page

**Problem**: No public-facing page to explain the product.

**Architecture Decision**: Separate from main app.

**Recommended Approach**:
```
eucora.com/                → Marketing site (static or Next.js)
eucora.com/login           → Redirect to app.eucora.com/login
app.eucora.com/            → Main application
acme.eucora.com/           → Org-specific app access
```

**Marketing Page Structure**:
```tsx
// frontend/src/routes/marketing/LandingPage.tsx
export function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="flex justify-between items-center px-8 py-4 bg-white shadow">
        <img src="/eucora-logo.svg" alt="EUCORA" className="h-8" />
        <div className="flex gap-4">
          <Link
            to="/demo"
            className="px-4 py-2 text-gray-700 hover:text-primary"
          >
            Try Demo
          </Link>
          <Link
            to="/login"
            className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
          >
            Login
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="py-20 px-8 bg-gradient-to-br from-blue-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-6">
            Enterprise Application Packaging & Deployment
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Automate your software deployment lifecycle with CAB-approved
            governance, ring-based rollouts, and complete audit trails.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              to="/register"
              className="px-8 py-3 bg-primary text-white text-lg rounded-lg hover:bg-primary-dark"
            >
              Start Free Trial
            </Link>
            <Link
              to="/demo"
              className="px-8 py-3 border border-primary text-primary text-lg rounded-lg hover:bg-blue-50"
            >
              Watch Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 px-8">
        <div className="max-w-6xl mx-auto grid grid-cols-3 gap-8">
          <FeatureCard
            icon={<ShieldIcon />}
            title="CAB Governance"
            description="Built-in Change Advisory Board workflows with risk scoring and evidence packs."
          />
          <FeatureCard
            icon={<LayersIcon />}
            title="Ring-Based Rollouts"
            description="Lab → Canary → Pilot → Production with automatic promotion gates."
          />
          <FeatureCard
            icon={<ConnectIcon />}
            title="Multi-Platform"
            description="Intune, SCCM, Jamf, Landscape, Ansible - all from one control plane."
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-8 bg-primary text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to modernize your deployment pipeline?
          </h2>
          <Link
            to="/register"
            className="inline-block px-8 py-3 bg-white text-primary text-lg rounded-lg hover:bg-gray-100"
          >
            Get Started Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-8 bg-gray-900 text-gray-400">
        {/* Footer content */}
      </footer>
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Landing page explains product value
- [ ] Login button navigates to login flow
- [ ] Demo button navigates to demo mode
- [ ] Mobile responsive
- [ ] SEO meta tags present

---

### P8.2: Login/Signup Selection Page

**Problem**: User clicks "Login" - do they want to login or signup?

**Solution**: Combined auth page with tabs.

```tsx
// frontend/src/routes/auth/AuthPage.tsx
export function AuthPage() {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const { orgSlug } = useParams();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
        {/* Tabs */}
        <div className="flex border-b mb-6">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 py-2 text-center ${
              mode === 'login'
                ? 'border-b-2 border-primary text-primary font-medium'
                : 'text-gray-500'
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => setMode('signup')}
            className={`flex-1 py-2 text-center ${
              mode === 'signup'
                ? 'border-b-2 border-primary text-primary font-medium'
                : 'text-gray-500'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Form */}
        {mode === 'login' ? (
          <LoginForm orgSlug={orgSlug} />
        ) : (
          <SignupForm orgSlug={orgSlug} />
        )}
      </div>
    </div>
  );
}
```

**Routes Configuration**:
```tsx
// frontend/src/App.tsx
<Routes>
  {/* Public routes */}
  <Route path="/" element={<LandingPage />} />
  <Route path="/demo" element={<DemoRedirect />} />

  {/* Auth routes */}
  <Route path="/login" element={<AuthPage />} />
  <Route path="/signup" element={<AuthPage />} />
  <Route path="/register" element={<OrgRegistrationPage />} />

  {/* Org-scoped auth */}
  <Route path="/org/:orgSlug/login" element={<AuthPage />} />
  <Route path="/org/:orgSlug/signup" element={<AuthPage />} />

  {/* Protected app routes */}
  <Route path="/app/*" element={<ProtectedLayout />}>
    {/* ... app routes */}
  </Route>
</Routes>
```

**Acceptance Criteria**:
- [ ] Single page handles both login and signup
- [ ] Tab state reflects in URL (/login vs /signup)
- [ ] Org context preserved when switching modes
- [ ] Form validation on both modes

---

### P8.3: Demo Mode Entry Point

**Problem**: "Demo" button on marketing page needs clear path.

**Demo Flow**:
```
1. User clicks "Try Demo" on marketing page
2. → Redirect to /demo
3. → Auto-login with demo credentials (if DEMO_MODE=true)
4. → Land on dashboard with demo data visible
5. → Banner shows "DEMO MODE - Not production data"
```

**Demo Redirect Component**:
```tsx
// frontend/src/routes/DemoRedirect.tsx
export function DemoRedirect() {
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const enterDemo = async () => {
      if (import.meta.env.VITE_DEMO_MODE !== 'true') {
        // Demo not available - show message
        navigate('/login', {
          state: { message: 'Demo mode not available in production' }
        });
        return;
      }

      // Auto-login with demo credentials
      try {
        await login({
          username: 'demo',
          password: import.meta.env.VITE_DEMO_PASSWORD,
        });
        navigate('/app/dashboard');
      } catch {
        navigate('/login', {
          state: { message: 'Demo login failed' }
        });
      }
    };

    enterDemo();
  }, []);

  return <LoadingSpinner message="Entering demo mode..." />;
}
```

**Demo Mode Banner**:
```tsx
// frontend/src/components/DemoModeBanner.tsx
export function DemoModeBanner() {
  if (import.meta.env.VITE_DEMO_MODE !== 'true') return null;

  return (
    <div className="bg-yellow-500 text-yellow-900 text-center py-2 text-sm font-medium">
      ⚠️ DEMO MODE - Data shown is for demonstration purposes only
    </div>
  );
}
```

**Acceptance Criteria**:
- [ ] Demo button works when DEMO_MODE=true
- [ ] Demo button shows message when DEMO_MODE=false
- [ ] Demo banner visible throughout session
- [ ] Demo data clearly marked

---

### P8.4: Organization Registration Page

**Problem**: New customers need to create their organization.

```tsx
// frontend/src/routes/auth/OrgRegistrationPage.tsx
export function OrgRegistrationPage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    organizationName: '',
    adminEmail: '',
    adminPassword: '',
    primaryColor: '#3B82F6',
    logo: null as File | null,
  });

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto">
        {/* Progress Steps */}
        <div className="flex justify-center mb-8">
          <StepIndicator current={step} total={3} />
        </div>

        <div className="bg-white p-8 rounded-lg shadow-lg">
          {step === 1 && (
            <OrgDetailsStep
              formData={formData}
              onChange={setFormData}
              onNext={() => setStep(2)}
            />
          )}

          {step === 2 && (
            <BrandingStep
              formData={formData}
              onChange={setFormData}
              onBack={() => setStep(1)}
              onNext={() => setStep(3)}
            />
          )}

          {step === 3 && (
            <AdminAccountStep
              formData={formData}
              onChange={setFormData}
              onBack={() => setStep(2)}
              onSubmit={handleSubmit}
            />
          )}
        </div>
      </div>
    </div>
  );
}

function OrgDetailsStep({ formData, onChange, onNext }) {
  return (
    <>
      <h2 className="text-2xl font-bold mb-6">Organization Details</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Organization Name *
          </label>
          <input
            type="text"
            value={formData.organizationName}
            onChange={(e) => onChange({...formData, organizationName: e.target.value})}
            className="w-full border rounded px-3 py-2"
            placeholder="Acme Corporation"
          />
          <p className="text-sm text-gray-500 mt-1">
            This will be displayed throughout the application
          </p>
        </div>
      </div>

      <button onClick={onNext} className="mt-6 w-full bg-primary text-white py-2 rounded">
        Continue
      </button>
    </>
  );
}

function BrandingStep({ formData, onChange, onBack, onNext }) {
  return (
    <>
      <h2 className="text-2xl font-bold mb-6">Customize Branding</h2>

      <div className="space-y-6">
        {/* Logo Upload */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Organization Logo
          </label>
          <LogoUploader
            value={formData.logo}
            onChange={(file) => onChange({...formData, logo: file})}
          />
          <p className="text-sm text-gray-500 mt-1">
            PNG, JPG, or SVG. Max 2MB. Recommended: 512x512px
          </p>
        </div>

        {/* Color Picker */}
        <div>
          <label className="block text-sm font-medium mb-1">
            Primary Color
          </label>
          <div className="flex items-center gap-4">
            <input
              type="color"
              value={formData.primaryColor}
              onChange={(e) => onChange({...formData, primaryColor: e.target.value})}
              className="w-12 h-12 rounded cursor-pointer"
            />
            <input
              type="text"
              value={formData.primaryColor}
              onChange={(e) => onChange({...formData, primaryColor: e.target.value})}
              className="border rounded px-3 py-2 w-32 font-mono"
              pattern="^#[0-9A-Fa-f]{6}$"
            />
          </div>
        </div>

        {/* Preview */}
        <div>
          <label className="block text-sm font-medium mb-2">Preview</label>
          <div
            className="p-4 rounded border"
            style={{ borderColor: formData.primaryColor }}
          >
            <button
              className="px-4 py-2 text-white rounded"
              style={{ backgroundColor: formData.primaryColor }}
            >
              Sample Button
            </button>
          </div>
        </div>
      </div>

      <div className="flex gap-4 mt-6">
        <button onClick={onBack} className="flex-1 border py-2 rounded">
          Back
        </button>
        <button onClick={onNext} className="flex-1 bg-primary text-white py-2 rounded">
          Continue
        </button>
      </div>
    </>
  );
}
```

**Acceptance Criteria**:
- [ ] Multi-step registration form
- [ ] Logo upload with preview
- [ ] Color picker with live preview
- [ ] Form validation at each step
- [ ] Submit creates organization + admin user

---

This plan is non-negotiable. Each phase builds on the previous. Skipping phases creates compounding risk. Execute in order, validate at each gate, or don't ship.
