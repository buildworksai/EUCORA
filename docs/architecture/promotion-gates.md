# Promotion Gates

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Promotion gates are **measurable thresholds** that must be met before a deployment can progress from one ring to the next. All gates are **deterministic** and **auditable**, ensuring explainable ring progression decisions.

**Design Principle**: Determinism — all promotion decisions are based on explicit, measurable criteria.

---

## Gate Evaluation Process

1. **Telemetry Collection**: Query execution plane for success rate, time-to-compliance, incident data
2. **Gate Evaluation**: Compare metrics against ring-specific thresholds
3. **Decision**: Pass → promote to next ring; Fail → remain in current ring, trigger remediation
4. **Audit**: Record gate evaluation result in event store with correlation ID

---

## Promotion Gate Thresholds

### Ring 0 → Ring 1 (Lab → Canary)

**Success Rate**: ≥ **98%**
- Install success rate across all devices in Ring 0
- Measured over minimum 24-hour observation period

**Time-to-Compliance**: ≤ **24 hours** (online sites)
- Time from deployment intent creation to successful install on ≥98% of devices

**Incident Threshold**: **Zero** security incidents attributable to package

**Rollback Validation**: Rollback plan validated and tested in Ring 0

**Evidence Completeness**: All required evidence pack fields present

---

### Ring 1 → Ring 2 (Canary → Pilot)

**Success Rate**: ≥ **97%**
- Install success rate across Ring 1 devices
- Measured over minimum 48-hour observation period

**Time-to-Compliance**:
- Online sites: ≤ **24 hours**
- Intermittent sites: ≤ **72 hours**

**Incident Threshold**: **Zero** security incidents attributable to package

**Rollback Validation**: Rollback strategy validated for target execution plane(s)

**CAB Approval**: Required if `Risk > 50` or privileged tooling

**Promotion Gate Evaluation**: All Ring 1 gates passed

---

### Ring 2 → Ring 3 (Pilot → Department)

**Success Rate**: ≥ **99%** (enterprise standard apps)
- Install success rate across Ring 2 devices
- Measured over minimum 72-hour observation period

**Time-to-Compliance**:
- Online sites: ≤ **24 hours**
- Intermittent sites: ≤ **72 hours**
- Air-gapped sites: ≤ **7 days** (or next approved transfer window)

**Incident Threshold**: **Zero** security incidents attributable to package

**Rollback Validation**: Rollback strategy validated and tested

**CAB Approval**: Required if `Risk > 50` or privileged tooling

**Promotion Gate Evaluation**: All Ring 2 gates passed

---

### Ring 3 → Ring 4 (Department → Global)

**Success Rate**: ≥ **99%** (enterprise standard apps)
- Install success rate across Ring 3 devices
- Measured over minimum 7-day observation period

**Time-to-Compliance**:
- Online sites: ≤ **24 hours**
- Intermittent sites: ≤ **72 hours**
- Air-gapped sites: ≤ **7 days** (or next approved transfer window)

**Incident Threshold**: **Zero** security incidents attributable to package

**Rollback Validation**: Rollback strategy validated and tested

**CAB Approval**: Required if `Risk > 50` or privileged tooling

**Promotion Gate Evaluation**: All Ring 3 gates passed

---

## Gate Evaluation Implementation

### Success Rate Calculation

```python
success_rate = (successful_installs / total_target_devices) * 100
```

Where:
- `successful_installs`: Devices reporting successful install status
- `total_target_devices`: Total devices in ring scope

### Time-to-Compliance Calculation

```python
time_to_compliance = max(device_compliance_times) - deployment_start_time
```

Where:
- `device_compliance_times`: Individual device compliance timestamps
- `deployment_start_time`: Deployment intent creation timestamp

### Incident Detection

Incidents are detected via:
- SIEM integration (Azure Sentinel)
- Telemetry event analysis
- Manual incident reports linked to deployment correlation ID

---

## Gate Failure Handling

When a promotion gate fails:

1. **Remain in Current Ring**: Deployment does not progress
2. **Emit Gate Failure Event**: Record in event store with correlation ID
3. **Trigger Remediation**: If failure is recoverable, trigger remediation workflow
4. **Notify Stakeholders**: Alert deployment owner and endpoint operations
5. **CAB Review**: If failure persists, escalate to CAB for review

---

## Gate Override (Break-Glass)

Gate overrides require:
- **CAB Approval**: Explicit approval for gate bypass
- **Justification**: Documented reason for override
- **Compensating Controls**: Additional monitoring or restrictions
- **Audit Trail**: Immutable record in event store

**Use Cases**:
- Critical security patches
- Emergency deployments
- Business-critical applications with documented exceptions

---

## Calibration

Promotion gate thresholds are **provisional** for v1.0 and may be adjusted based on:
- Historical deployment data
- Incident analysis
- CAB feedback
- Quarterly Security + CAB review

Threshold changes require:
- Version bump (e.g., `promotion_gates_v1.0` → `v1.1`)
- Evidence of calibration (data analysis)
- CAB approval

---

## References

- [Ring Model](./ring-model.md)
- [Risk Model](./risk-model.md)
- [CAB Workflow](./cab-workflow.md)
- [Telemetry Collection](../architecture/telemetry.md)

