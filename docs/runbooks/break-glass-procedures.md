# Break-Glass Procedures

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

Break-glass procedures provide **emergency access** and **deployment override** capabilities for critical incidents. All break-glass actions are **audited** and require **post-incident review**.

**Design Principle**: Audit Trail Integrity — all break-glass actions logged to SIEM.

---

## Break-Glass Scenarios

### 1. Critical Security Patch

**Scenario**: Zero-day vulnerability requiring immediate deployment

**Procedure**:
1. **Justification**: Document security threat
2. **CAB Notification**: Notify CAB (may be post-deployment)
3. **Break-Glass Access**: Use break-glass account
4. **Deployment**: Deploy patch with expedited process
5. **Post-Incident Review**: Complete within 24 hours

### 2. Production Outage

**Scenario**: Application causing production outage

**Procedure**:
1. **Incident Declaration**: Declare incident
2. **Break-Glass Access**: Use break-glass account
3. **Rollback**: Execute emergency rollback
4. **Post-Incident Review**: Complete within 48 hours

### 3. System Failure

**Scenario**: Control Plane unavailable, deployment required

**Procedure**:
1. **System Status**: Verify Control Plane unavailable
2. **Break-Glass Access**: Use break-glass account
3. **Direct Deployment**: Deploy via execution plane directly
4. **Post-Incident Review**: Complete within 48 hours

---

## Break-Glass Accounts

### Account Requirements

- **Separate Accounts**: Dedicated break-glass accounts (not regular user accounts)
- **Access Reviews**: Quarterly access reviews
- **Rotation**: Credentials rotated after each use
- **Monitoring**: All access logged to SIEM

### Account Management

- **Storage**: Stored in secure vault
- **Access**: Requires two-person approval
- **Usage**: Logged and audited
- **Rotation**: Automatic rotation after use

---

## Break-Glass Process

### 1. Incident Declaration

- Declare incident severity
- Document justification
- Notify stakeholders

### 2. Break-Glass Access

- Request break-glass credentials
- Two-person approval required
- Access granted with time limit (default: 4 hours)

### 3. Action Execution

- Execute break-glass action
- Document all actions taken
- Log all operations to SIEM

### 4. Post-Incident Review

- Complete within 24-48 hours
- Document incident root cause
- Review break-glass actions
- Update procedures if needed

---

## Audit Requirements

### SIEM Logging

All break-glass actions logged to SIEM:

```json
{
  "event_type": "BREAK_GLASS_ACCESS",
  "actor": "break-glass-account",
  "action": "deployment_override",
  "justification": "Critical security patch",
  "timestamp": "2026-01-06T10:00:00Z",
  "incident_id": "uuid"
}
```

### Event Store

All break-glass actions recorded in event store:

```json
{
  "correlation_id": "uuid",
  "event_type": "BREAK_GLASS_ACTION",
  "event_data": {
    "action": "deployment_override",
    "justification": "Critical security patch",
    "incident_id": "uuid"
  },
  "actor": "break-glass-account",
  "created_at": "2026-01-06T10:00:00Z"
}
```

---

## Post-Incident Actions

### Required Actions

1. **Credential Rotation**: Rotate break-glass credentials
2. **Access Review**: Review break-glass account access
3. **Incident Report**: Complete incident report
4. **Procedure Update**: Update procedures if gaps identified
5. **CAB Review**: Present incident to CAB

### Timeline

- **Credential Rotation**: Within 1 hour of incident resolution
- **Incident Report**: Within 24 hours
- **CAB Review**: Within 7 days

---

## References

- [Incident Response](./incident-response.md)
- [Audit Trail Schema](../infrastructure/audit-trail-schema.md)
- [SIEM Integration](../infrastructure/siem-integration.md)
