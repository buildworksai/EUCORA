# CAB Submission Runbook

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Step-by-step instructions for preparing evidence packs, submitting to CAB, and handling approvals/exceptions.
**Design Principle**: "Evidence-first governance with deterministic submissions and immutable audit logs."

## Preparation Checklist
1. Confirm artifact metadata, SBOM, and scan results (Trivy/Grype/Snyk) exist with pass/fail status.
2. Validate test evidence (automated lab install/rollback logs) shows ≥98% Ring 0 success.
3. Ensure rollback plan is documented per plane (Intune/SCCM/…) and includes correlation id.
4. Document exceptions (if any) with expiry dates, compensating controls, Security Reviewer approval.
5. Compute `risk_score` using `risk_model_v1.0`; include normalized factors in payload.

## Submission Workflow
1. Use CLI/API `POST /cab/submissions` with JSON payload (see CAB Workflow doc). Include `correlation_id`, `risk_score`, `evidence_pack_uri`, `exceptions`.
2. Validation runs; HTTP 400 `EVIDENCE_INCOMPLETE` means fix missing `sbom_uri` or `scan_result_id`.
3. Upon success, event stored (`cab.submission.created`). If `risk_score > 50`, set `cab_gate=true`; Promotion beyond Ring 1 waits for `cab.approval`.
4. CAB review: Approver retrieves via `GET /cab/submissions/{id}`; time windows: standard 48h, urgent 24h.
5. Decision logged with `event_type=cab.approval`. Approval includes `conditions` (e.g., `rollback_validation=true`).

## Exception Handling
- Submit exception payloads with `expiry` (max 90 days) and `compensating_controls` (monitoring, limited scope).
- Security Reviewer must approve exception; record event `cab.exception.approved` with `correlation_id`.
- Automated enforcement rejects deployments referencing expired exceptions (HTTP 403 `exception_expired`).

## Notifications & Continuity
- Notifications: on submission, CAB, exception, and approval events publish to SIEM + Slack channel `#cab-approvals`.
- Keep evidence pack accessible; update `docs/architecture/evidence-pack-schema.md` for schema changes.
- Maintain cross-reference list of submission IDs per application for audits.

## Related Documentation
- [CAB Workflow](../architecture/cab-workflow.md)
- [Evidence Pack Rules](../../.agents/rules/10-evidence-pack-rules.md)
- [Incident Response Runbook](./incident-response.md)

---

**CAB Submission Runbook v1.0 — Design**
