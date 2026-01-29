# Audit Trail Schema

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This document defines the **immutable audit trail schema** for all deployment events, approvals, and system actions. All events are stored in an **append-only event store** for compliance and auditability.

**Design Principle**: Audit Trail Integrity — all events stored in append-only event store (immutable).

---

## Event Store Architecture

### Append-Only Policy

- **No Updates**: Events cannot be modified after creation
- **No Deletes**: Events cannot be deleted
- **Immutable**: Once written, events are permanent

### Storage

- **Database**: PostgreSQL with append-only constraints
- **Backup**: Daily backups with 7-year retention
- **Archival**: Old events archived to cold storage

---

## Event Schema

### Base Event Structure

```json
{
  "event_id": "uuid",
  "correlation_id": "uuid",
  "event_type": "string",
  "event_data": {},
  "actor": "string",
  "timestamp": "2026-01-06T10:00:00Z",
  "created_at": "2026-01-06T10:00:00Z"
}
```

### Event Types

#### Deployment Events

- `DEPLOYMENT_CREATED`: Deployment intent created
- `DEPLOYMENT_STARTED`: Deployment execution started
- `DEPLOYMENT_COMPLETED`: Deployment successfully completed
- `DEPLOYMENT_FAILED`: Deployment failed
- `ROLLBACK_INITIATED`: Rollback started
- `ROLLBACK_COMPLETED`: Rollback completed

#### Approval Events

- `CAB_SUBMITTED`: CAB submission created
- `CAB_APPROVED`: CAB approval granted
- `CAB_REJECTED`: CAB approval denied
- `EXCEPTION_APPROVED`: Exception approved
- `EXCEPTION_DENIED`: Exception denied
- `EXCEPTION_EXPIRED`: Exception expired

#### Risk Assessment Events

- `RISK_ASSESSED`: Risk score calculated
- `RISK_MODEL_UPDATED`: Risk model version updated

#### System Events

- `DRIFT_DETECTED`: Reconciliation loop detected drift
- `REMEDIATION_TRIGGERED`: Remediation workflow triggered
- `GATE_EVALUATED`: Promotion gate evaluated
- `GATE_FAILED`: Promotion gate failed

---

## Event Data Schemas

### Deployment Created Event

```json
{
  "event_type": "DEPLOYMENT_CREATED",
  "event_data": {
    "deployment_intent_id": "uuid",
    "app_name": "Application Name",
    "version": "1.2.3",
    "target_ring": "canary",
    "execution_plane": "intune",
    "target_scope": {
      "acquisition_boundary": "acquisition-a",
      "business_unit": "bu-engineering",
      "site": "site-1"
    },
    "evidence_pack_id": "uuid",
    "risk_score": 35
  },
  "actor": "publisher@example.com"
}
```

### CAB Approved Event

```json
{
  "event_type": "CAB_APPROVED",
  "event_data": {
    "approval_id": "uuid",
    "deployment_intent_id": "uuid",
    "approver": "cab-member@example.com",
    "decision": "approved",
    "conditions": ["Deploy only to Ring 1"],
    "justification": "Low risk, well-tested",
    "risk_score": 45
  },
  "actor": "cab-member@example.com"
}
```

### Drift Detected Event

```json
{
  "event_type": "DRIFT_DETECTED",
  "event_data": {
    "deployment_intent_id": "uuid",
    "drift_type": "missing_assignment",
    "severity": "high",
    "affected_devices": 10,
    "execution_plane": "intune",
    "remediation_triggered": true
  },
  "actor": "system:reconciliation_loop"
}
```

---

## Database Schema

### DeploymentEvent Model

```python
class DeploymentEvent(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    correlation_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=50)
    event_data = models.JSONField()
    actor = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['correlation_id', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
        ]
        ordering = ['-created_at']
```

### Immutability Enforcement

```python
def save(self, *args, **kwargs):
    if self.pk is not None:
        raise ValueError('DeploymentEvent is append-only, updates not allowed')
    super().save(*args, **kwargs)

def delete(self, *args, **kwargs):
    raise ValueError('DeploymentEvent is append-only, deletes not allowed')
```

---

## Query Patterns

### Get Events by Correlation ID

```python
events = DeploymentEvent.objects.filter(
    correlation_id=correlation_id
).order_by('created_at')
```

### Get Events by Type

```python
events = DeploymentEvent.objects.filter(
    event_type='DEPLOYMENT_CREATED',
    created_at__gte=timezone.now() - timedelta(days=30)
)
```

### Get Events by Actor

```python
events = DeploymentEvent.objects.filter(
    actor='publisher@example.com',
    created_at__gte=timezone.now() - timedelta(days=7)
)
```

---

## SIEM Integration

### Azure Sentinel Integration

- **Endpoint**: Azure Sentinel Data Collector API
- **Format**: JSON events
- **Fields**: correlation_id, event_type, actor, timestamp
- **Filtering**: Send all events or filtered subset

### Event Forwarding

```python
def forward_to_siem(event):
    sentinel_client.post_event({
        'correlation_id': event.correlation_id,
        'event_type': event.event_type,
        'actor': event.actor,
        'timestamp': event.created_at.isoformat(),
        'event_data': event.event_data
    })
```

---

## Retention Policy

- **Retention Period**: 7 years (compliance requirement)
- **Archival**: Events older than 1 year archived to cold storage
- **Deletion**: Requires compliance team approval

---

## References

- [Event Store](../architecture/event-store.md)
- [Approval Audit Schema](../architecture/approval-audit-schema.md)
- [SIEM Integration](./siem-integration.md)
