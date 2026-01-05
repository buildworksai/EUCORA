# 002 — Why Deterministic Risk Scoring

**Status**: Accepted
**Date**: 2026-01-04

## Context
Risk scoring must gate automation and CAB approvals. Without deterministic, documented factors, stakeholders worry about opaque decisions and the possibility of AI-driven outcomes.

## Decision
Implement a formula `RiskScore = clamp(0..100, Σ(weight_i × normalized_factor_i))` with documented normalized values and quarterly calibration. All risk models are versioned (e.g., `risk_model_v1.0`). Risk scores greater than 50 automatically require CAB approval for Ring 2+ deployments.

## Consequences
- Allows CAB to audit decisions, tune weights, and respond to incidents.
- Prevents “black box” scoring while still allowing future enhancements via new model versions.
- Ensures compliance with governance and audit requirements.
