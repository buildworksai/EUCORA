# Incident Response Runbook

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Define P0–P3 incident handling, rollback triggers, and CAB/responsibility coordination.
**Design Principle**: "Deterministic response with CAB-ready evidence, idempotent rollback, and offline-aware operations."

## Incident Classification
- **P0/P1**: Control Plane outage, evidence store down, failed deployment with immediate security impact. Trigger halt on deployments, notify CAB, start rollback (≤4h SLA).
- **P2**: Ring 1/2 partially failing (<99% success) or high failure rate. Pause promotions, investigate, remediate, may roll back depending on root cause.
- **P3**: Non-critical drift or minor telemetry alert; monitor, collect logs, plan maintenance.

## Response Steps
1. **Detect**: Alert triggered via SIEM (Critical/High). Include `correlation_id`, `component`, `error_class`.
2. **Triage**: On-call SRE assesses severity, updates incident ticket with `risk_score`, `ring`, `scope`, `site_class`.
3. **Contain**: For P0/P1, pause new deployments (circuit breaker). If evidence store down, publishes return HTTP 503.
4. **Notify**: Notify CAB + Platform Admin; escalate to Security Reviewer if compromised secrets.
5. **Rollback**: Trigger rollback-runbook (see `rollback-execution.md`) with correlation id; ensure rollback tests executed in Ring 0 before P1 rollback launch.
6. **Communicate**: Publish status board update every 30 minutes; include telemetry (time-to-compliance, rollback success, error codes).
7. **Post-Mortem**: Within 24h capture evidence pack, SIEM logs, lessons learned; update `reports/incidents/incident-<id>.md`.

## Rollback SLA & Criteria
- P0/P1 rollback must complete ≤4h; orchestrator monitors job state and raises CAB alert if exceeded.
- Rollback executed by Publisher/Endpoint Ops only; evidence pack includes `rollback_job_id` and stage.

## Post-Incident Actions
- Update `docs/architecture/ring-model.md` (if gates need adjusting) and `docs/runbooks/cab-submission.md` if evidence pack lacked fields.
- Review `todo` in `reports/incident-review.md` for follow-ups (CAB approval, additional testing).

## Related Documentation
- [Ring Model](../architecture/ring-model.md)
- [Rollback Runbook](./rollback-execution.md)
- [CAB Submission](./cab-submission.md)

---

**Incident Response Runbook v1.0 — Design**
