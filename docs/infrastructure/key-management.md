# Key Management
**Version**: 1.0
**Status**: Draft
**Last Updated**: 2026-01-05

---

## Overview
Documents how code signing keys, certificates, and supporting PKI artifacts are generated, stored, rotated, and revoked for the Packaging & Publishing Factory and connectors. Key owners are accountable for integrity, and all use is tracked in the evidence store per the thin Control Plane principle.

**Design Principle**: "Separation of duties" — signing keys are owned and rotated separately from packaging/publishing roles, preventing escalation and enforcing governance.

---

## 1. Key Inventory & PKI Hierarchy
1. **Root CA** (offline/air-gapped) issues intermediate-level keys for signing pipelines; stored in HSM with access by the Security Reviewer.
2. **Intermediate CAs** create signing certificates for each platform pipeline:
   - **Windows Authenticode** (MSIX/Win32).
   - **macOS Developer ID Installer** (flat packages/PKG).
   - **APT repo signing (GPG)** for Linux packages.
3. **Connector certificates** for Intune Graph and other APIs (stored in vaults, renewed via automation).
4. **PKI ownership**: Security Reviewer is accountable for root/intermediate management; Packaging Engineers are responsible for daily usage but cannot export private key material.

### HSM Requirements
- All signing keys must reside in FIPS 140-2 Level 2 (minimum) certified HSMs (Azure Key Vault Managed HSM, AWS CloudHSM, or equivalent).
- HSM operations produce audit logs and require dual control for critical operations (generate, delete, export).
- Validation rule: `HSMAccessReviewFrequency = 90 days` and `HSMExportLock = True`.

## 2. Certificate Lifecycle (Generation → Rotation → Revocation)
- **Generation**: keys are generated via HSM APIs; script logs correlation id + fingerprint.
- **Storage**: private keys never leave the HSM; public certificates are published to the Control Plane configuration repository (read-only) and referenced by packaging pipelines.
- **Rotation**:
  - Signing certificates rotate every 90 days; automation uses `Invoke-RetryWithBackoff` to call HSM APIs, update pipeline config, and store new certificate metadata in the evidence store.
  - Connector certificates rotate every 60 days; automation pipeline ensures service principals use the new cert before revoking the old.
  - GPG keys for Linux rotate every 90 days with escrowed copies for disaster recovery.
  - Validation gate: `CertificateAgeDays < RotationInterval` before enabling new deployments.
- **Revocation**: on compromise or rotation, the revocation is published to the certificate revocation list (CRL) and the Control Plane marks dependent artifacts as `re-sign required`.

## 3. Key Ownership & Accountability
| Key Type | Owner | Responsibilities |
|---|---|---|
| Root + Intermediate CA | Security Reviewer (primary) | rotate keys (90-day cycle), manage HSM access, document break-glass events |
| Windows Authenticode | Packaging Engineer (with Security Reviewer oversight) | sign artifacts, record evidence, trigger rotation pipeline |
| macOS Developer ID | Packaging Engineer (Security Reviewer consult) | sign/notarize, ensure notarization metadata recorded |
| APT GPG keys | Linux packaging owner | sign repo, rotate, coordinate offline target mirrors |
| Connector certs (Intune, Jamf, SCCM) | Connector team lead | store credentials in vault, rotate (60-day) per automation |

Owners must log every signing request with correlation id + evidence pack entry. Break-glass rotation (e.g., urgent revoke) requires dual control: Security Reviewer + Platform Admin and triggers new evidence pack version.

## 4. Validation & Compliance Rules
1. Signing operation is blocked unless the certificate referenced in the evidence pack is in the vault and `Status = Active`.
2. Every artifact includes `signing.fingerprint` and `signing.certificate_issued` fields in the evidence pack schema (per `evidence-pack-schema.md`).
3. Rotation proof is recorded as `rotation_event` with correlation id, new certificate thumbprint, and verification results.
4. Revocation events log `revocation_reason` and `rotated_by` and require CAB approval for production re-signing.
5. Regular audits verify `KeyRotationLog` entries exist for each key over the last 90 days; missing logs trigger compliance failure.

## 5. Failure Modes & Mitigation
| Failure | Impact | Mitigation |
|---|---|---|
| HSM outage | Cannot sign artifacts | Pause packaging pipeline; switch to secondary HSM (preloaded) within 8 hours; `FailoverDrill` includes key sync checks |
| Key compromise | Risk to artifact integrity | Immediately rotate key, revoke old certificate, update evidence pack, notify CAB + SIEM |
| Rotation pipeline failure | Certificate expires | Automated alert (SIEM) triggers manual rotation within 24h; no production publish until new cert validated |
| Vault secret access failure | Connectors cannot authenticate | fallback to alternate vault endpoint (if available); gating rule prevents publish until `SecretAccess = Success` |

## 6. Recovery & Disaster Readiness
- Backup of certificate metadata stored separately from HSM; includes key owner, rotation history, evidence pack references.
- In DR scenario, the secondary HSM has pre-provisioned keys or uses escrowed copies sealed by Security Reviewer; replay evidence pack events before enabling new deployments.

---

## Related Documentation
- [docs/architecture/architecture-overview.md](../architecture/architecture-overview.md)
- [docs/infrastructure/ha-dr-requirements.md](ha-dr-requirements.md)
- [docs/infrastructure/secrets-management.md](secrets-management.md)
- [docs/architecture/risk-model.md](../architecture/risk-model.md)
- [docs/architecture/evidence-pack-schema.md](../architecture/evidence-pack-schema.md)

---

**Key Management v1.0 — Draft**
