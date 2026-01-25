# Intune Rollback Procedures

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This document defines **rollback strategies** for Intune deployments. Rollback is validated before Ring 2+ promotion.

**Design Principle**: Rollback Validation — all rollback strategies validated before Ring 2+ promotion.

---

## Rollback Strategies

### 1. Supersedence/Version Pinning

**Use Case**: Rollback to previous version
**Method**: Create supersedence relationship in Intune

**Process**:
1. Identify previous version to rollback to
2. Create supersedence relationship (new version → old version)
3. Update assignment to target old version
4. Monitor rollback success

**Limitations**:
- Requires previous version to be retained
- Supersedence may not uninstall new version immediately

### 2. Targeted Uninstall

**Use Case**: Remove application completely
**Method**: Create uninstall assignment

**Process**:
1. Create uninstall assignment targeting affected devices
2. Set uninstall command from package metadata
3. Deploy uninstall assignment
4. Monitor uninstall success

**Requirements**:
- Valid uninstall command in package metadata
- Detection rules for uninstall verification

### 3. Remediation Scripts

**Use Case**: Fix issues without full rollback
**Method**: Deploy PowerShell remediation script

**Process**:
1. Create remediation script (PowerShell)
2. Package as Win32 app with detection rules
3. Deploy remediation script
4. Monitor remediation success

**Use Cases**:
- Registry fixes
- File cleanup
- Configuration corrections

---

## Rollback Validation

### Pre-Rollback Checks

1. **Previous Version Available**
   - Verify previous version exists in Intune
   - Verify previous version is retained (90-day policy)

2. **Uninstall Command Valid**
   - Verify uninstall command in package metadata
   - Test uninstall command in lab environment

3. **Detection Rules Valid**
   - Verify detection rules for rollback verification
   - Test detection rules in lab environment

4. **Assignment Scope Valid**
   - Verify target device scope
   - Verify device count matches expectations

### Rollback Testing

**Lab Testing**:
- Test rollback in Ring 0 (Lab)
- Verify rollback success rate ≥95%
- Document rollback procedure

**Validation Criteria**:
- Rollback executes successfully
- Previous version installs correctly
- New version uninstalls (if applicable)
- Detection rules verify rollback

---

## Rollback Execution

### 1. Rollback Initiation

**Trigger**: Manual or automatic (on gate failure)

**Process**:
1. Create rollback intent in Control Plane
2. Generate rollback plan
3. Validate rollback plan
4. Execute rollback via Intune connector

### 2. Rollback Plan

```json
{
  "rollback_id": "uuid",
  "deployment_intent_id": "uuid",
  "rollback_strategy": "supersedence|uninstall|remediation",
  "target_version": "1.2.2",
  "target_devices": ["device-id-1", "device-id-2"],
  "rollback_commands": {
    "uninstall": "msiexec /x {product_code} /qn",
    "detection": "file:C:\\Program Files\\App\\app.exe"
  },
  "estimated_duration_minutes": 60
}
```

### 3. Rollback Execution

**Intune Connector**:
1. Create rollback assignment in Intune
2. Target affected devices
3. Deploy rollback assignment
4. Monitor rollback progress

### 4. Rollback Verification

**Reconciliation Loop**:
1. Query Intune for device compliance
2. Verify previous version installed
3. Verify new version uninstalled (if applicable)
4. Emit rollback completion event

---

## Rollback Events

### Rollback Initiated Event

```json
{
  "correlation_id": "uuid",
  "event_type": "ROLLBACK_INITIATED",
  "event_data": {
    "rollback_id": "uuid",
    "deployment_intent_id": "uuid",
    "rollback_strategy": "supersedence",
    "reason": "Promotion gate failure",
    "target_devices": 100
  },
  "actor": "system:rollback_orchestrator",
  "created_at": "2026-01-06T10:00:00Z"
}
```

### Rollback Completed Event

```json
{
  "correlation_id": "uuid",
  "event_type": "ROLLBACK_COMPLETED",
  "event_data": {
    "rollback_id": "uuid",
    "success_rate": 98.5,
    "failed_devices": 2,
    "duration_minutes": 45
  },
  "actor": "system:intune_connector",
  "created_at": "2026-01-06T10:45:00Z"
}
```

---

## Rollback Failure Handling

### Partial Rollback Failure

**Handling**:
1. Identify failed devices
2. Retry rollback for failed devices
3. Escalate to manual intervention if retry fails

### Complete Rollback Failure

**Handling**:
1. Log failure to event store
2. Notify deployment owner
3. Escalate to CAB/Security team
4. Consider break-glass procedures

---

## References

- [Intune Connector Spec](./connector-spec.md)
- [Error Handling](./error-handling.md)
- [Ring Model](../../architecture/ring-model.md)
- [Promotion Gates](../../architecture/promotion-gates.md)
