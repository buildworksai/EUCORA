# 004 — Why Intune Primary for Windows

**Status**: Accepted
**Date**: 2026-01-04

## Context
Intune already manages the majority of Windows devices and integrates with Entra ID and Conditional Access. Introducing a new primary management plane would duplicate capabilities and complicate SoD.

## Decision
Accept Intune as the primary execution plane for Windows with SCCM handling constrained/offline sites via the Control Plane’s co-management strategy. SCCM DPs serve as the authoritative content channel for those sites, while Intune maintains compliance assignments and telemetry.

## Consequences
- Minimizes additional infrastructure while meeting compliance/governance needs.
- Clear boundary between policy intent (Control Plane) and execution (Intune/SCCM).
- Provides deterministic fallback for air-gapped/offline environments using SCCM DPs and connected cache patterns.
