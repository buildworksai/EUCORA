# Landscape Connector Specification

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Landscape manages Ubuntu packages and site mirrors; connector ensures signed APT repos, drift detection, and compliance reporting.
**Design Principle**: "Thin control plane delegates package enforcement to Landscape while maintaining idempotent connectors + audit trails."

## Authentication & API
- **API**: Landscape REST API via `https://landscape.example.com/api/1.0/` and CLI tooling for edge cases.
- **Auth**: Service account + API token stored in Azure Key Vault; token rotates every 30 days and logs to SIEM.
- **Permissions**: Token scoped to package uploads, schedule management, and compliance queries.

## Package Flow
1. Connector creates signed APT package and pushes metadata to Landscape via `POST /package/upload`.
2. Landscape verifies GPG signature (see Key Management doc); connector ensures `manifest.hash` recorded.
3. Compliance schedules defined per site class; connector configures jobs referencing `correlation_id` and site tags.
4. Response includes `task_id` and `status`; failure codes map to error classification.

## Drift Detection & Remediation
- Landscape inventory compared to desired package list every 15 minutes; mismatch emits `drift` event with `error_class=policy_violation`.
- Remediation triggered via Ansible playbook (see Ansible connector) referencing `manifest.hash`; event logged for audit.

## Offline Mirror Sync Procedures
- Site mirrors created per acquisition boundary; connector syncs via rsync over SSH with `hash-verification` step.
- Transfers include `correlation_id`, `site_scope`, `mirror_uri`; failure triggers `mirror.sync.fail` alert (High severity).
- Mirror signing keys stored offline; rotation uses offline script `scripts/mirror-key-rotate.sh` recorded in Evidence Pack.

## Error Classification
- `transient`: HTTP 503, SSH timeout, coverage job running (retry defined)
- `permanent`: invalid package signature, manifest mismatch
- `policy_violation`: unauthorized drift remediation attempt or missing CAB approval

## Monitoring & Validation
- Validate idempotency: repeated package push with same `correlation_id` results in HTTP 409 and no duplicate packages.
- Mirror sync job logs hashed file lists; script `python scripts/validate_mirror.py` ensures checksums match.
- Telemetry includes compliance score, drift events per site, mirror sync durations.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [Execution Plane Connectors](../../architecture/execution-plane-connectors.md)
- [Connector Rules](../../../.agents/rules/08-connector-rules.md)

---

**Landscape Connector Specification v1.0 — Design**
