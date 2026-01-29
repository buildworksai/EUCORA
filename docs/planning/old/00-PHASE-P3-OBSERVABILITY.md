# Phase P3: Observability & Operations

**Status**: EXECUTING
**Duration**: 1 week
**Prerequisite**: P2 (Resilience & Reliability) ✅ COMPLETE

---

## Objective

Achieve production-grade observability: structured logging with correlation IDs, comprehensive health checks, sanitized error responses, and operational visibility into system state. Enable rapid debugging and incident response.

---

## Deliverables

### P3.1: Structured JSON Logging ✅ IN PROGRESS

**Objective**: All logs in JSON format with `correlation_id` on every entry for audit trail tracking.

**Deliverables**:
- [ ] Backend: pythonjsonlogger formatter integration
- [ ] Middleware: Inject correlation_id on every request
- [ ] Models: correlation_id field on all business-critical models
- [ ] Services: All service operations log with correlation_id
- [ ] Tests: Verify JSON structure and correlation_id propagation

**Required Fields** (per CLAUDE.md):
```json
{
  "timestamp": "2026-01-22T10:30:00Z",
  "level": "INFO",
  "service_name": "eucora-control-plane",
  "correlation_id": "abc-123-def-456",
  "user_id": "user@example.com",
  "message": "Event description",
  "context": { "extra": "data" }
}
```

**Files to Create/Modify**:
- `backend/apps/core/logging.py` - Custom JSON formatter
- `backend/apps/core/middleware.py` - Inject correlation_id on request
- `backend/config/settings/logging.py` - LOGGING configuration
- All apps that make requests must pass correlation_id

### P3.2: Frontend Logger Implementation

**Objective**: Remove all `console.log/error/warn`, implement typed logger, send to Sentry/LogRocket.

**Deliverables**:
- [ ] Create `frontend/src/lib/logger.ts` with typed logger interface
- [ ] Replace console statements in all components (authenticated scan)
- [ ] Sentry integration for production error tracking
- [ ] Development mode: console passthrough
- [ ] Zero console.log in production bundle (verified via build)

**Logger Interface**:
```typescript
interface Logger {
  info(message: string, context?: Record<string, any>): void;
  warn(message: string, context?: Record<string, any>): void;
  error(message: string, error?: Error, context?: Record<string, any>): void;
  debug(message: string, context?: Record<string, any>): void;
}

export const logger = createLogger('frontend');
```

**Files to Create/Modify**:
- `frontend/src/lib/logger.ts` - Logger implementation
- `frontend/src/lib/api/client.ts` - Log API errors with correlation_id
- All React components using console statements

### P3.3: Error Response Sanitization

**Objective**: Never expose internal details (stack traces, SQL, file paths). Always expose correlation_id for debugging.

**Sanitization Pattern**:
- **Expose to Client**: `{ "error": "User-friendly message", "correlation_id": "..." }`
- **Log Server-Side**: Full error context with stack trace + SQL + internal state (secure, searchable)

**Implementation**:
- Create DRF exception handler that sanitizes responses
- All errors return correlation_id for log lookup
- 5xx errors: generic "internal server error" message
- 4xx errors: specific validation messages
- No Stack traces in 500 responses

**Files to Create/Modify**:
- `backend/config/exception_handler.py` - Sanitization logic
- `backend/config/settings/rest_framework.py` - Register exception handler

### P3.4: Enhanced Health Checks

**Objective**: `/api/v1/health/` endpoint that verifies all dependencies (database, Redis, Celery, MinIO, circuit breakers).

**Health Check Components**:
- [ ] Database connectivity + query latency
- [ ] Redis connectivity + ping latency
- [ ] Celery worker availability (at least 1 active)
- [ ] MinIO object store connectivity
- [ ] Circuit breaker status summary
- [ ] External service circuit breaker states

**Response Structure**:
```json
{
  "status": "healthy" | "degraded" | "unhealthy",
  "timestamp": "2026-01-22T10:30:00Z",
  "checks": {
    "database": { "status": "healthy", "latency_ms": 5 },
    "redis": { "status": "healthy", "latency_ms": 2 },
    "celery": { "status": "healthy", "active_workers": 3 },
    "minio": { "status": "healthy", "latency_ms": 10 },
    "circuit_breakers": {
      "status": "healthy",
      "open_count": 0,
      "total": 16
    }
  }
}
```

**Endpoint**: `GET /api/v1/health/`
- Returns 200 if all healthy
- Returns 503 if any degraded/unhealthy
- No authentication required (for load balancers)

