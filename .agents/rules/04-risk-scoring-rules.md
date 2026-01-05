# Risk Scoring Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Enforce deterministic risk scoring with normalized factors, versioned models, and quarterly calibration reminders.
**Design Principle**: "Deterministic risk scoring with explicit factor definitions (no AI-driven decisions)."

## Rules
1. Risk formula: `RiskScore = clamp(0..100, Σ(weight_i × normalized_factor_i))`.
2. Normalized factors must live between 0.0 and 1.0. Document scoring rubric per factor (see architecture/risk-model). Provide sample values for publisher trust, privilege, SBOM/vuln.
3. Thresholds: `Risk ≤ 50` allows automated Ring 1 progression; `Risk > 50` requires CAB approval beyond Ring 1; privileged tooling always CAB-gated.
4. Calibration frequency: quarterly review by Security + CAB with recorded minutes; updates create new model version (e.g., `risk_model_v1.1`).
5. Evidence packs must include factor contributions and normalized values.

## Enforcement Examples
- ✅ Publisher trust rubric snippet: signed + known vendor = 0.1; signed + unknown = 0.4; unsigned = 0.9.
- ✅ Vulnerability factor: no High/Critical findings = 0.0; High only = 0.7; Critical present = 1.0.
- ❌ Publishing with `Risk > 50` if CAB approval record missing (audit event) is forbidden.

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [Risk Model](../docs/architecture/risk-model.md)

---

**Risk Scoring Rules v1.0 — Design**
