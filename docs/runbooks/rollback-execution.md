# Rollback Execution Runbook

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Procedures for triggering and monitoring rollback per execution plane, ensuring SLA ≤4h for P0/P1.
**Design Principle**: "Each rollback is plane-specific, idempotent, and tied to a correlation id/event for audit."

## Pre-Rollback Validation
- Rollback must be validated in Ring 0 (lab automation) with documented success rates; update evidence pack with `rollback_validation=true` before Ring 1 promotion.
- Validator script `python scripts/rollback/validator.py --plane intune --artifact win32-v3.5` ensures detection and uninstall commands succeed.

## Rollback Steps by Plane
1. **Intune**: Supersedence via `POST /deviceAppManagement/mobileApps/{id}/assignments`; targeted uninstall script; ensure telemetry success rate logs `status_code=200`.
2. **SCCM**: Deploy rollback package to DP + collection. Use `New-CMRollbackDeployment -PackageID <id>` and monitor status via `Get-CMDeploymentStatus`. Ensure event logs include `dp-...` correlation id.
3. **Jamf**: Update policy to previous version; use `POST /JSSResource/policies/id/{id}` with `priority=100` and log `rollback_job` status.
4. **Landscape/Linux**: `apt pin` previous version and run Ansible remediation playbook; verify state via `landscape.manifest` diff.
5. **Mobile**: Reassign previous tracked version via Intune for MDM (iOS) or Managed Google Play track for Android; if prior version unavailable, remove app and plan manual re-install.

## Execution Workflow
- Only Publisher or Endpoint Ops triggers rollback; each request includes `correlation_id`, `rollback_plan_id`, `trigger_reason`.
- Connector call returns HTTP status (200 success, 409 conflict, 422 invalid state) and `error_class`.
- Log event in append-only store with `event_type=rollback.executed`, success/failure, SLA duration.

## Monitoring & Communication
- Rollback telemetry tracked (success rate and time-to-compliance) and shared every 15 minutes; use `dashboards/rollback-progress`.
- If rollback exceeds ≤4h SLA for P0/P1, auto-escalate to CAB and update incident ticket.

## Post-Rollback Actions
- Update evidence pack with rollback outcomes and attach log files.
- Document root cause in `reports/rollback/post.md` and share with CAB.

## Related Documentation
- [Incident Response Runbook](./incident-response.md)
- [Ring Model](../architecture/ring-model.md)
- [Rollback Rules](../../.agents/rules/07-rollback-rules.md)

---

**Rollback Execution Runbook v1.0 — Design**
