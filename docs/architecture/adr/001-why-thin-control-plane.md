# 001 — Why Thin Control Plane

**Status**: Accepted
**Date**: 2026-01-04

## Context
The enterprise already operates multiple execution planes (Intune, Jamf, SCCM, Landscape, Ansible). A monolithic control plane that directly manages endpoints would introduce duplication, new attack surface, and risk to SoD.

## Decision
We keep the control plane strictly thin: it defines policy intents, orchestrates approvals, enforces deterministic risk scoring, and records evidence – but it never replaces execution planes or directly touches endpoints. All connectors talk to existing management APIs only.

## Consequences
- Ensures rapid CAB acceptance; reduces project risk.
- Offloads device configuration responsibilities to established tools.
- Limits the control plane’s scope to deterministic orchestration and auditability.
