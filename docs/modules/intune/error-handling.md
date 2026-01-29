# Intune Connector Error Handling

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This document defines **error classification** and **retry logic** for the Intune connector. All errors are classified as transient, permanent, or policy violation.

**Design Principle**: Idempotency — all operations are safe to retry.

---

## Error Classification

### Transient Errors

**Definition**: Temporary failures that may succeed on retry

**Examples**:
- HTTP 429 (Too Many Requests) - Rate limiting
- HTTP 503 (Service Unavailable) - Service degradation
- HTTP 500 (Internal Server Error) - Temporary server error
- Network timeouts
- Graph API eventual consistency delays

**Handling**:
- Exponential backoff retry (1s, 2s, 4s, 8s, 16s)
- Maximum retries: 5
- Idempotent keys used for safe retries

### Permanent Errors

**Definition**: Errors that will not succeed on retry

**Examples**:
- HTTP 400 (Bad Request) - Invalid request data
- HTTP 401 (Unauthorized) - Authentication failure
- HTTP 403 (Forbidden) - Insufficient permissions
- HTTP 404 (Not Found) - Resource does not exist
- HTTP 409 (Conflict) - Resource conflict (non-retryable)

**Handling**:
- No retry
- Error logged to event store
- Notification sent to deployment owner

### Policy Violations

**Definition**: Errors indicating policy constraint violations

**Examples**:
- Scope validation failures
- RBAC permission violations
- CAB approval missing
- Risk score threshold exceeded

**Handling**:
- No retry
- Error logged to event store
- CAB/Security team notification
- Deployment blocked

---

## Retry Logic

### Exponential Backoff

```python
def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            time.sleep(wait_time)
```

### Idempotent Keys

**Usage**: All create/update operations use idempotent keys

**Format**: `{deployment_intent_id}-{operation}-{timestamp}`

**Example**:
```python
idempotent_key = f"{deployment_intent_id}-create-assignment-{timestamp}"
```

---

## Graph API Specific Handling

### Rate Limiting

**Detection**: HTTP 429 response
**Headers**: `Retry-After` header indicates wait time

**Handling**:
```python
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    retry_request()
```

### Pagination

**Handling**: All list operations paginated

**Implementation**:
```python
def get_all_pages(url, headers):
    all_items = []
    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        all_items.extend(data.get('value', []))
        url = data.get('@odata.nextLink')
    return all_items
```

### Eventual Consistency

**Handling**: Query operations may return stale data

**Strategy**:
- Wait 5 seconds after create/update before query
- Retry query up to 3 times if data not found
- Use correlation IDs for tracking

---

## Error Response Mapping

### Graph API Errors

| HTTP Status | Error Code | Classification | Action |
|-------------|------------|----------------|--------|
| 200 | Success | - | Continue |
| 400 | BadRequest | Permanent | Log error, no retry |
| 401 | Unauthorized | Permanent | Refresh token, retry once |
| 403 | Forbidden | Policy Violation | Log, notify, block |
| 404 | NotFound | Permanent | Log error, no retry |
| 409 | Conflict | Permanent/Transient | Check idempotent key |
| 429 | TooManyRequests | Transient | Retry with backoff |
| 500 | InternalServerError | Transient | Retry with backoff |
| 503 | ServiceUnavailable | Transient | Retry with backoff |

---

## Error Logging

### Event Store Events

```json
{
  "correlation_id": "uuid",
  "event_type": "CONNECTOR_ERROR",
  "event_data": {
    "connector_type": "intune",
    "operation": "create_assignment",
    "error_classification": "transient|permanent|policy_violation",
    "error_code": "429",
    "error_message": "Rate limit exceeded",
    "retry_count": 3,
    "deployment_intent_id": "uuid"
  },
  "actor": "system:intune_connector",
  "created_at": "2026-01-06T10:00:00Z"
}
```

---

## References

- [Intune Connector Spec](./connector-spec.md)
- [Rollback Procedures](./rollback-procedures.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)
