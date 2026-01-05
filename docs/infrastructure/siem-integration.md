# SIEM Integration
**Version**: 1.0
**Status**: Draft
**Last Updated**: 2026-01-05

---

## Overview
Defines how the Control Plane forwards structured telemetry, CAB approvals, and vault/audit events to the enterprise SIEM (Azure Sentinel or Splunk) to satisfy compliance, evidence, and security monitoring.

**Design Principle**: “Evidence-first governance” — every privileged action, CAB decision, or vault access produces a correlation-id-tagged event stored permanently in the SIEM.

---

## 1. SIEM Technology Stack
- **Primary platform**: Azure Sentinel (Log Analytics workspace) with secondary export to Splunk for compliance reporting.
- **Authentication**: Managed Identity or service principal with certificate (no hardcoded secrets). Sentinel workspace ID + shared key retrieved via `Get-ConfigValue` from `scripts/config/settings.json` or environment variables.
- **Endpoint**: `https://{workspace}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01` per Azure Log Analytics Data Collector API.
- **Log type**: `ControlPlaneEvents`; each log includes timestamp, level, message, correlation_id, component, metadata breakdown.

## 2. Log Sources & Formats
| Source | Logged Fields | Format/Transport |
|---|---|---|
| Control Plane API + workflow | correlation_id, event_type, actor, intent_id, success_rate, ring | `Write-StructuredLog` JSON → console + file + `Send-SIEMEvent` via REST |
| Connector operations | correlation_id, plane, action, status, error classification (transient/permanent/policy) | connectors call `Send-SIEMEvent` (via `Invoke-RetryWithBackoff`) with `component=connector` |
| CAB approvals | approval_id, approver, decision, conditions, expiry, evidence_pack_id | `Write-StructuredLog` invoked in CAB module; event stored in immutable event store, forwarded to SIEM |
| Vault access | secret_path, actor, action (get/list/rotate), outcome | vault audit logs streamed into SIEM; control-plane aggregator adds correlation_id |
| Security incidents (policy breach, drift) | type, severity, impacted scope | telemetry service posts via same pipeline with `level=Critical/High/Medium` |
| Failure/rotation events | failure code, remediation action, component | `Send-SIEMEvent` ensures correlation_id and metadata persisted

## 3. Severity Mapping & Alert Rules
| Event Level | SIEM Severity | Triggered Alert |
|---|---|---|
| Critical | `BreakGlass` | failover needed, new deployment blocked, CAB notified |
| High | `FailedPublish` | immediate incident response + review (P0/P1) |
| Medium | `CertificateExpiry` | watchlist (rotate within 72h) |
| Informational | `ApprovalGranted` | recorded for audit but no immediate action |
| Debug | `Operational` | optional, aggregated per component

Alert rules (measurable):
1. **Break-glass activation** (Critical) fires when vault break-glass path accessed or CAB denies high-risk publish; SLA: respond within 15 minutes.
2. **Publish failure** (High) triggers when connectors fail with policy violation code; automated rollback triggered if failure occurs in Ring 0/1.
3. **Certificate nearing expiry** (Medium) checks `cert.expiry_date - now <= 7 days`; rotation automation sequences run and log completion.
4. **Vault access anomaly** (High) when `AuditVolume` spikes > 2x baseline for 5 min; gating rule ensures connectors halt new publish.

## 4. Log Format & Correlation
- Logs are JSON with fields: `timestamp`, `level`, `message`, `correlation_id`, `component`, `metadata`. Example stored by `Write-StructuredLog` and forwarded by `Send-SIEMEvent`.
- Each log contains correlation_id from deployment intent (e.g., `dp-YYYYMMDD-xxxx`), enabling end-to-end traceability across Control Plane → connectors → CAB events.
- Audit trail export (via `Export-AuditTrail`) collects all events for a correlation id and exports JSON/CSV/HTML for CAB reviews.
- Validation rule: `LogRecord.correlation_id` must not be null; failure re-triggers log flush.

## 5. Retention & Reporting
- Log retention ≥ 2 years (per compliance), matching architecture doc and SIEM doc.
- Quarterly compliance reports (sent to CAB + security) summarize:
  - number of deployments (per ring) with correlation ids
  - evidence pack completeness rate
  - failure modes triggered and RTO/RPO results
- Reporting pipeline uses SIEM queries to compute success metrics aligning with `ring-model` thresholds.

## 6. Failures & Mitigation
| Failure | Impact | Mitigation |
|---|---|---|
| SIEM ingestion failure (workspace unreachable) | events not stored | Buffer logs locally (JSON files) and replay once SIEM available; gating rule prevents new publishes requiring audit evidence |
| Authentication failure (shared key missing/invalid) | `Send-SIEMEvent` fails | automation rotates key via Key Vault; connectors rethrow after 5 min while still logging locally |
| Alert rule flapping | false positives | tune thresholds (non-violation defined) and track via `AlertStability` metric; adjustments require CAB signoff |

## 7. Validation Rules
1. Every `Send-SIEMEvent` call must include `correlation_id` and `component`; missing fields trigger `policy violation` error and block export.
2. SIEM ingest success is required (`HTTP 200` + JSON `status = ok`); failures signaled to telemetry and requeued with `Invoke-RetryWithBackoff`.
3. Vault and CAB events cross-reference each other via correlation_id to ensure evidence completeness; compare counts weekly.

---

## Related Documentation
- [docs/architecture/architecture-overview.md](../architecture/architecture-overview.md)
- [docs/infrastructure/secrets-management.md](secrets-management.md)
- [docs/infrastructure/ha-dr-requirements.md](ha-dr-requirements.md)
- [.agents/rules/08-connector-rules.md](../../.agents/rules/08-connector-rules.md)
- [scripts/utilities/logging/Send-SIEMEvent.ps1](../../scripts/utilities/logging/Send-SIEMEvent.ps1)

---

**SIEM Integration v1.0 — Draft**
