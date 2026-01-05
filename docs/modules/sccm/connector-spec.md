# SCCM Connector Specification

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
SCCM serves as the authoritative distribution channel for constrained/offline Windows sites while Intune remains the compliance plane.
**Design Principle**: "Control Plane orchestrates – SCCM executes distribution; co-management alignment ensures idle connectors remain idempotent."

## Authentication & Environment
- **API**: `https://<sccm-site>/sms_mp/.sms_aut?mplist=` for REST calls; PowerShell remoting via `New-CimSession` for server operations.
- **Auth**: Service account w/ constrained delegation; credentials retrieved from Azure Key Vault and rotated every 60 days.
- **SoD**: No shared credentials; service account scoped to SCCM site, logging `actor=control-plane-sccm`.

## Publishing Flow
1. Control Plane emits deployment intent w/ `correlation_id` + `site_scope` tags.
2. Connector creates SCCM package + program via PowerShell script:
```
$package = New-CMPackage -Name "Win32-App" -Version "v3.5" -SourcePath "\\fileserver\packages\win32";
New-CMProgram -PackageId $package.PackageID -CommandLine "Setup.exe /S" -InstallBehaviour InstallForSystem;
```
3. Package distributed to Distribution Points (DPs) aligned to `site_scope` collections; Intune assignment triggers SCCM DP content distribution.
4. Response returns HTTP 200 and `status_code` (0=success, 1603=failure) mapped to error classification.

## Co-Management & Scope Controls
- `site_scope` derived from Entra ID group by acquisition/regional tag; connectors ensure SCCM collection membership matches.
- Control Plane enforces `target_scope ⊆ publisher_scope` before issuing command; violation returns HTTP 403 `policy_violation`.
- Collections and DPs remuneration logged in event store with `collection_id` and `dp_ids` for audit.

## Rollback Strategy
- Rollback package created per version; connectors publish via `New-CMRollbackDeployment` referencing stored `correlation_id`.
- Rollback SLA <=4h for P0/P1; orchestrator monitors status and escalates to CAB if not completed.

## Error Handling
| HTTP/Exit | Error Class | Notes |
|---|---|---|
| 429/503 | `transient` | Retry w/ exponential backoff (2s base, 2^n) then circuit breaker.
| 409 | `permanent` | Duplicate collection; manual reconciliation required.
| 1603 | `permanent` | MSI error, log `error_code=1603` and fail deployment.
| 403 | `policy_violation` | Scope mismatch or missing CAB approval; reject and alert.

## Validation & Monitoring
- Idempotency enforced: duplicate `correlation_id` attempt returns HTTP 409 with `error_class=permanent` and no additional DPs.
- Connector tests ensure DP distribution uses `dp_hash` and verifies content via hash check (SHA-256).
- Telemetry includes success rate, average DP distribution time, error breakdown; logged to SIEM (see doc).

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)
- [Connector Rules](../../../.agents/rules/08-connector-rules.md)

---

**SCCM Connector Specification v1.0 — Design**
