# Jamf Pro Connector Error Handling

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

This document defines **error classification** and **retry logic** for the Jamf Pro connector.

---

## Error Classification

### Transient Errors

**Examples**:
- HTTP 429 (Rate Limiting)
- HTTP 503 (Service Unavailable)
- Network timeouts
- API temporary unavailability

**Handling**: Exponential backoff retry (max 5 attempts)

### Permanent Errors

**Examples**:
- HTTP 400 (Bad Request)
- HTTP 401 (Unauthorized)
- HTTP 403 (Forbidden)
- HTTP 404 (Not Found)

**Handling**: No retry, log error, notify

### Policy Violations

**Examples**:
- Scope validation failures
- RBAC permission violations

**Handling**: No retry, log, notify, block deployment

---

## Retry Logic

- **Backoff**: Exponential (1s, 2s, 4s, 8s, 16s)
- **Max Retries**: 5
- **Idempotent Keys**: All operations use idempotent keys

---

## References

- [Jamf Connector Spec](./connector-spec.md)
- [Rollback Procedures](./rollback-procedures.md)

