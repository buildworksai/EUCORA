# Reconciliation Loops

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

Reconciliation loops are **periodic processes** that detect drift between desired state (deployment intents) and actual state (execution plane state). They ensure **reconciliation over hope** — continuous enforcement of desired state rather than assuming deployments remain compliant.

**Design Principle**: Reconciliation over Hope — continuous desired-vs-actual drift detection.

---

## Reconciliation Process

### 1. State Query

Query execution plane state for:
- Application assignments (Intune/Jamf/SCCM)
- Package versions deployed
- Device compliance status
- Assignment scope (groups/collections)

**Frequency**: Every **1 hour** (configurable per app criticality)

### 2. State Comparison

Compare execution plane state to Control Plane deployment intents:
- **Desired State**: Deployment Intent records in Control Plane
- **Actual State**: Execution plane query results

### 3. Drift Detection

Identify mismatches:
- **Missing Assignments**: Intent exists but no execution plane assignment
- **Version Mismatch**: Wrong version deployed
- **Scope Mismatch**: Assignment scope differs from intent
- **Compliance Drift**: Devices not compliant with intent

### 4. Drift Event Emission

Emit drift events to event store:
- Correlation ID linkage
- Drift type and severity
- Affected devices/scopes
- Timestamp

### 5. Remediation Trigger

Trigger remediation workflows within policy constraints:
- **Automatic Remediation**: For low-risk drift (configurable)
- **Manual Review**: For high-risk drift or policy violations
- **CAB Escalation**: For persistent drift or security concerns

---

## Reconciliation Loop Implementation

### Celery Periodic Task

```python
@shared_task(name='apps.deployment_intents.tasks.reconciliation_loop')
def reconciliation_loop():
    """
    Periodic reconciliation loop (runs every hour).
    """
    active_intents = DeploymentIntent.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS', 'COMPLETED']
    )

    for intent in active_intents:
        # Query execution plane state
        actual_state = query_execution_plane(intent)

        # Compare to desired state
        drift = compare_states(intent, actual_state)

        if drift:
            # Emit drift event
            emit_drift_event(intent, drift)

            # Trigger remediation if policy allows
            if should_remediate(drift):
                trigger_remediation(intent, drift)
```

### Execution Plane Query

**Intune**:
- Microsoft Graph API: `GET /deviceAppManagement/mobileApps/{id}/assignments`
- Query device install status: `GET /deviceManagement/managedDevices/{id}/detectedApps`

**Jamf**:
- Jamf Pro API: `GET /JSSResource/policies`
- Query device compliance: `GET /JSSResource/computers`

**SCCM**:
- PowerShell/REST: Query collection membership and deployment status
- WMI queries for device compliance

---

## Drift Types

### 1. Missing Assignment

**Severity**: High
**Detection**: Intent exists but no execution plane assignment found
**Remediation**: Create assignment via connector

### 2. Version Mismatch

**Severity**: Medium
**Detection**: Wrong version deployed
**Remediation**: Update assignment to correct version

### 3. Scope Mismatch

**Severity**: High
**Detection**: Assignment scope differs from intent
**Remediation**: Update assignment scope (may require CAB approval)

### 4. Compliance Drift

**Severity**: Medium
**Detection**: Devices not compliant with intent
**Remediation**: Trigger compliance remediation scripts

---

## Remediation Policies

### Automatic Remediation

Allowed for:
- Low-risk drift (missing assignments, version mismatches)
- Non-production rings (Lab, Canary)
- Non-privileged applications

**Constraints**:
- Maximum remediation attempts: 3
- Backoff between attempts: Exponential (1h, 2h, 4h)
- Escalation after max attempts

### Manual Review Required

Required for:
- High-risk drift (scope mismatches)
- Production rings (Pilot, Department, Global)
- Privileged applications
- Security policy violations

### CAB Escalation

Required for:
- Persistent drift after remediation attempts
- Security incidents
- Cross-boundary scope changes
- Policy violations

---

## Reconciliation Frequency

| App Criticality | Frequency | Max Drift Tolerance |
|----------------|----------|---------------------|
| Critical | 15 minutes | 0 (immediate remediation) |
| High | 30 minutes | 1 hour |
| Standard | 1 hour | 4 hours |
| Low | 4 hours | 24 hours |

---

## Monitoring & Alerting

### Metrics

- **Drift Detection Rate**: Number of drift events per hour
- **Remediation Success Rate**: Percentage of successful remediations
- **Time-to-Remediation**: Average time from drift detection to resolution
- **Persistent Drift Count**: Drift events not resolved after max attempts

### Alerts

- **High Drift Rate**: >10 drift events/hour for critical apps
- **Remediation Failure**: Remediation attempts failing >50%
- **Persistent Drift**: Drift unresolved after max attempts
- **Security Drift**: Scope mismatches or policy violations

---

## Event Store Integration

All reconciliation events are stored in append-only event store:

```json
{
  "correlation_id": "uuid",
  "event_type": "DRIFT_DETECTED",
  "event_data": {
    "deployment_intent_id": "uuid",
    "drift_type": "missing_assignment",
    "severity": "high",
    "affected_devices": 10,
    "remediation_triggered": true
  },
  "actor": "system:reconciliation_loop",
  "created_at": "2026-01-06T00:00:00Z"
}
```

---

## References

- [Ring Model](./ring-model.md)
- [Execution Plane Connectors](./execution-plane-connectors.md)
- [Event Store](../architecture/event-store.md)
- [CAB Workflow](./cab-workflow.md)
