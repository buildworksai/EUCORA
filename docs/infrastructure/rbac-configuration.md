# RBAC Configuration

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview

This document defines the **Role-Based Access Control (RBAC)** model for the Enterprise Endpoint Application Packaging & Deployment Factory. RBAC enforces **Separation of Duties (SoD)** to ensure that Packaging ≠ Publishing ≠ Approval.

**Design Principle**: Separation of duties — no shared credentials, no role escalation, scoped access by BU/acquisition boundary.

---

## RBAC Roles

### 1. Platform Admin

**Responsibilities**:
- Platform configuration and infrastructure management
- Integration credentials and service principal management
- Policy configuration (risk model, promotion gates, CAB workflow)
- HA/DR management

**Access Boundaries**:
- Full Control Plane access (all APIs, all scopes)
- **NO direct Intune production write access** (SoD enforcement)
- Infrastructure management (Azure resources, databases, object storage)

**Entra ID Group**: `AAD-ControlPlane-PlatformAdmins`

**API Scopes**: `control-plane.admin`

**SoD Enforcement**:
- Platform Admins can configure connectors but cannot publish apps to production
- Service principal credentials for connectors are stored in vault with audit trail
- Any production publish action requires Publisher role (separate credentials)

---

### 2. Packaging Engineer

**Responsibilities**:
- Build/test/sign artifacts in Packaging Factory
- Generate SBOM and run vulnerability scans
- Publish to **staging only** (not production)
- Create Deployment Intents for CAB review

**Access Boundaries**:
- **NO Intune production write access** (cannot create/update app objects, assignments, or production groups)
- Read-only access to production for verification
- Write access to staging/test environments
- Read access to artifact store and evidence store

**Entra ID Group**: `AAD-ControlPlane-PackagingEngineers`

**API Scopes**: `control-plane.packaging`

**SoD Enforcement**:
- Packaging Engineers cannot publish to production — they can only prepare artifacts and submit for CAB approval
- Separate Entra ID group with no production write permissions on execution planes
- All production publish actions require Publisher role with separate credentials

---

### 3. Publisher

**Responsibilities**:
- Publishes **CAB-approved** artifacts to execution planes (Intune/Jamf/SCCM/Landscape/Ansible)
- Executes ring promotions after promotion gates pass
- Triggers rollback actions when needed

**Access Boundaries**:
- Production publish rights only (scoped by BU/acquisition boundary)
- **NO packaging or build access** (cannot modify artifacts)
- **NO CAB approval rights** (cannot approve own deployments)
- Scoped by acquisition boundary and business unit

**Entra ID Group**: `AAD-ControlPlane-Publishers-{BU}-{AcquisitionBoundary}`
- Example: `AAD-ControlPlane-Publishers-Finance-Acq001`
- Example: `AAD-ControlPlane-Publishers-HR-Acq002`

**API Scopes**: `control-plane.publisher.{bu}.{acq}`

**SoD Enforcement**:
- Publishers are a **separate, limited role** monitored and access-reviewed quarterly
- Preferably JIT (Just-In-Time) via Entra ID Privileged Identity Management (PIM)
- Publish actions require Control Plane correlation id + CAB approval record (for gated changes)
- Service principals for Publishers are scoped and rotated (90-day rotation policy)

**JIT Workflow (Recommended)**:
1. Publisher requests JIT access via PIM for specific BU/acquisition boundary
2. Approval required from Platform Admin or CAB Approver
3. Access granted for time-limited period (max 8 hours)
4. All publish actions logged to SIEM with JIT session id

---

### 4. CAB Approver

**Responsibilities**:
- Review evidence packs for high-risk (`Risk > 50`) or privileged deployments
- Approve/deny deployment requests with conditions
- Apply expiry dates and compensating controls
- Review exception requests

**Access Boundaries**:
- Read access to evidence packs and deployment intents
- Write access to approval records
- **NO publish rights** (cannot execute deployments)
- **NO packaging or build access**

**Entra ID Group**: `AAD-ControlPlane-CABApprovers`

**API Scopes**: `control-plane.cab-approver`

**SoD Enforcement**:
- CAB Approvers can approve but cannot publish (separate role)
- Approval records are immutable (stored in append-only event store)
- CAB Approvers cannot modify evidence packs after submission

---

### 5. Security Reviewer

