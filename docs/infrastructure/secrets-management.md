# Secrets Management
**Version**: 1.0
**Status**: Draft
**Last Updated**: 2026-01-05

---

## Overview
Defines how the Control Plane and connector services securely store and rotate credentials, certificates, and API tokens. Secrets are never hardcoded, always retrieved via vaults (Azure Key Vault, HashiCorp Vault, or equivalent) with enforced RBAC and audit logging.

**Design Principle**: "Evidence-first governance" — every privileged action (including secrets usage) has an immutable audit trail tied to correlation IDs.

---

## 1. Vault Technology & Architecture
1. **Primary vault**: Azure Key Vault (or HashiCorp Vault Enterprise) in each region with soft-delete + purge protection enabled.
2. **Replication**: Vaults replicate secrets to a secondary region; replication lag must be ≤ 5 minutes (validation rule: `VaultReplicationLagMinutes <= 5`).
3. **Access model**: Control Plane services authenticate via Managed Identities (preferred) and request secrets from vault. Connectors use service principals with certificate-based auth or managed identity.
4. **Secret scope**: secrets are grouped per subsystem (Control Plane, Packaging Factory, Connectors, CAB) and accessed via policy-managed paths.
5. **Auditing**: every vault access generates an audit record streamed to SIEM (see `siem-integration.md`) with correlation id, requestor, operation, and outcome.
6. **Failure tolerance**: multi-region failover uses fallback vault (read-only) until replication catches up; validation rule ensures `FallbackVaultSynced = True` before permitting writes.

## 2. Credential + Key Types
- **Control Plane service principals** (API gateway, orchestrator, policy engine) use certificate-based authentication stored as Key Vault secrets.
- **Connector credentials**:
  - Intune (Graph API) uses Entra ID app registration cert + optional client secret with rotation.
  - Jamf uses OAuth client creds stored as Key Vault secrets.
  - SCCM uses service account credentials with constrained delegation, stored in vault and consumed by connectors via Managed Identity.
  - Landscape/Ansible use API tokens/cert secrets.
- **Signing keys** (Windows Authenticode, macOS Developer ID, APT GPG) are stored inside Hardware Security Modules (HSM) or vendor-managed Key Vault with `FIPS 140-2 Level 2` compliance.
- **Secrets for scanning tools** stored per tool (Trivy/Grype/Snyk) as read-only tokens; pipeline agents access them via vault.

## 3. Access Policies & Separation of Duties
- Platform Admin group retains vault write access for key rotation + break-glass; Packaging/Connector roles have read-only access to required secrets.
- **SoD enforcement**: packaging pipelines may read signing keys but cannot access production publish credentials (governed via `rbac-configuration` doc). Publishers have separate vault policies for execution plane publish secrets.
- Access policies include:
  - `project/control-plane/*` path for core secrets (platform vault RBAC: Control Plane service principals only)
  - `project/connectors/intune/*`, `.../jamf/*`, etc., each with scoped service principals or Managed Identities.
- **Break-glass**: limited `EmergencyAccess` secret path requiring dual control (two approvers) and immediate rotation after use.
- **Validation**: monthly `VaultAccessReview` ensures least privilege (per CLAUDE requirement for quarterly access reviews).

## 4. Rotation Policies (Measurable)
| Secret Type | Rotation Interval | Metric/Validation |
|---|---|---|
| Service principal certificates | 90 days | `CertificateAgeDays <= 90` before renewal completes |
| API tokens (e.g., Jamf, Landscape) | 60 days | rotation automation triggered via pipeline; `TokenExpiryAlarm` triggers 7 days prior |
| Signing keys in HSM | 90 days (per key owner) | `SigningKeyRotationComplete = True` recorded in evidence pack |
| SIEM/telemetry secrets | 30 days | `SIEMSecretExpiryDays <= 30` before rotation |
| Vault root/admin keys | 30 days | rotation executed via break-glass audit event |

Rotation process:
1. Automated job acquires new secret, stores it in vault under versioned path, updates target resource via configuration pipeline, and records rotation event with correlation id.
2. Old secrets remain in vault for 7 days (audit hold) before scheduled purge; rotation job verifies `SecretVersionActive` before enabling dependent services.
3. Validation gate enforces `RotationDocumented = True` before pipeline resumes.

## 5. Audit Logging & Compliance
- Vault audit logs stream to SIEM with status (success/failure) and correlation id.
- Every privileged operation (signing requests, connector publish) logs both the credential used and the resulting event; `Write-StructuredLog` helper ensures JSON output with `correlation_id`.
- Vault log retention: minimum 2 years in SIEM (`siem-integration` retention policy is 2 years). Evidence pack includes rotation proof for CAB review.

## 6. Failure Modes & Mitigation
| Failure | Impact | Mitigation |
|---|---|---|
| Vault service unavailable | Secrets cannot be retrieved | Use cached secret (when allowed) with TTL ≤ 5 minutes; fallback to secondary vault; block publishes requiring new secrets |
| Secret corruption or unauthorized access detected | Compliance violation | Rotate secret immediately; invoke break-glass, issue new secrets, notify CAB/security |
| HSM outage (signing keys) | Cannot sign artifacts | Pause packaging pipeline; failover to secondary HSM key with `SigningOwnerApproval` and new evidence pack |
| Rotation job failure | Secret expires | Retry job with exponential backoff (per `Invoke-RetryWithBackoff`); if not resolved within 24h, escalate to CAB |

## 7. Validation Rules
1. Secrets are only consumed when `SecretMetadata` indicates `Status = Active` (prevents using expired rotations).
2. Any attempt to access `vault/*` outside defined RBAC results in SIEM alert (per architecture logging requirements).
3. Vault audit event must include correlation id (per CLAUDE: correlation IDs everywhere). Failure to log triggers gating check `AuditEventCount == expected`.
4. Break-glass usage requires dual approval record stored in event store before secret is used.

---

## Related Documentation
- [docs/architecture/architecture-overview.md](../architecture/architecture-overview.md)
- [docs/infrastructure/rbac-configuration.md](rbac-configuration.md)
- [docs/infrastructure/ha-dr-requirements.md](ha-dr-requirements.md)
- [docs/infrastructure/siem-integration.md](siem-integration.md)
- [.agents/rules/09-rbac-enforcement-rules.md](../../.agents/rules/09-rbac-enforcement-rules.md)

---

**Secrets Management v1.0 — Draft**
