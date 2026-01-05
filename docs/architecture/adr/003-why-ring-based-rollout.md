# 003 — Why Ring-Based Rollout

**Status**: Accepted
**Date**: 2026-01-04

## Context
Deployments across 50k endpoints with diverse sites cannot proceed “all at once” without risking outages and compliance violations. We need measurable promotion gates that match the Control Plane’s deterministic model.

## Decision
Adopt a ring progression (Lab → Canary → Pilot → Department → Global) with defined success thresholds (98/97/99%) and time-to-compliance targets (24h/72h/7d). Rollback validation is mandatory before Ring 1 promotion; Ring 2+ promotions require CAB approval when `Risk > 50`.

## Consequences
- Provides measurable guardrails for CAB and operations teams.
- Enables incremental rollouts and controlled scaling across sites, including air-gapped deployments.
- Ensures rollbacks are tested and documented before affecting large audiences.
