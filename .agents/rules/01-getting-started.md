# Getting Started for Contributors

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview
Quick ramp-up for new contributors to the Enterprise Endpoint Application Packaging & Deployment Factory.
**Design Principle**: "Thin Control Plane (policy + orchestration + evidence only)." This guide keeps new engineers aligned with the control-plane discipline before they touch production assets.

## Prerequisites & Environment
1. Entra ID access (Platform Admin, Packaging, Publisher groups as needed).
2. Microsoft Intune tenant + Azure subscription with RBAC scoped for labs.
3. Vault access (Azure Key Vault) for service principals, signing certs, API tokens.
4. Local dev setup: repo clone, `pyenv` toolchain (Python 3.11), Node 18, `pre-commit` hooks installed.
5. Lab tenant for Ring 0 testing: deploy artifacts through Packaging Factory pipeline → risk model → evidence pack → Ring 0 in Intune.

## First Deployment Walkthrough
1. Packaging Engineer builds artifact → signs → SBOM + vuln scan in artifact pipeline.
2. Control Plane computes risk score, generates evidence pack, and emits correlation id `dp-20260104-0001`.
3. Publisher creates Deployment Intent for Ring 0, verifies evidence pack completeness, then calls Intune connector (Graph API `POST /deviceAppManagement/mobileApps`).
4. Rollout Orchestrator evaluates Ring 0 success (≥98% test installs). Upon pass, promotion enters Ring 1 (Canary) per thresholds.

## Validation
- ✅ Command example: `./tools/control-plane-cli submit-deployment --ring 0 --correlation-id dp-20260104-0001` only runs after full evidence pack.
- ❌ Skipping RBAC group membership (e.g., using Platform Admin creds for packaging) violates SoD.

## Related Documentation
- [Architecture Overview v1.2](../docs/architecture/architecture-overview.md)
- [Control Plane Design](../docs/architecture/control-plane-design.md)

---

**Getting Started for Contributors v1.0 — Design**
