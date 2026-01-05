# RBAC Enforcement Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Strict SoD enforcement for Packaging, Publishing, and Approval roles, with scoped service principals and rotating credentials.
**Design Principle**: "Separation of duties (Packaging ≠ Publishing ≠ Approval) enforced by RBAC boundaries."

## Rules
1. Packaging Engineers have no Intune production write access; stored in separate Entra ID group with read-only staging rights.
2. Publishers reside in scoped Entra ID group; access reviewed quarterly and enforced via PIM/JIT workflows (max 1h sessions).
3. CAB Approvers have approval-only rights; cannot publish or modify artifacts.
4. Service principals must be scoped per role; no shared credentials between Packaging and Publishing.
5. Break-glass: dual-control (two approvers) needed for emergency overrides; credentials rotated immediately after use.

## Enforcement Examples
- ✅ Quarterly access review log entry: `rbac_review_2026Q1.csv` showing Packaging group membership audit.
- ✅ PIM request command: `az role assignment create --assignee <Publisher-SP>` with `--role Reader` for staging, `--expires-in PT1H` for production.
- ❌ Using Publisher SP for packaging pipeline or giving CAB Approver publish rights violates SoD.

## Related Documentation
- [RBAC Configuration](../docs/infrastructure/rbac-configuration.md)
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)

---

**RBAC Enforcement Rules v1.0 — Design**