**Responsibilities**:
- Approve exceptions (vulnerability, unsigned package, scope violation)
- Own SBOM/vulnerability scan policy
- Manage PKI controls (signing keys, notarization, APT repo signing)
- Review and approve security-related changes (risk model calibration, etc.)

**Access Boundaries**:
- SBOM/scan policy write access
- Exception approval write access
- Key lifecycle management (rotation, revocation)
- **NO publish rights**
- **NO packaging or build access** (can review but not modify)

**Entra ID Group**: `AAD-ControlPlane-SecurityReviewers`

**API Scopes**: `control-plane.security-reviewer`

**SoD Enforcement**:
- Security Reviewers can approve exceptions but cannot publish
- Exception records are immutable and linked to deployment intents for audit trail
- Key management operations logged to SIEM

---

### 6. Endpoint Operations

**Responsibilities**:
- Monitor telemetry and dashboards
- Trigger remediation workflows within scope
- Manage operational runbooks (incident response, rollback execution)
- Own Entra ID dynamic groups lifecycle
- Own ABM/ADE tokens + VPP licensing operations (Apple platform)

**Access Boundaries**:
- Read access to telemetry and deployment events
- Write access to remediation intents (within scope)
- Operational runbooks and playbooks
- **NO publish rights** (can trigger remediation but not new deployments)
- **NO CAB approval rights**

**Entra ID Group**: `AAD-ControlPlane-EndpointOps`

**API Scopes**: `control-plane.endpoint-ops`

**Ownership Clarity**:
- **Intune production app objects & assignments**: Publisher (accountable), Endpoint Ops (responsible for operational health/runbooks), Security (consulted for policy exceptions)
- **Entra ID dynamic groups lifecycle**: Endpoint Ops / Identity team (responsible) with change control; Publishers consume approved groups, do not create ad-hoc production groups
- **ABM/ADE tokens + VPP licensing operations**: Endpoint Ops (Apple platform owner) with documented renewal owners and operational runbooks

---

### 7. Auditor

**Responsibilities**:
- Read-only access to all events and evidence packs
- Generate audit reports and compliance evidence
- Investigate incidents and policy violations

**Access Boundaries**:
- Read-only access to immutable event store
- Read-only access to evidence packs
- **NO write access anywhere**

**Entra ID Group**: `AAD-ControlPlane-Auditors`

**API Scopes**: `control-plane.auditor`

**SoD Enforcement**:
- Auditors have no write access to prevent tampering with audit trail
- Event store is append-only and immutable

---

## RBAC Matrix

| Activity | Platform Admin | Packaging Engineer | Publisher | CAB Approver | Security Reviewer | Endpoint Ops | Auditor |
|---|---|---|---|---|---|---|---|
| **Configure Control Plane** | ✅ R | ❌ | ❌ | ❌ | C | ❌ | ❌ |
| **Manage infrastructure** | ✅ R | ❌ | ❌ | ❌ | C | ❌ | ❌ |
| **Build/sign artifacts** | ❌ | ✅ R | ❌ | ❌ | C | ❌ | ❌ |
| **Generate SBOM/scan** | ❌ | ✅ R | ❌ | ❌ | C | ❌ | ❌ |
| **Publish to staging** | ❌ | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Submit for CAB approval** | ❌ | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Approve high-risk deployments** | ❌ | C | C | ✅ A | C | C | ❌ |
| **Approve exceptions** | ❌ | C | C | C | ✅ A | C | ❌ |
| **Publish to production** | ❌ | ❌ | ✅ R | ❌ | ❌ | C | ❌ |
| **Execute ring promotions** | ❌ | ❌ | ✅ R | ❌ | ❌ | C | ❌ |
| **Trigger rollback** | ❌ | ❌ | ✅ R | ❌ | ❌ | C | ❌ |
| **Monitor telemetry** | C | C | C | C | C | ✅ R | ✅ R |
| **Trigger remediation** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ R | ❌ |
| **Manage signing keys** | C | C | C | C | ✅ R | C | ❌ |
| **Review audit events** | C | C | C | C | C | C | ✅ R |

**Legend**:
- **R** = Responsible (does the work)
- **A** = Accountable (approves/owns the outcome)
- **C** = Consulted (provides input)
- ✅ = Has access
- ❌ = No access

---

## Scope-Based Access Control

