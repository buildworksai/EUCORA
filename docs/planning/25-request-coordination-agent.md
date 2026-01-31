# E16: Request Communication & Coordination Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P3-Medium
**Sprint**: 15-16 (Weeks 29-32)
**Dependencies**: E8 (AI Workflows), E10 (CMDB), E11 (Change Communications)
**ALM L2 Category**: Service Request Management

---

## Overview

The Request Communication & Coordination Agent manages status updates, escalations, and coordination across stakeholders for non-standard or delayed requests. It ensures requestors are kept informed at all times and provides transparency to management with real-time dashboards.

### Key Benefits

- Reduces manual follow-ups and status chasing
- Ensures requestors are kept informed at all times
- Provides transparency to management with real-time dashboards
- Automates escalation workflows

### Data Sources

- ServiceNow
- Word Templates
- Technical Specs (PDFs)
- Email/Teams

---

## Requirements

### 1. Request Tracking

**Request Types**:
- Software installation requests
- Access requests
- Hardware requests
- Configuration changes
- Exception requests

**Tracking Data**:
- Request status
- Assigned team/person
- SLA deadlines
- Blockers/dependencies
- Stakeholder list

### 2. Communication Automation

**Automated Updates**:
- Status change notifications
- SLA warning notifications
- Escalation notifications
- Completion notifications
- Weekly digest

**Channels**:
- Email
- Microsoft Teams
- ServiceNow notifications
- Slack (optional)

### 3. Escalation Management

**Triggers**:
- SLA breach approaching
- SLA breached
- Blocked for X days
- Multiple reassignments
- Customer complaint

**Actions**:
- Notify manager
- Notify escalation chain
- Create incident (for major issues)
- Update priority

### 4. Reporting

**Dashboards**:
- Open requests by status
- SLA compliance rates
- Average resolution time
- Escalation trends
- Team workload

---

## Data Model

### Django Models

```python
# apps/request_coordination/models.py

class TrackedRequest(TimeStampedModel, CorrelationIdModel):
    """ServiceNow request being tracked."""
    servicenow_number = models.CharField(max_length=50, unique=True)
    servicenow_sys_id = models.CharField(max_length=100)
    request_type = models.CharField(max_length=50)
    short_description = models.CharField(max_length=255)
    requestor_email = models.EmailField()
    requestor_name = models.CharField(max_length=255)
    assigned_to = models.CharField(max_length=255, null=True)
    assignment_group = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=50)
    priority = models.CharField(max_length=20)
    sla_due = models.DateTimeField(null=True)
    is_escalated = models.BooleanField(default=False)
    escalation_level = models.IntegerField(default=0)
    last_updated = models.DateTimeField()
    blocked_reason = models.TextField(null=True)

class RequestStakeholder(TimeStampedModel):
    """Stakeholder interested in a request."""
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE)
    email = models.EmailField()
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=50)  # requestor, approver, watcher, manager
    notification_preferences = models.JSONField(default=dict)

class RequestStatusUpdate(TimeStampedModel):
    """Status update for a tracked request."""
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=50)
    new_status = models.CharField(max_length=50)
    update_notes = models.TextField(null=True)
    updated_by = models.CharField(max_length=255)

class RequestCommunication(TimeStampedModel, CorrelationIdModel):
    """Communication sent for a request."""
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE)
    communication_type = models.CharField(max_length=50)  # status_update, sla_warning, escalation, completion
    channel = models.CharField(max_length=50)
    recipients = models.JSONField()
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=20)

class EscalationRule(TimeStampedModel):
    """Rules for automatic escalation."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    request_type = models.CharField(max_length=50, null=True)  # null = all types
    trigger_type = models.CharField(max_length=50)  # sla_warning, sla_breach, blocked, reassignment
    trigger_config = models.JSONField()
    escalation_actions = models.JSONField()
    is_active = models.BooleanField(default=True)

class EscalationEvent(TimeStampedModel, CorrelationIdModel):
    """Record of escalation triggered."""
    request = models.ForeignKey(TrackedRequest, on_delete=models.CASCADE)
    rule = models.ForeignKey(EscalationRule, on_delete=models.SET_NULL, null=True)
    trigger_reason = models.TextField()
    escalation_level = models.IntegerField()
    actions_taken = models.JSONField()
    resolved_at = models.DateTimeField(null=True)

class CommunicationTemplate(TimeStampedModel):
    """Templates for request communications."""
    name = models.CharField(max_length=255)
    communication_type = models.CharField(max_length=50)
    channel = models.CharField(max_length=50)
    subject_template = models.CharField(max_length=500)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "request_coordination_workflow",
  "agent_type": "request_coordination",
  "risk_level": "R1",
  "is_continuous": true,
  "poll_interval_minutes": 30,
  "steps": [
    {
      "name": "sync_requests",
      "description": "Sync request status from ServiceNow",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "check_sla_status",
      "description": "Check SLA status for all tracked requests",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "detect_status_changes",
      "description": "Detect requests with status changes since last check",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "identify_blocked",
      "description": "Identify blocked or stalled requests",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "send_updates",
      "description": "Send status update notifications to stakeholders",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "trigger_escalations",
      "description": "Trigger escalations based on rules",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review escalation before notifying management"
    },
    {
      "name": "generate_digest",
      "description": "Generate periodic digest for managers",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "sla_policy",
    "escalation_policy"
  ]
}
```

---

## API Endpoints

