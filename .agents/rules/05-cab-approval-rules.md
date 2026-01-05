# CAB Approval Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Govern CAB evidence packs and approval workflow to enforce evidence-first governance and immutable audit trails.
**Design Principle**: "Evidence-first governance with policy intent system-of-record."

## Rules
1. Evidence pack completeness check runs before any CAB submission; required fields include artifact hashes, SBOM, scan report, rollout & rollback plans, test evidence, exception records.
2. CAB submission workflow: Packaging Engineer uploads evidence pack → CAB Approver reviews within 48h (24h for urgent) → approval/denial recorded in append-only event store with correlation id.
3. All approvals are immutable; updates require new event version and re-approval.
4. Exception handling: expiry date, compensating controls, Security Reviewer approval, and audit event linking to deployment intent.
5. Scope changes (cross-boundary targeting) require CAB approval and scope-diff summary in evidence pack.

## Enforcement Examples
- ✅ Validation rule: `if evidence_pack.test_evidence.missing: reject submission (HTTP 400, code: EVIDENCE_MISSING_TEST)`.
- ✅ Exception example: critical vuln exception stored with `expiry=2026-02-15`, `controls=["additional monitoring"]`, `approver=Security Reviewer`.
- ❌ Approving `Risk > 50` change without CAB record and correlation id is forbidden; event store must show `event_type=cab.approval`.

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [CAB Workflow](../docs/architecture/cab-workflow.md)

---

**CAB Approval Rules v1.0 — Design**
