# Exception Management

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Exception management provides a **controlled workflow** for approving deviations from standard policies (e.g., vulnerability scan failures, unsigned packages, cross-boundary deployments). All exceptions require **Security Reviewer approval**, **expiry dates**, and **compensating controls**.

**Design Principle**: Evidence-First Governance — exceptions are documented, approved, and auditable.

---

## Exception Types

### 1. Vulnerability Scan Exception

**Use Case**: Package has High/Critical vulnerabilities but deployment is approved  
**Requires**:
- Security Reviewer approval
- Expiry date (default: 90 days)
- Compensating controls (e.g., network isolation, additional monitoring)
- Justification

**Example**:
```json
{
  "type": "vulnerability_scan",
  "vulnerabilities": [
    {"cve": "CVE-2024-1234", "severity": "High", "component": "library-v1.2.3"}
  ],
  "expiry_date": "2026-04-06",
  "compensating_controls": [
    "Network isolation",
    "Enhanced monitoring",
    "Quarterly review"
  ],
  "approved_by": "security-reviewer@example.com",
  "approval_date": "2026-01-06"
}
```

### 2. Unsigned Package Exception

**Use Case**: Package cannot be signed (legacy, third-party constraints)  
**Requires**:
- Security Reviewer approval
- Expiry date
- Compensating controls (e.g., hash verification, source verification)
- Justification

### 3. Cross-Boundary Deployment Exception

**Use Case**: Deploying app across acquisition boundaries  
**Requires**:
- CAB approval
- Security Reviewer approval
- Expiry date
- Compensating controls (e.g., scope restrictions, additional monitoring)
- Blast radius analysis

### 4. Promotion Gate Override Exception

**Use Case**: Bypassing promotion gate thresholds  
**Requires**:
- CAB approval
- Justification
- Compensating controls
- Expiry date

---

## Exception Lifecycle

### 1. Exception Request

**Initiated By**: Packaging Engineer, Publisher, or Platform Admin  
**Required Fields**:
- Exception type
- Justification
- Proposed compensating controls
- Requested expiry date
- Affected deployment intent (if applicable)

### 2. Security Reviewer Review

**Review Criteria**:
- Risk assessment
- Compensating controls adequacy
- Expiry date reasonableness
- Justification validity

**Decision**: Approve / Deny / Request Changes

### 3. CAB Review (if required)

**Required For**:
- Cross-boundary deployments
- High-risk exceptions (>50 risk score)
- Privileged tooling exceptions

**Decision**: Approve / Deny / Request Changes

### 4. Exception Activation

**Upon Approval**:
- Exception record created in evidence store
- Linked to deployment intent (if applicable)
- Expiry date set
- Monitoring configured

### 5. Exception Expiry

**At Expiry**:
- Exception automatically invalidated
- Deployment blocked if exception still required
- Notification sent to exception owner
- Re-approval required for extension

---

## Exception Record Schema

```json
{
  "exception_id": "uuid",
  "type": "vulnerability_scan|cross_boundary|unsigned_package|gate_override",
  "status": "pending|approved|denied|expired",
  "justification": "string",
  "compensating_controls": ["string"],
  "expiry_date": "2026-04-06",
  "requested_by": "user@example.com",
  "approved_by": "security-reviewer@example.com",
  "cab_approved_by": "cab-member@example.com",
  "approval_date": "2026-01-06",
  "deployment_intent_id": "uuid",
  "created_at": "2026-01-06T00:00:00Z",
  "updated_at": "2026-01-06T00:00:00Z"
}
```

---

## Compensating Controls

Compensating controls must be **specific**, **measurable**, and **enforceable**:

### Examples

**Network Isolation**:
- Specific: "Deploy to isolated VLAN 192.168.100.0/24"
- Measurable: Network monitoring confirms isolation
- Enforceable: Firewall rules enforce VLAN boundaries

**Enhanced Monitoring**:
- Specific: "Monitor application logs for suspicious activity"
- Measurable: Log analysis queries configured
- Enforceable: SIEM alerts configured

**Scope Restrictions**:
- Specific: "Limit deployment to Ring 1 (Canary) only"
- Measurable: Deployment intent scope validation
- Enforceable: Control Plane policy enforcement

---

## Exception Expiry Management

### Automatic Expiry

Exceptions automatically expire at `expiry_date`. At expiry:
1. Exception status set to `expired`
2. Deployment blocked if exception still required
3. Notification sent to exception owner
4. Re-approval workflow initiated

### Extension Process

To extend an exception:
1. Request extension with justification
2. Security Reviewer review
3. CAB review (if required)
4. New expiry date set

**Maximum Extension**: 90 days from original expiry

---

## Exception Audit Trail

All exception actions are recorded in event store:

```json
{
  "correlation_id": "exception-uuid",
  "event_type": "EXCEPTION_APPROVED|EXCEPTION_DENIED|EXCEPTION_EXPIRED",
  "event_data": {
    "exception_id": "uuid",
    "type": "vulnerability_scan",
    "decision": "approved",
    "reviewer": "security-reviewer@example.com"
  },
  "actor": "security-reviewer@example.com",
  "created_at": "2026-01-06T00:00:00Z"
}
```

---

## Policy Enforcement

### Pre-Deployment Checks

Before deployment:
1. Check for required exceptions
2. Validate exception status (approved, not expired)
3. Verify compensating controls are active
4. Block deployment if exception missing or expired

### During Deployment

Monitor for:
- Exception expiry during deployment
- Compensating control failures
- Policy violations

### Post-Deployment

Track:
- Exception effectiveness
- Compensating control compliance
- Exception renewal requirements

---

## References

- [Risk Model](./risk-model.md)
- [CAB Workflow](./cab-workflow.md)
- [Evidence Pack Schema](./evidence-pack-schema.md)
- [Security & Compliance](../infrastructure/secrets-management.md)

