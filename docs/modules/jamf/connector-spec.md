# Jamf Connector Specification

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Specifies how the Control Plane integrates with Jamf Pro as a secondary execution plane for macOS deployments.
**Design Principle**: "Thin control plane relies on deterministic connectors with correlation-id discipline; Jamf only executes what the control plane authorizes."

## Authentication & Permissions
- **Endpoint**: `https://<jamf-domain>/JSSResource/`
- **Auth**: OAuth client credentials; credentials stored in Azure Key Vault and rotated every 30 days; tokens scoped to `policies`, `packages`, `distributionPoints`, `smartGroups`.
- **Service Account**: Restricted role (no API calls outside deployment flows); CAB approval required before privilege elevation (PIM session tracked).

## Publishing Flow
1. Control Plane issues `POST /publish` with body:
```json
{
  "correlation_id": "dp-20260104-0100",
  "artifact": "macos-app-v3.2",
  "policy_id": 123,
  "smart_group_id": 456,
  "ring": "Pilot"
}
```
2. Connector uploads pkg via `POST /packages/id/0` and updates policy via `POST /JSSResource/policies/id/123/revisions/next`.
3. Policy payload includes `priority` (used for rollback pinning) and `category` tags (`control-plane-auto`).
4. Response must return HTTP 201 with `status_line` and `error_class`. Duplicate `correlation_id` returns HTTP 409 (idempotent).

## Rollback Handling
- Version pin stored in policy notes; rollback triggered by `POST /JSSResource/policies/id/{id}` with `revert_to` payload.
- Connector logs `error_class` for rollback failures (`policy_violation` if CAB gate missing).
- Rollback runs validated in Ring 0 before Ring 1 promotion.

## Error Classification
- **429/503**: `transient` → retry w/ exponential backoff (2s base, max 60s) as per Connector Rules.
- **409**: `permanent` (conflict/duplicate) → surface to operator.
- **403**: `policy_violation` (scope mismatch or missing CAB approval).
- **400**: `permanent` with code `JAMF_INVALID_PAYLOAD`; validate JSON schema before call.

## Failure Modes & Mitigation
| Failure | Impact | Mitigation |
|---|---|---|
| Jamf API rate limit | Publish/rollback delayed | Respect `Retry-After`; circuit breaker after 3 retries; log alert to SIEM (severity=High) |
| Token expired | Auth fails (401) | Connector refreshes token via vault before retry; emit event `connector.auth.refresh` |
| Distribution point missing | Policy assignment fails | Trigger remediation workflow to create DP and re-run publish; log event `connector.jamf.dp_missing` |

## Monitoring & Assertions
- Every publish/query/remediate logs `correlation_id`, HTTP status, `error_class`, and Jamf IDs to event store (Audit doc).
- Idempotency test ensures repeated `correlation_id` returns HTTP 409 and no duplicate policy revisions.
- Telemetry records success rate and time-to-compliance every 5 minutes.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)
- [Connector Rules](../../../.agents/rules/08-connector-rules.md)

---

**Jamf Connector Specification v1.0 — Design**
