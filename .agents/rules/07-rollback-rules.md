# Rollback Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Define rollback validation, plane strategies, SLAs, execution workflow, and version retention.
**Design Principle**: "Rollback validation before promotion; rollback execution is plane-specific and auditable."

## Rules
1. Rollback validation must run in Ring 0 before any promotion to Ring 1 (recorded event `rollback.validation.complete`).
2. Plane-specific rollback strategies: Intune (supersedence, uninstall scripts), Jamf (policy pinning), SCCM (rollback packages + collections), Linux (apt pinning), Mobile (assignment/remove with track control).
3. Rollback SLA: ≤4 hours for P0/P1 incidents; orchestrator must monitor and escalate to CAB if not met.
4. Rollback execution workflow: only Publisher or designated Endpoint Ops can trigger; all triggers emit correlation id and error classification.
5. Version retention policy: retain prior 2 releases or 90 days (whichever longer) to support rollback.

## Enforcement Examples
- ✅ Rollback command snippet: `POST /rollback/execute` → body includes `correlation_id`, `plane=Intune`, `target_version=1.3.2`, `approved=true`.
- ✅ Rollback audit event: `{"event":"rollback.executed","status":"success","sla_ms":3600000}`.
- ❌ Allowing developer to trigger rollback without Publisher/Endpoint Ops scope violates SoD.

## Related Documentation
- [Control Plane Design](../docs/architecture/control-plane-design.md)
- [Rollout Rules](../docs/architecture/ring-model.md)

---

**Rollback Rules v1.0 — Design**
