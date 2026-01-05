# Ring Rollout Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Enforce ring progression order, promotion gate thresholds, rollback validation, and CAB enforcement for risk > 50.
**Design Principle**: "Deterministic ring-based rollout with measurable gates."

## Rules
1. Rings progress Lab → Canary → Pilot → Department → Global; Ring 0 rollback validated before any Ring 1 promotion.
2. Promotion gate metrics: Ring 1 success ≥98%, Ring 2 ≥97%, Rings 3-4 ≥99%; time-to-compliance thresholds (Online ≤24h, Intermittent ≤72h, Air-gapped ≤7d).
3. CAB approval required for `Risk > 50` before publishing beyond Ring 1; Ring 1 still needs evidence pack completeness.
4. Deployment scheduling respects site window constraints, including air-gapped transfer windows and maintenance windows.
5. Rollout metadata must include correlation ids for each promotion event.

## Enforcement Examples
- ✅ Promotion command: `POST /rollout/promote` with body `{"ring":1,"success_rate":0.985,"time_to_compliance":22}` (CAUTION: success_rate must be ≥98% to promote Ring 1 to Ring 2).
- ✅ Ring 0 rollback validation crates autop-runbook referencing `rollback_job_id` before enabling Ring 1.
- ❌ Scheduling Ring 2 start during air-gapped transfer window without documented maintenance approval.

## Related Documentation
- [Ring Model](../docs/architecture/ring-model.md)
- [Control Plane Design](../docs/architecture/control-plane-design.md)

---

**Ring Rollout Rules v1.0 — Design**