**Files to Create/Modify**:
- `backend/apps/core/health.py` - Health check implementations
- `backend/apps/core/views_health.py` - Extend with comprehensive checks

### P3.5: Test Coverage (≥90%)

**Objective**: Comprehensive tests for logging, health checks, error handling.

**Test Files to Create**:
- `backend/apps/core/tests/test_logging.py` - JSON format, correlation_id propagation
- `backend/apps/core/tests/test_health.py` - All health check paths
- `backend/config/tests/test_exception_handler.py` - Error sanitization

**Test Scenarios**:
- Correlation ID generated on request entry
- Correlation ID passed through service calls
- JSON logging validates schema
- Error responses sanitized (no stack traces)
- Health endpoint with all dependencies healthy
- Health endpoint with one dependency down (returns 503)
- Health endpoint with circuit breaker open (marked degraded)

---

## Architecture Decisions

### Correlation ID Strategy

1. **Generated on Request Entry**: Middleware creates UUID if not provided
2. **Propagated Through Services**: All HTTP calls include header: `X-Correlation-ID`
3. **Logged on Every Operation**: Every log entry includes `correlation_id`
4. **Included in Error Responses**: Client gets correlation_id to lookup logs
5. **Async Tasks**: Celery tasks inherit correlation_id from creating request

**Implementation Pattern**:
```python
# In middleware
correlation_id = request.META.get('HTTP_X_CORRELATION_ID', str(uuid.uuid4()))
request.correlation_id = correlation_id

# In every service call
client.get(url, headers={'X-Correlation-ID': correlation_id})

# In every log
logger.info('Action completed', extra={'correlation_id': correlation_id})
```

### JSON Logging Schema

All logs must validate against this schema:
- `timestamp`: ISO 8601 UTC
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `service_name`: "eucora-control-plane"
- `correlation_id`: UUID v4 or trace ID
- `user_id`: Optional, if available
- `message`: Clear, actionable message
- `context`: Optional extra fields

### Error Sanitization Rules

**NEVER expose in client response**:
- Stack traces
- SQL queries or table names
- File paths
- Internal variable values
- Database connection strings
- API keys or tokens

**ALWAYS expose**:
- Correlation ID (for log lookup)
- HTTP status code
- User-friendly error message
- Field validation errors (for 400s)

**Log server-side (secure)**:
- Full stack trace
- SQL query + parameters
- Internal state
- Request/response bodies

---

## Quality Gates

- [ ] All tests pass (pytest)
- [ ] ≥90% test coverage (measured via pytest-cov)
- [ ] Django check passes (0 errors)
- [ ] Zero console.log in production bundle (verified)
- [ ] Health endpoint verifies all dependencies
- [ ] All error responses sanitized (no stack traces)
- [ ] Correlation ID on every log entry
- [ ] API documentation updated with correlation_id header

---

## Files to Create/Modify

```
backend/
├── apps/core/
│   ├── logging.py (CREATE) - JSON formatter + correlation_id injection
│   ├── health.py (CREATE) - Health check components
│   ├── views_health.py (MODIFY) - Extend with comprehensive checks
│   ├── middleware.py (CREATE/MODIFY) - Inject correlation_id
│   └── tests/
│       ├── test_logging.py (CREATE)
│       ├── test_health.py (CREATE)
│       └── test_correlation_id.py (CREATE)
├── config/
│   ├── exception_handler.py (CREATE) - Error sanitization
│   ├── settings/logging.py (CREATE) - LOGGING config
│   ├── settings/base.py (MODIFY) - Add logging + exception handler
│   └── tests/
│       └── test_exception_handler.py (CREATE)
└── tests/integration/
    └── test_health_checks.py (CREATE) - E2E health checks

frontend/
├── src/lib/
│   └── logger.ts (CREATE) - Frontend logger
├── src/lib/api/
│   └── client.ts (MODIFY) - Pass correlation_id header
└── src/tests/
    └── logger.test.ts (CREATE)

docs/
├── runbooks/
│   ├── log-analysis.md (CREATE) - How to search logs by correlation_id
│   └── health-check-failures.md (CREATE) - Troubleshooting health endpoint
└── architecture/
    └── observability.md (CREATE) - Logging & correlation ID design
```

---

## Success Criteria

✅ **P3 is COMPLETE when**:
1. All logs output JSON format with correlation_id
2. All error responses are sanitized (no stack traces)
3. Health endpoint verifies all dependencies
4. ≥90% test coverage achieved
5. Zero console.log statements in frontend
6. Django check passes (0 errors)
7. API documentation includes correlation_id header

**Target Completion**: January 23, 2026 (1 day)
