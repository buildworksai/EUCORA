# Execution Plane Connectors

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Document integration patterns, idempotency, error classification, and audit trail expectations for Intune, Jamf, SCCM, Landscape, and Ansible connectors.
**Design Principle**: "Thin Control Plane relies on deterministic connectors with correlation-id discipline."

## Common Integration Pattern
1. **Publish**: Control Plane calls connector `POST /publish` with body `{correlation_id, artifact_id, ring, scope}`.
2. **Query**: Connectors expose `GET /status/{correlation_id}` to fetch install telemetry/status.
3. **Remediate**: `POST /remediate` triggers rollback/uninstall with idempotent semantics.
4. **Idempotency key**: connectors require `Idempotency-Key` header equal to `correlation_id` (per Connector Rules).
5. **Error classification**: connectors respond with `{status_code, error_class}` where `error_class` is `transient`/`permanent`/`policy_violation`.
6. **Audit**: every request logs `correlation_id`, `component`, HTTP status, and error classification to event store for SIEM ingestion.

## Intune Connector
- **API**: Microsoft Graph (`https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps`).
- **Auth**: Entra ID app registration with certificate credential, `clientCredentials` flow, scope `https://graph.microsoft.com/.default`.
- **Publish**: create `win32LobApp` or `msiPackage`; assignment via `mobileAppAssignments` referencing `deploymentIntent.cohort_group_id`.
- **Error handling**: map 429 → `transient` (retry after header), 409 → `permanent` (conflict), 400 → `policy_violation` (scope violation).
- **Rollback**: deploy supersedence policy or targeted uninstall script; track version pin via `intune.package.version`. Response includes `status_code` (e.g., 201 success, 409 conflict) and `error_class`.
- **Throttling**: respect `Retry-After` header; circuit breaker trips after 3 consecutive 503 responses.

## Jamf Connector
- **API**: Jamf Pro REST API with OAuth/client credentials; use endpoints `POST /JSSResource/packages/id/{id}` and `POST /JSSResource/policies/id/{id}/revisions/next`.
- **Idempotency**: correlation id stored in policy notes; duplicate requests return HTTP 409 with message `Duplicate policy revision`.
- **Rollback**: snapshot policy pinning (set `priority=100`), targeted script to uninstall; connectors keep track of `jamf.version` metadata.
- **Error codes**: 423 (resource locked) treated as `transient`, 404 as `permanent`, 403 as `policy_violation` (scope/budget issue).

## SCCM Connector
- **Integration**: PowerShell + REST provider (`https://{sccm-site}/sms_mp`).
- **Auth**: service account with constrained delegation; vault fetch via Azure Key Vault.
- **Content flow**: package creation → DP distribution → membership evaluation for site-scoped collections.
- **Co-management**: control plane maintains `site_scope` groups; connectors populate SCCM collections referencing those groups for offline sites.
- **Rollback**: SCCM rollback package and collection; event store logs `rollback_package_id`, `collection_id`, `status_code` (e.g., 200 success, 503 unavailable).
- **Error classification**: 503/reserve as `transient`, 409 (collection conflict) as `permanent`, 403 (SoD violation) as `policy_violation`.

## Landscape Connector
- **API**: Landscape API + CLI; uses service account + API token stored in vault.
- **Tasks**: manage signed APT repo, schedule package updates, report compliance states.
- **Drift detection**: compare desired package version with `landscape.manifest`; emit drift event if mismatch, with `error_class=policy_violation` when unauthorized change detected.
- **Offline mirrors**: connectors sync site-local mirrors via secure transport; maintain `manifest.hash` for verification.
- **Retry**: use exponential backoff; treat network timeouts as `transient` (retry up to 5 times), `certificate mismatch` as `permanent`.

## Ansible Connector
- **API**: AWX/Tower REST API (`/api/v2/job_templates/{id}/launch/`) with OAuth/token.
- **Playbooks**: use idempotent `package_install.yml` and `repo_sync.yml`; each launch annotated with correlation id.
- **Inventory targeting**: uses device tags from Control Plane; connectors map to AWX inventories.
- **Error handling**: job failures emit `error_class=transient` (retries for `ansible-runner` codes 4,5) or `policy_violation` (configuration drift/locked state) depending on `rc`.
- **Logging**: job stdout forwarded to SIEM with JSON lines containing `correlation_id`, `status`, `rc`, `event_type`.

## Common Patterns
- **Correlation IDs**: reused across connectors/events (e.g., publish, rollback, drift) to maintain traceability.
- **Idempotency enforcement**: connectors store last successful `correlation_id` per artifact; duplicate requests return HTTP 409 and avoid reprocessing.
- **Error classification table**:
  - `transient`: HTTP 429/503/504, network timeouts, temporary rate limits
  - `permanent`: 400/404/409 conflict, schema mismatch, resource deleted
  - `policy_violation`: 403, scope mismatch, unauthorized device, missing CAB approval
- **Audit logging**: all responses include `status_code` + `error_class` fields logged to Azure Sentinel (see SIEM doc).

## Validation Rules
- Connector integration tests assert idempotency by issuing same `correlation_id` twice and expecting HTTP 409 + no duplicate deployments.
- Preflight script `scripts/connector_health_check.sh` validates each connector's `heartbeat_endpoint` before enabling new deployments.
- All connectors must emit telemetry for success rate, time-to-compliance, and failure classification at least every 5 minutes.

---

## Related Documentation
- [Architecture Overview v1.2](./architecture-overview.md)
- [Connector Rules](../../.agents/rules/08-connector-rules.md)
- [Ring Model](./ring-model.md)

---

**Execution Plane Connectors v1.0 — Design**
