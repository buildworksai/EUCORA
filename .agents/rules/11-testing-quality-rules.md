# Testing & Quality Rules

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Ensure ≥90% coverage, pre-commit gate enforcement, idempotency, rollback, and integration testing with no exceptions.
**Design Principle**: "Quality gates are zero tolerance; deterministic behavior ensured by testing."

## Rules
1. Test coverage must be ≥90%; CI job `coverage-report` enforces this and fails with code 1 if not met.
2. Pre-commit hooks must run type checks (TypeScript/Python/Go), linting (`--max-warnings 0`), formatting, and secrets detection; failures block commits.
3. Idempotency tests validate connectors use correlation ids; duplicate correlation id run must produce same outcome.
4. Rollback tests execute in Ring 0 environment to validate strategies per plane before Ring 1 rollout.
5. Integration tests cover each connector end-to-end (Intune, Jamf, SCCM, Landscape, Ansible) with synthetic artifacts.

## Enforcement Examples
- ✅ CI command: `npm run test -- coverage` verifying ≥90% coverage; job fails with `EXIT CODE 1` if below.
- ✅ Pre-commit example: `pre-commit run --all-files` must pass before `git commit` completes.
- ❌ Skipping idempotency tests for SCCM connector is forbidden; they must assert `correlation_id` reuse returns `409` conflict, not duplicate deployments.

## Related Documentation
- [Control Plane Design](../docs/architecture/control-plane-design.md)
- [Connector Rules](../.agents/rules/08-connector-rules.md)

---

**Testing & Quality Rules v1.0 — Design**
