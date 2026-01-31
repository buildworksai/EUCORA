# E15: IAM Security Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P2-High
**Sprint**: 13-14 (Weeks 25-28)
**Dependencies**: E3 (RBAC), E7 (pgvector), E8 (AI Workflows)
**ALM L2 Category**: Service Catalog / Identity and Access Management (IDAM)

---

## Overview

The IAM Agent runs autonomously and alerts security admins to anomalies related to accessing enterprise applications. It is always on—checking access logs and reviewing permission lists—and surfaces insights to the Support team on potential problematic trends and incidents.

### Key Benefits

- Always-on agent checking access logs
- Reviews permission lists for anomalies
- Surfaces insights on problematic trends
- Early detection of security incidents

### Data Sources

- Azure AD / Entra ID
- Okta
- ServiceNow
- Internal IAM logs

---

## Requirements

### 1. Identity Provider Integration

**Supported Providers**:
- Microsoft Entra ID (Azure AD)
- Okta
- ServiceNow IAM
- On-premises Active Directory

**Data Collected**:
- Sign-in logs
- Audit logs
- Permission changes
- Group memberships
- Application access grants

### 2. Anomaly Detection

**Detection Types**:
- Unusual login patterns (time, location, device)
- Privilege escalation
- Dormant account access
- Excessive permission grants
- Access from new devices/locations
- Failed authentication patterns
- Service account anomalies

### 3. Permission Review

**Analysis**:
- Over-privileged users
- Stale permissions
- Separation of duties violations
- Orphaned access grants
- Group membership anomalies

### 4. Alerting & Response

**Alert Channels**:
- Email notifications
- Teams/Slack integration
- ServiceNow incident creation
- SIEM integration

**Response Actions (R2/R3)**:
- Disable account (R3)
- Revoke permissions (R2)
- Force password reset (R2)
- Block sign-in (R3)

---

## Data Model

### Django Models

```python
# apps/iam_security/models.py

class IdentityProvider(TimeStampedModel):
    """Configured identity provider."""
    name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=50)  # entra_id, okta, ad, servicenow
    tenant_id = models.CharField(max_length=255, null=True)
    connection_config = models.JSONField()
    sync_interval_minutes = models.IntegerField(default=15)
    last_sync = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

class SignInEvent(TimeStampedModel):
    """Captured sign-in event."""
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=255, unique=True)
    user_principal = models.CharField(max_length=255)
    user_display_name = models.CharField(max_length=255)
    app_display_name = models.CharField(max_length=255, null=True)
    client_ip = models.GenericIPAddressField(null=True)
    location = models.JSONField(null=True)
    device_detail = models.JSONField(null=True)
    status = models.CharField(max_length=20)  # success, failure
    failure_reason = models.CharField(max_length=255, null=True)
    risk_level = models.CharField(max_length=20, null=True)
    event_time = models.DateTimeField()

class PermissionChange(TimeStampedModel):
    """Captured permission/role change."""
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=255, unique=True)
    actor_principal = models.CharField(max_length=255)
    target_principal = models.CharField(max_length=255)
    change_type = models.CharField(max_length=50)  # add, remove, modify
    resource_type = models.CharField(max_length=50)  # role, group, permission, app_access
    resource_name = models.CharField(max_length=255)
    old_value = models.JSONField(null=True)
    new_value = models.JSONField(null=True)
    event_time = models.DateTimeField()

class AnomalyDetection(TimeStampedModel, CorrelationIdModel):
    """Detected security anomaly."""
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE)
    anomaly_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)  # low, medium, high, critical
    user_principal = models.CharField(max_length=255)
    description = models.TextField()
    evidence = models.JSONField()
    related_events = models.JSONField(default=list)  # event IDs
    detection_rule = models.CharField(max_length=255)
    status = models.CharField(max_length=20)  # new, investigating, resolved, false_positive
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True)
    resolution_notes = models.TextField(null=True)

class DetectionRule(TimeStampedModel):
    """Anomaly detection rules."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    anomaly_type = models.CharField(max_length=50)
    severity = models.CharField(max_length=20)
    rule_config = models.JSONField()
    threshold_config = models.JSONField()
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True)
    trigger_count = models.IntegerField(default=0)

class SecurityAlert(TimeStampedModel, CorrelationIdModel):
    """Security alert sent to stakeholders."""
    anomaly = models.ForeignKey(AnomalyDetection, on_delete=models.CASCADE)
    channel = models.CharField(max_length=50)  # email, teams, servicenow
    recipients = models.JSONField()
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=20)  # sent, delivered, failed
```

