# Control Plane Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Explicit control-plane boundaries: no direct endpoint touches, deterministic orchestration, correlation-id discipline.
**Design Principle**: "Thin control plane (policy, risk, approvals, orchestration, evidence) only."

## Rules
1. API Gateway must authenticate via Entra ID app registration (client certificate, `clientCredential` flow) and issue scoped tokens to downstream services.
2. Policy Engine evaluates entitlements → risk → approval gating before orchestrator schedules Deployment Intents.
3. Orchestrator acts as state machine; transitions are append-only events stored with correlation id and timestamp.
4. Event Store must be immutable; no event may be updated—only new events appended (use Postgres append table or event store with write-once policy).
5. Connectors talk only to Intune/Jamf/SCCM/Landscape/Ansible APIs; no direct endpoint agent channels exist in Phase 0–2.
6. Every deployment event must include a correlation id (e.g., `dp-20260104-0002`) and error classification (transient/permanent/policy_violation).

## Enforcement Examples
- ✅ Entra ID client cert authentication: `POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token` with `grant_type=client_credentials` and `scope=https://graph.microsoft.com/.default`.
- ❌ Embedding endpoint SSH or WinRM credentials in Control Plane—violates no-direct-endpoint rule.
- ✅ Event emission example snippet (Python):
```
emit_event({
  "correlation_id": "dp-20260104-0002",
  "type": "deployment_intent.created",
  "status": "pending",
  "error_class": null
})
```

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [Execution Plane Connectors](../docs/architecture/execution-plane-connectors.md)

---

**Control Plane Rules v1.0 — Design**
