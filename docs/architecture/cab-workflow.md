# CAB Workflow

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Define the CAB submission, review, and approval workflow that enforces evidence-first governance and deterministic risk scoring.
**Design Principle**: "Evidence-first governance with policy intents/evidence as the control plane system-of-record."

## Submission Flow
1. **Packaging Engineer** uploads artifact, SBOM, scan report, rollout + rollback plans, and automated test evidence to the artifact store (via `POST /artifacts`).
2. Risk Model service computes `risk_score` per `risk_model_v1.0` and records `normalized_factors`. The evidence pack payload includes field `risk_model_version` and `risk_score`.
3. Caller records `correlation_id` (e.g., `dp-20260104-00A1`) and POSTs to `POST /cab/submissions` with schema:
```json
{
  "correlation_id": "dp-20260104-00A1",
  "artifact_id": "win32-v2.4.1",
  "risk_score": 62,
  "inventory": {"hash": "sha256:..."},
  "evidence": {
    "sbom_uri": "https://...",
    "scan_result_id": "scan-20260104-01",
    "rollout_plan": "rings.json",
    "rollback_plan": "rollback.json"
  },
  "exceptions": []
}
```
4. System validates evidence completeness (hash presence, SBOM, scan result, test proof); failure returns HTTP 400 `EVIDENCE_INCOMPLETE` per Evidence Pack Rules.
5. If `risk_score > 50`, metadata flags `cab_gate=true` and resume only after CAB Approver sets `status=approved` in event store.

## CAB Review
- CAB Approvers have RBAC-scoped access (no publish rights) and consume evidence via `GET /cab/submissions/{correlation_id}`.
- Approval window: Standard (48h), Urgent (24h) with justification recorded in event store.
- Decisions log to append-only event store with JSON containing `status`, `approver_id`, `timestamp`, and `conditions`.
- Exceptions: require Security Reviewer approval, expiry date, compensating controls, and are logged with event `cab.exception.added`.

## Approval Mechanics
- Approval produces event `cab.approval` (HTTP 201) with `conditions` such as `rollback_validation=true`.
- Publishing beyond Ring 1 is blocked until `cab.approval` is recorded when `risk_score > 50` or privileged tooling.
- Ring 1 can progress after evidence completeness; CAB approval is optional for automated risk scores ≤ 50 but must still log decision.
- Scope change (cross-boundary) requires new submission with `scope_diff` summary and explicit CAB approval; API rejects otherwise (HTTP 409 `SCOPE_CHANGE_REQUIRED`).

## Exception & Expiry
- Exception record schema:
```json
{"exception_id":"exc-20260104-001","expires_on":"2026-02-15T00:00:00Z","compensating_controls":["enhanced monitoring"],"approver":"security@corp","status":"active"}
```
- Once expired, deployments referencing exception automatically fail until renewed.

## Audit & Retention
- All CAB interactions (submit/approve/deny/exception) include `correlation_id`, `actor`, `ip`, `event_type`, `event_status` (e.g., `approved`, `denied`) for SIEM ingestion.
- Retention: events stored 7 years minimum; archived to `audit/cab/` blob store.
- JSON logs forwarded to Azure Sentinel with `severity`, `component=cab`, and `correlation_id` fields.

## Failure Modes
| Failure | Impact | Mitigation |
|---|---|---|
| Evidence server unavailable | CAB submissions fail (HTTP 503) | Retry with exponential backoff; queue submissions with correlation id; alert CAB via Sentinel |
| CAB approver unavailable | Risk > 50 approvals stalled | Backup approver list; escalate via `PIM/JIT`; log event `cab.approval.pending` |
| Exception expiry unattended | Deployments fail | Automation re-notifies owner; re-open CAB window when necessary |

---

## Related Documentation
- [Architecture Overview v1.2](./architecture-overview.md)
- [Evidence Pack Rules](../../.agents/rules/10-evidence-pack-rules.md)
- [Ring Model](./ring-model.md)

---

**CAB Workflow v1.0 — Design**