---

## Agent Workflow Definition

```json
{
  "name": "iam_security_workflow",
  "agent_type": "iam_security",
  "risk_level": "R2",
  "is_continuous": true,
  "poll_interval_minutes": 15,
  "steps": [
    {
      "name": "collect_events",
      "description": "Collect sign-in and audit events from identity providers",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "analyze_patterns",
      "description": "Analyze events for anomalous patterns",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "detect_anomalies",
      "description": "Apply detection rules and identify anomalies",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "assess_severity",
      "description": "Assess severity and priority of detected anomalies",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_alerts",
      "description": "Generate and send security alerts",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "recommend_response",
      "description": "Recommend response actions for critical anomalies",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review and approve security response action"
    },
    {
      "name": "execute_response",
      "description": "Execute approved response actions",
      "risk_level": "R3",
      "requires_approval": true,
      "approval_context": "CRITICAL: Confirm security action execution"
    }
  ],
  "policy_requirements": [
    "security_policy",
    "access_control_policy"
  ]
}
```

---

## Detection Rules

### Built-in Rules

```python
DETECTION_RULES = [
    {
        "name": "impossible_travel",
        "description": "Sign-ins from geographically distant locations in short time",
        "anomaly_type": "suspicious_login",
        "severity": "high",
        "config": {
            "max_speed_kmh": 1000,  # Faster than commercial flight
            "min_events": 2
        }
    },
    {
        "name": "brute_force_attempt",
        "description": "Multiple failed sign-in attempts",
        "anomaly_type": "authentication_attack",
        "severity": "high",
        "config": {
            "failure_threshold": 10,
            "time_window_minutes": 30
        }
    },
    {
        "name": "unusual_hour_access",
        "description": "Access outside normal working hours",
        "anomaly_type": "unusual_activity",
        "severity": "medium",
        "config": {
            "normal_hours_start": 7,
            "normal_hours_end": 20,
            "timezone": "user_timezone"
        }
    },
    {
        "name": "new_device_access",
        "description": "Access from a new device",
        "anomaly_type": "new_device",
        "severity": "low",
        "config": {
            "lookback_days": 90
        }
    },
    {
        "name": "privilege_escalation",
        "description": "User granted elevated privileges",
        "anomaly_type": "privilege_change",
        "severity": "high",
        "config": {
            "sensitive_roles": ["Global Administrator", "Security Administrator"]
        }
    },
    {
        "name": "dormant_account_activation",
        "description": "Account inactive for extended period now active",
        "anomaly_type": "dormant_activation",
        "severity": "medium",
        "config": {
            "dormant_days": 90
        }
    },
    {
        "name": "service_account_interactive",
        "description": "Service account used for interactive sign-in",
        "anomaly_type": "service_account_abuse",
        "severity": "critical",
        "config": {
            "service_account_patterns": ["svc-*", "*-service", "SA_*"]
        }
    }
]
```

---

## API Endpoints

