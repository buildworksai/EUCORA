# Connector Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Anchor connectors on idempotency, error classification, retries, throttling, and audit correlation.
**Design Principle**: "Idempotent connectors with correlation id audit trail."

## Rules
1. Use `correlation_id` as idempotent key for every publish/query/remediate call.
2. Errors must be classified: `transient` (retry with backoff), `permanent` (fail and surface to operator), `policy_violation` (CAB/Lifecycle issue).
3. Retry policy: exponential backoff (base 2s, max 60s) with circuit breaker after 3 consecutive retriable failures.
4. Respect `Retry-After` headers from APIs (Graph, Jamf, AWX). Persistent throttling increments must abort to avoid bans.
5. All connector operations must log correlation id + error classification to event store (JSON log format). Failures must map to HTTP status codes (e.g., 429 for throttling, 409 for conflict).

## Enforcement Examples
- ✅ Idempotent key usage: `POST /deviceAppManagement/msiDeployments` with header `Idempotency-Key: dp-20260104-0003` ensures safe retries.
- ✅ Error log entry example:
```
{"correlation_id":"dp-20260104-0003","connector":"Intune","error_class":"transient","status_code":429}
```
- ❌ Treating every failure as permanent without classification prevents proper retries and auditing.

## Related Documentation
- [Execution Plane Connectors](../docs/architecture/execution-plane-connectors.md)
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)

---

**Connector Rules v1.0 — Design**
