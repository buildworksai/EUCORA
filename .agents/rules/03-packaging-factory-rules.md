# Packaging Factory Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Enforce supply-chain controls (SBOM, scans, signing, provenance, immutability) inside the Packaging & Publishing Factory.
**Design Principle**: "Packaging ≠ Publishing ≠ Approval, evidence-first governance."

## Rules
1. SBOM generation is mandatory for every artifact (SPDX or CycloneDX). Store SBOM with artifact metadata in object store.
2. Vulnerability scan gate: block Critical/High findings unless Security Reviewer approves exception (expiry + compensating controls).
3. Signing requirements: Windows Authenticode, macOS notarized PKG (Developer ID Installer), Linux APT repo GPG keys.
4. Provenance metadata must include builder identity, pipeline run ID, inputs list, timestamps, and hashes.
5. Artifact immutability: once a release is published, underlying binaries/hashes cannot change—version new artifacts instead.

## Enforcement Examples
- ✅ Scan command example: `trivy fs --security-checks vuln --severity HIGH,CRITICAL ./artifacts/Win32`. Block publish unless exit code `0` or approved exception stored.
- ✅ Signing command example: `signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 releasein`. Include `NoRemove=1` logic in evidence pack if removing not allowed.
- ❌ Re-uploading same artifact with new hash to fix vulnerabilities violates immutability—publish new version.

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [Infrastructure Secrets Management](../docs/infrastructure/secrets-management.md)

---

**Packaging Factory Rules v1.0 — Design**