```
# Identity Providers
GET/POST /api/iam-security/providers/
GET/PUT/DELETE /api/iam-security/providers/{id}/
POST /api/iam-security/providers/{id}/test/
POST /api/iam-security/providers/{id}/sync/

# Events
GET /api/iam-security/sign-ins/
GET /api/iam-security/permission-changes/

# Anomalies
GET /api/iam-security/anomalies/
GET /api/iam-security/anomalies/{id}/
POST /api/iam-security/anomalies/{id}/investigate/
POST /api/iam-security/anomalies/{id}/resolve/
POST /api/iam-security/anomalies/{id}/false-positive/

# Detection Rules
GET/POST /api/iam-security/rules/
GET/PUT/DELETE /api/iam-security/rules/{id}/
POST /api/iam-security/rules/{id}/test/

# Alerts
GET /api/iam-security/alerts/

# Response Actions
POST /api/iam-security/actions/disable-account/
POST /api/iam-security/actions/revoke-permissions/
POST /api/iam-security/actions/force-password-reset/

# Reports
GET /api/iam-security/reports/summary/
GET /api/iam-security/reports/trends/
```

---

## Frontend Components

### 1. IAM Security Dashboard

```
AI Agents > IAM Security
├── Threat Summary
│   ├── Active anomalies by severity
│   ├── Trend sparklines
│   └── Last 24h events
├── Anomaly Queue
│   ├── Critical (requires immediate action)
│   ├── High priority
│   ├── Under investigation
│   └── Quick actions
├── Activity Timeline
│   ├── Recent events
│   ├── Detection triggers
│   └── Response actions taken
├── User Risk Scores
│   ├── Highest risk users
│   └── Risk trend
└── Agent Status
    ├── Running / Paused
    ├── Last check
    └── Providers connected
```

### 2. Anomaly Investigation

```
Anomaly: Impossible Travel - john.doe@company.com
├── Header
│   ├── Severity: HIGH
│   ├── Status: Investigating
│   └── Assigned to: Security Team
├── Summary
│   ├── User: John Doe
│   ├── Detection time
│   └── Rule triggered
├── Evidence
│   ├── Event 1: New York, 10:00 AM
│   ├── Event 2: London, 10:15 AM
│   ├── Distance: 5,500 km
│   └── Impossible without teleportation
├── User Context
│   ├── Role and permissions
│   ├── Recent activity
│   └── Risk history
├── Related Events
│   ├── Other sign-ins
│   ├── Permission changes
│   └── Failed attempts
└── Actions
    ├── Mark as investigating
    ├── Resolve (legitimate)
    ├── Mark false positive
    ├── Disable account (R3)
    └── Force password reset (R2)
```

### 3. Detection Rules Management

```
Settings > IAM Security > Detection Rules
├── Built-in Rules
│   ├── Impossible travel ✓
│   ├── Brute force ✓
│   ├── Unusual hours ✓
│   └── ...
├── Custom Rules
│   ├── Add custom rule
│   └── Rule editor
├── Rule Configuration
│   ├── Enable/disable
│   ├── Severity override
│   ├── Threshold tuning
│   └── Test rule
└── Alert Configuration
    ├── Recipients by severity
    └── Channels
```

---

## Entra ID Integration

```python
class EntraIDClient:
    """Client for Microsoft Entra ID (Azure AD)."""

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.graph_url = "https://graph.microsoft.com/v1.0"

    async def get_sign_in_logs(self, since: datetime) -> list[dict]:
        """Get sign-in audit logs."""
        # GET /auditLogs/signIns

    async def get_directory_audit(self, since: datetime) -> list[dict]:
        """Get directory audit logs."""
        # GET /auditLogs/directoryAudits

    async def get_risky_users(self) -> list[dict]:
        """Get users flagged as risky."""
        # GET /identityProtection/riskyUsers

    async def disable_user(self, user_id: str) -> bool:
        """Disable user account."""
        # PATCH /users/{id} { accountEnabled: false }

    async def revoke_sessions(self, user_id: str) -> bool:
        """Revoke all refresh tokens."""
        # POST /users/{id}/revokeSignInSessions
```

---

## Acceptance Criteria

- [ ] Entra ID integration working
- [ ] Sign-in log collection
- [ ] Permission change tracking
- [ ] Anomaly detection rules
- [ ] Real-time alerting
- [ ] Investigation workflow
- [ ] Response actions (with approval)
- [ ] Risk scoring
- [ ] Dashboard with trends
- [ ] ≥90% test coverage