### Acquisition Boundary Scoping

Publishers are scoped by **acquisition boundary** to prevent cross-boundary deployments without CAB approval.

**Example Scopes**:
- `acq-001` (Original Company)
- `acq-002` (Acquisition A)
- `acq-003` (Acquisition B)

**Publisher Groups**:
- `AAD-ControlPlane-Publishers-Finance-Acq001` → Can publish to `bu-finance` + `acq-001` only
- `AAD-ControlPlane-Publishers-HR-Acq002` → Can publish to `bu-hr` + `acq-002` only

**Scope Validation** (enforced by Policy Engine):
```python
def validate_publisher_scope(deployment_intent, publisher):
    """Validate that publisher scope contains target scope."""
    target_scope = deployment_intent.target_scope
    publisher_scope = publisher.allowed_scope

    if not is_subset(target_scope, publisher_scope):
        raise PolicyViolation(
            f"Target scope {target_scope} exceeds publisher scope {publisher_scope}"
        )
```

---

## Service Principal Management

### Service Principals for Execution Plane Connectors

Each execution plane connector uses a **dedicated service principal** with scoped permissions.

**Service Principals**:
- `SP-ControlPlane-IntuneConnector`
- `SP-ControlPlane-JamfConnector`
- `SP-ControlPlane-SCCMConnector`
- `SP-ControlPlane-LandscapeConnector`
- `SP-ControlPlane-AnsibleConnector`

**Permissions** (example for Intune Connector):
- **Microsoft Graph API**: `DeviceManagementApps.ReadWrite.All`, `DeviceManagementConfiguration.ReadWrite.All`
- **Authentication**: Certificate-based (no client secrets)
- **Rotation Policy**: Certificates rotated every 90 days

**Credential Storage**:
- Certificates stored in **Azure Key Vault** with access policies
- Access to Key Vault logged to SIEM
- Certificate rotation automated via runbook (see [Key Management](key-management.md))

---

## How We Prevent Role Escalation

### 1. Separate Entra ID Groups

- **Packaging Engineers**: `AAD-ControlPlane-PackagingEngineers` (no production write access)
- **Publishers**: `AAD-ControlPlane-Publishers-{BU}-{AcqBoundary}` (scoped production write access)
- **Platform Admins**: `AAD-ControlPlane-PlatformAdmins` (infrastructure only, no production publish)

**Enforcement**:
- Entra ID Conditional Access policies enforce MFA for all roles
- PIM (Privileged Identity Management) enforces JIT access for Publishers
- Group membership changes logged to SIEM and reviewed quarterly

---

### 2. No Shared Service Principals

- Each connector has a dedicated service principal
- Publisher credentials are scoped by BU/acquisition boundary
- No service principal has both "packaging" and "publishing" permissions

**Enforcement**:
- Service principal permissions audited quarterly
- Least-privilege principle enforced (only required Graph API permissions)
- Certificate rotation policy (90 days) prevents long-lived credentials

---

### 3. Publish Actions Require Correlation ID + CAB Approval

- All publish actions require a valid `correlation_id` from a Deployment Intent
- High-risk (`Risk > 50`) or privileged deployments require `cab_approval_id` linkage
- Policy Engine validates CAB approval record before allowing publish action

**Enforcement**:
```python
def publish(deployment_intent, publisher):
    """Publish to execution plane with CAB enforcement."""
    # Validate correlation_id
    if not deployment_intent.correlation_id:
        raise PolicyViolation("Missing correlation_id")

    # Validate CAB approval for high-risk
    if deployment_intent.risk_score > 50 or deployment_intent.is_privileged:
        if not deployment_intent.cab_approval_id:
            raise PolicyViolation("CAB approval required for high-risk deployment")

        approval = get_approval_record(deployment_intent.cab_approval_id)
        if approval.decision != "approved":
            raise PolicyViolation("Deployment not approved by CAB")

        if approval.expiry < datetime.now():
            raise PolicyViolation("CAB approval expired")

    # Execute publish
    connector.publish(deployment_intent)
```

---

## Access Review Process

**Frequency**: Quarterly (Q1, Q2, Q3, Q4)

**Review Scope**:
- Entra ID group memberships (all roles)
- Service principal permissions (all connectors)
- JIT access logs (Publishers)
- Privileged action logs (Platform Admins, Security Reviewers)

