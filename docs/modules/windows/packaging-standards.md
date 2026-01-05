# Windows Packaging Standards

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Define Windows packaging best practices aligned with the thin control plane and evidence-first governance.
**Design Principle**: "The Control Plane decides policy intent while packaging produces deterministic, signed artifacts ready for Intune/SCCM execution."

## Artifact Types & Format
- **Preferred**: MSIX for modern applications; produce signed `appx` bundles with manifest declarations.
- **Fallback**: Win32 `.intunewin` wrapping MSI/EXE/unpackaged binaries.
- **Metadata**: each artifact must include JSON manifest (`manifest.json`) containing `hashes`, `version`, `platform`, `installer_type`, and `detection_rules.`

## Installation Requirements
- Use silent switches (`/qn` for MSI, `/S` or vendor-specific) documented in manifest.
- Detection rules must include file (`%ProgramFiles%\App\app.exe`), registry (`HKLM\Software\Apps\App`, `DisplayVersion`), or product code GUID.
- Exit code mapping: `0=success`, `3010=success_reboot`, `1641/3010=reboot_required`, `1603=failure`, `1618=conflict`, `1940=security` (documented per app). Store mapping in evidence packs.

## Signing & Provenance
- Authenticode signing via enterprise cert stored in Azure Key Vault HSM (FIPS 140-2 Level 2).
- Notarized metadata recorded for MSIX packages and included in evidence pack (`signing_subject`, `timestamp_url`).
- Versioned provenance record stored in artifact store, referencing pipeline run id, builder identity, and SBOM location.

## Offline Support
- For constrained/offline Windows sites, package is distributed via SCCM DP; Control Plane ensures DP distribution job has `target_scope` and `correlation_id` recorded.
- Intune remains compliance plane; offline retrieval rely on SCCM DP caches with `Delivery Optimization` for partial scenarios.

## Validation Rules
- Preflight command: `signtool verify /pa <artifact>` ensures signature is valid and trusted.
- `Manifest validator` script ensures detection rules exist and `hashes.sha256` matches built binary.
- Evidence pack includes test logs (Ring 0 install/uninstall) with success rate ≥98% before promotion.

## Related Documentation
- [Architecture Overview v1.2](../../architecture/architecture-overview.md)
- [Ring Model](../../architecture/ring-model.md)
- [Windows Connector Rules](../../.agents/rules/08-connector-rules.md)

---

**Windows Packaging Standards v1.0 — Design**

## Testing & Evidence
- Automated install/uninstall tests run via PowerShell: `Invoke-Pester -Script .\tests\install.Tests.ps1` with success defined as expected exit code (≤1) and detection rule satisfied.
- Test evidence includes logging outputs, detection rule validation, and `rollback_validation=passed` flag; stored in evidence pack.

## Retention & Audit
- Artifact retention: keep latest **3 releases** or **90 days**, whichever longer; older packages archived and referenced in evidence pack.
- Audit log entry example: `{"correlation_id":"dp-20260104-00W1","component":"packaging","artifact":"win32-v3.5","status":"signed"}` stored in append-only event store.
