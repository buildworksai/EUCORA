# Ansible Connector Specification

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
AWX/Tower executes playbooks for Linux and other platforms; connector ensures idempotent playbooks, inventory management, and repo mirrors.
**Design Principle**: "Control Plane orchestrates deterministic, idempotent Ansible playbooks with correlation IDs; no hidden drift."

## Authentication & API
- **Endpoint**: `https://awx.example.com/api/v2/`
- **Auth**: OAuth token with scope to `job_templates`, `inventories`, `projects`; rotated every 30 days.
- **Token storage**: Azure Key Vault (per Secrets Management doc) and used via AWX credential objects.

## Playbook Execution Flow
1. Connector launches `POST /job_templates/<id>/launch/` with:
```json
{
  "extra_vars": {
    "correlation_id": "dp-20260104-0200",
    "artifact": "linux-app-v1.4",
    "target_inventory": "p1-site"
  }
}
```
2. Playbooks `package_install.yml` and `repo_sync.yml` are idempotent (`apt-get install -y`, `stat` checks) and reference `manifest.hash`.
3. AWX returns job `id`, state; success states include `successful`, failure states include `failed` and `errored` with `rc` codes.

## Inventory & Repo Mirror Configuration
- Inventories mapped to site-scope tags (acquisition, BU, site) determined by control plane.
- Repo mirrors configured via `scripts/repo-sync.yml`; mirror URIs recorded with `site_scope` and validated via `hash`.
- Offline mirrors use hashed artifacts; failure to match triggers `policy_violation` drift event.

## Error Handling & Idempotency
- **Transient**: HTTP 500, AWX job timeout (`rc=124`) → retried with exponential backoff; circuit breaker after 3 failures.
- **Permanent**: Job returned `rc=1` with `msg=package not found` → escalate to Packaging team, log event.
- **Policy violation**: Attempt to run job against unauthorized inventory or missing CAB approval → job blocked, event `error_class=policy_violation`.
- **Idempotency**: AWX job template ensures `creates:` or `register` conditions to avoid reinstallation; duplicate correlation id returns HTTP 409.

## Monitoring & Assurance
- Job stdout streamed to SIEM with JSON lines referencing `correlation_id`, `inventory`, `job_id`, `rc`.
- Scripts validate drift by comparing `status.managed` vs `manifest.hash`; mismatch triggers automated remediation via AWX job referencing `manifest.hash` (drift detection event type).
- Connector health check `scripts/ansible/health.py` pings AWX heartbeat endpoint; failure triggers alert and prevents new deployments.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)
- [Connector Rules](../../../.agents/rules/08-connector-rules.md)

---

**Ansible Connector Specification v1.0 — Design**