**Review Workflow**:
1. **Platform Admin** exports Entra ID group memberships and service principal permissions
2. **Security Reviewer** reviews exports against current org chart and role definitions
3. **Security Reviewer** identifies anomalies (e.g., users with multiple conflicting roles, inactive users still in groups)
4. **Platform Admin** remediates anomalies (remove inactive users, fix role conflicts)
5. **Auditor** validates remediation and documents review in compliance report

**Compliance Evidence**:
- Access review report stored in `reports/access-reviews/{YYYY-QN}/access-review-report.md`
- Remediation actions logged to immutable event store
- Quarterly compliance attestation to CAB

---

## Emergency Access (Break-Glass)

**Scenario**: Control Plane unavailable, urgent production fix required.

**Break-Glass Accounts**:
- `AAD-ControlPlane-BreakGlass-01`
- `AAD-ControlPlane-BreakGlass-02`

**Permissions**:
- Full Control Plane access (Platform Admin + Publisher combined)
- **Highly audited** — all actions logged to SIEM with alerts

**Usage Policy**:
1. Break-glass accounts used **only** during declared incidents (P0/P1)
2. Activation requires **two-person authorization** (dual control)
3. Usage duration **time-limited** (max 4 hours)
4. Post-incident review **mandatory** within 24 hours
5. Credentials **rotated immediately** after use

**Audit Requirements**:
- All break-glass actions logged to immutable event store
- SIEM alerts sent to Security Reviewer + Platform Admin immediately
- Post-incident report submitted to CAB within 48 hours

**Credentials**:
- Break-glass credentials stored in **physical secure location** (safe, sealed envelope)
- Access to credentials logged (who opened envelope, when, reason)
- Credentials rotated after every use or every 90 days (whichever is sooner)

---

## SIEM Integration

**Privileged Actions Logged to SIEM**:
- All publish actions to production (with correlation_id, publisher, timestamp)
- All CAB approval decisions (with approver, decision, timestamp)
- All exception grants (with Security Reviewer, expiry, compensating controls)
- All break-glass account activations
- All service principal credential rotations
- All Entra ID group membership changes

**SIEM Alert Rules**:
- **Critical**: Break-glass account activation
- **High**: Failed publish attempt (policy violation)
- **High**: CAB approval denied (with reason)
- **Medium**: Service principal credential near expiry (< 14 days)
- **Low**: Entra ID group membership change

**SIEM Retention**: 2 years (or per enterprise compliance requirements)

---

## Entra ID Configuration

### Conditional Access Policies

**Policy 1**: Require MFA for All Control Plane Roles
- **Assignments**: All Entra ID groups (`AAD-ControlPlane-*`)
- **Conditions**: All cloud apps, all locations
- **Access controls**: Require MFA (Microsoft Authenticator or hardware token)

**Policy 2**: Require Compliant Device for Publishers
- **Assignments**: `AAD-ControlPlane-Publishers-*`
- **Conditions**: All cloud apps, all locations
- **Access controls**: Require MFA + Require device to be marked as compliant

**Policy 3**: Block Legacy Authentication
- **Assignments**: All Entra ID groups (`AAD-ControlPlane-*`)
- **Conditions**: All cloud apps, legacy authentication protocols
- **Access controls**: Block access

---

### Privileged Identity Management (PIM)

**Eligible Roles** (JIT activation required):
- `AAD-ControlPlane-Publishers-{BU}-{AcqBoundary}` (Publisher role)
- `AAD-ControlPlane-PlatformAdmins` (Platform Admin role)

**Activation Requirements**:
- MFA required
- Business justification required
- Approval required (by Platform Admin or CAB Approver)
- Maximum activation duration: 8 hours
- Periodic re-authentication: Every 4 hours

**Activation Notifications**:
- Notification sent to Security Reviewer + Platform Admin on activation
- Notification sent to user on expiration (30 min before)
- Activation events logged to SIEM

---

## Related Documentation

- [Architecture Overview](../architecture/architecture-overview.md)
- [Control Plane Design](../architecture/control-plane-design.md)
- [Key Management](key-management.md)
- [Secrets Management](secrets-management.md)
- [SIEM Integration](siem-integration.md)

---

**RBAC Configuration v1.0 — Subject to quarterly access reviews and refinement.**
