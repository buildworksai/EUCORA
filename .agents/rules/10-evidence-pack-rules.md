# Evidence Pack Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Define validation, immutability, versioning, retention, and completeness for CAB evidence packs.
**Design Principle**: "Evidence-first governance with deterministic CAB submissions."

## Rules
1. Required fields: artifact hashes, SBOM (SPDX/CycloneDX), vulnerability scan results, rollout plan, rollback plan, automated test evidence, exception records with expiry.
2. Immutability: store packs in WORM object storage (e.g., Azure Blob immutable storage) and prevent in-place edits; new versions require new event records.
3. Versioned schema (v1.0, v1.1, etc.) tracked in metadata; validation rejects file if schema mismatch.
4. Retention policy: 7 years minimum or per compliance requirement (whichever is longer).
5. Completeness check executed before CAB submission; failure returns HTTP 400 with code `EVIDENCE_INCOMPLETE`.

## Enforcement Examples
- ✅ Validation rule example: `SELECT count(*) FROM evidence_pack WHERE schema_version='v1.0' AND scan_result IS NULL` must return `0` before CAB submission.
- ✅ WORM storage example: Azure Blob container set to `immutabilityPolicy` with `days=3650`.
- ❌ Editing existing evidence pack JSON after approval without creating new version and re-approval is forbidden.

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [CAB Workflow](../docs/architecture/cab-workflow.md)

---

**Evidence Pack Rules v1.0 — Design**