```
# Tracked Requests
GET /api/request-coordination/requests/
GET /api/request-coordination/requests/{id}/
POST /api/request-coordination/requests/sync/
GET /api/request-coordination/requests/{id}/timeline/

# Stakeholders
GET/POST /api/request-coordination/requests/{id}/stakeholders/
DELETE /api/request-coordination/requests/{id}/stakeholders/{stakeholder_id}/

# Communications
GET /api/request-coordination/communications/
POST /api/request-coordination/send/

# Escalation Rules
GET/POST /api/request-coordination/escalation-rules/
GET/PUT/DELETE /api/request-coordination/escalation-rules/{id}/

# Escalation Events
GET /api/request-coordination/escalations/
POST /api/request-coordination/escalations/{id}/resolve/

# Templates
GET/POST /api/request-coordination/templates/
GET/PUT/DELETE /api/request-coordination/templates/{id}/

# Reports
GET /api/request-coordination/reports/sla-compliance/
GET /api/request-coordination/reports/workload/
GET /api/request-coordination/reports/trends/
```

---

## Frontend Components

### 1. Request Coordination Dashboard

```
AI Agents > Request Coordination
├── Summary Cards
│   ├── Open requests
│   ├── SLA at risk
│   ├── Escalated
│   └── Completed today
├── Request Queue
│   ├── Critical (SLA breached/at risk)
│   ├── Blocked
│   ├── Awaiting response
│   └── All open
├── SLA Compliance
│   ├── Compliance % gauge
│   ├── Trend chart
│   └── By request type
├── Escalation Queue
│   ├── Active escalations
│   ├── Recent escalations
│   └── Quick resolve
└── Team Workload
    ├── Requests by assignee
    └── Average resolution time
```

### 2. Request Detail

```
Request: REQ0045678 - Software Installation
├── Header
│   ├── Status: In Progress
│   ├── Priority: Medium
│   ├── SLA Due: 2 hours remaining
│   └── Escalation: None
├── Summary
│   ├── Requestor: Jane Smith
│   ├── Description
│   ├── Assigned to: IT Support
│   └── Created: 2 days ago
├── Timeline
│   ├── Created
│   ├── Assigned
│   ├── Status update sent
│   ├── Blocked - awaiting approval
│   └── Resumed
├── Stakeholders
│   ├── Jane Smith (requestor)
│   ├── Manager: John Doe (watcher)
│   └── Add stakeholder
├── Communications
│   ├── Sent messages
│   └── Send update
└── Actions
    ├── Sync status
    ├── Send update
    ├── Escalate
    └── Mark complete
```

### 3. Escalation Rules Management

```
Settings > Request Coordination > Escalation Rules
├── Active Rules
│   ├── SLA Warning (4h before breach)
│   ├── SLA Breach (immediate)
│   ├── Blocked > 2 days
│   └── Multiple reassignments
├── Add Rule
│   ├── Name
│   ├── Request type (optional)
│   ├── Trigger type
│   ├── Trigger configuration
│   ├── Actions
│   │   ├── Notify manager
│   │   ├── Notify escalation chain
│   │   ├── Update priority
│   │   └── Create incident
│   └── Save
└── Rule History
    ├── Recent triggers
    └── Effectiveness metrics
```

---

## Communication Templates

### SLA Warning Template

```
Subject: ⚠️ SLA Warning: ${request_number} - ${short_description}

Body:
The following request is approaching its SLA deadline:

**Request Details:**
- Number: ${request_number}
- Description: ${short_description}
- Requestor: ${requestor_name}
- Assigned to: ${assigned_to}
- SLA Due: ${sla_due}
- Time Remaining: ${time_remaining}

**Current Status:** ${status}

Please take action to ensure this request is resolved before the SLA deadline.

---
This is an automated notification from EUCORA Request Coordination.
```

### Escalation Template

```
Subject: 🔴 ESCALATION: ${request_number} - ${escalation_reason}

Body:
A request has been escalated and requires management attention:

**Request Details:**
- Number: ${request_number}
- Description: ${short_description}
- Requestor: ${requestor_name}
- Assigned to: ${assigned_to}

**Escalation Reason:** ${escalation_reason}

**Timeline:**
${timeline_summary}

**Recommended Action:** ${recommended_action}

---
This is an automated escalation from EUCORA Request Coordination.
```

---

## Escalation Rule Examples

```python
ESCALATION_RULES = [
    {
        "name": "SLA Warning - 4 Hours",
        "trigger_type": "sla_warning",
        "trigger_config": {
            "hours_before_breach": 4
        },
        "actions": [
            {"type": "notify", "recipients": ["assigned_to", "assignment_group_manager"]},
            {"type": "update_priority", "new_priority": "high"}
        ]
    },
    {
        "name": "SLA Breach",
        "trigger_type": "sla_breach",
        "trigger_config": {},
        "actions": [
            {"type": "notify", "recipients": ["escalation_chain"]},
            {"type": "escalate", "level": 1}
        ]
    },
    {
        "name": "Blocked > 2 Days",
        "trigger_type": "blocked",
        "trigger_config": {
            "blocked_days": 2
        },
        "actions": [
            {"type": "notify", "recipients": ["requestor", "assignment_group_manager"]},
            {"type": "add_work_note", "note": "Request has been blocked for ${blocked_days} days."}
        ]
    },
    {
        "name": "Multiple Reassignments",
        "trigger_type": "reassignment",
        "trigger_config": {
            "reassignment_count": 3,
            "time_window_hours": 48
        },
        "actions": [
            {"type": "notify", "recipients": ["requestor", "service_owner"]},
            {"type": "escalate", "level": 1}
        ]
    }
]
```

---

## Acceptance Criteria

- [ ] ServiceNow request sync
- [ ] Status change detection
- [ ] Stakeholder management
- [ ] SLA tracking and warnings
- [ ] Automated notifications
- [ ] Escalation rules engine
- [ ] Escalation workflow
- [ ] Management dashboard
- [ ] Communication templates
- [ ] ≥90% test coverage
