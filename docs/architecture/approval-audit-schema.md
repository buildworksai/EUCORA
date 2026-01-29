# Approval Audit Schema

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This document defines the **immutable audit schema** for CAB approvals, exception approvals, and security reviewer decisions. All approval records are stored in an **append-only event store** for compliance and auditability.

**Design Principle**: Audit Trail Integrity — all events stored in append-only event store (immutable).

---

## Approval Record Schema

### CAB Approval Record

```json
{
  "approval_id": "uuid",
  "deployment_intent_id": "uuid",
  "correlation_id": "uuid",
  "approval_type": "CAB_APPROVAL",
  "status": "approved|denied|pending|conditional",
  "conditions": [
    "Deploy only to Ring 1",
    "Monitor for 48 hours",
    "Rollback plan validated"
  ],
  "approver": "cab-member@example.com",
  "approver_role": "CAB_APPROVER",
  "approval_date": "2026-01-06T10:00:00Z",
  "expiry_date": "2026-04-06T10:00:00Z",
  "justification": "Low risk, well-tested application",
  "evidence_pack_id": "uuid",
  "risk_score": 35,
  "created_at": "2026-01-06T09:00:00Z",
  "updated_at": "2026-01-06T10:00:00Z"
}
```

### Security Reviewer Approval Record

```json
{
  "approval_id": "uuid",
  "exception_id": "uuid",
  "correlation_id": "uuid",
  "approval_type": "SECURITY_REVIEWER_APPROVAL",
  "status": "approved|denied|pending",
  "exception_type": "vulnerability_scan|cross_boundary|unsigned_package",
  "compensating_controls": [
    "Network isolation",
    "Enhanced monitoring"
  ],
  "approver": "security-reviewer@example.com",
  "approver_role": "SECURITY_REVIEWER",
  "approval_date": "2026-01-06T11:00:00Z",
  "expiry_date": "2026-04-06T11:00:00Z",
  "justification": "Critical security patch, compensating controls adequate",
  "created_at": "2026-01-06T10:30:00Z",
  "updated_at": "2026-01-06T11:00:00Z"
}
```

### Conditional Approval Record

```json
{
  "approval_id": "uuid",
  "deployment_intent_id": "uuid",
  "correlation_id": "uuid",
  "approval_type": "CONDITIONAL_APPROVAL",
  "status": "conditional",
  "conditions": [
    "Deploy only to Ring 1 (Canary)",
    "Monitor success rate for 48 hours",
    "Require 99% success rate before Ring 2 promotion",
    "Rollback if success rate < 97%"
  ],
  "approver": "cab-member@example.com",
  "approver_role": "CAB_APPROVER",
  "approval_date": "2026-01-06T12:00:00Z",
  "expiry_date": "2026-02-06T12:00:00Z",
  "justification": "New application, conditional approval for limited scope",
  "evidence_pack_id": "uuid",
  "risk_score": 45,
  "created_at": "2026-01-06T11:30:00Z",
  "updated_at": "2026-01-06T12:00:00Z"
}
```

---

## Event Store Integration

All approval actions generate events in the append-only event store:

### Approval Event

```json
{
  "correlation_id": "uuid",
  "event_type": "CAB_APPROVED|CAB_REJECTED|EXCEPTION_APPROVED|EXCEPTION_DENIED",
  "event_data": {
    "approval_id": "uuid",
    "deployment_intent_id": "uuid",
    "approver": "cab-member@example.com",
    "decision": "approved",
    "conditions": ["condition1", "condition2"],
    "justification": "string"
  },
  "actor": "cab-member@example.com",
  "created_at": "2026-01-06T10:00:00Z"
}
```

### Approval Revocation Event

```json
{
  "correlation_id": "uuid",
  "event_type": "APPROVAL_REVOKED",
  "event_data": {
    "approval_id": "uuid",
    "revoked_by": "platform-admin@example.com",
    "revocation_reason": "Security incident discovered",
    "original_approval_date": "2026-01-06T10:00:00Z"
  },
  "actor": "platform-admin@example.com",
  "created_at": "2026-01-06T15:00:00Z"
}
```

---

## Database Schema

### ApprovalRecord Model

```python
class ApprovalRecord(models.Model):
    approval_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    deployment_intent_id = models.UUIDField(null=True, blank=True)
    exception_id = models.UUIDField(null=True, blank=True)
    correlation_id = models.UUIDField(db_index=True)
    approval_type = models.CharField(max_length=50)  # CAB_APPROVAL, SECURITY_REVIEWER_APPROVAL
    status = models.CharField(max_length=20)  # approved, denied, pending, conditional
    conditions = models.JSONField(default=list)
    approver = models.EmailField()
    approver_role = models.CharField(max_length=50)
    approval_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    justification = models.TextField()
    evidence_pack_id = models.UUIDField(null=True, blank=True)
    risk_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['correlation_id', 'approval_date']),
            models.Index(fields=['deployment_intent_id']),
            models.Index(fields=['exception_id']),
            models.Index(fields=['status', 'expiry_date']),
        ]
```

---

## Immutability Enforcement

### Append-Only Policy

- **No Updates**: Approval records cannot be modified after creation
- **No Deletes**: Approval records cannot be deleted
- **Versioning**: Changes require new approval record with version link

### Implementation

```python
class ApprovalRecord(models.Model):
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError('ApprovalRecord is append-only, updates not allowed')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('ApprovalRecord is append-only, deletes not allowed')
```

---

## Approval Query Patterns

### Get Approvals for Deployment Intent

```python
approvals = ApprovalRecord.objects.filter(
    deployment_intent_id=deployment_intent_id,
    status='approved',
    expiry_date__gt=timezone.now()
).order_by('-approval_date')
```

### Get Expired Approvals

```python
expired_approvals = ApprovalRecord.objects.filter(
    status='approved',
    expiry_date__lt=timezone.now()
)
```

### Get Approvals by Approver

```python
approvals = ApprovalRecord.objects.filter(
    approver='cab-member@example.com',
    approval_date__gte=timezone.now() - timedelta(days=30)
)
```

---

## Compliance & Audit

### Retention Policy

- **Retention Period**: 7 years (compliance requirement)
- **Archival**: Old records archived to cold storage
- **Deletion**: Requires compliance team approval

### Audit Trail

All approval actions generate immutable events:
- Approval creation
- Approval revocation
- Approval expiry
- Condition updates (via new approval)

---

## References

- [CAB Workflow](./cab-workflow.md)
- [Exception Management](./exception-management.md)
- [Event Store](../architecture/event-store.md)
- [Risk Model](./risk-model.md)
