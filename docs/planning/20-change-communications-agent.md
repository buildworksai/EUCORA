# E11: Change Communications Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P2-High
**Sprint**: 11-12 (Weeks 21-24)
**Dependencies**: E8 (AI Workflows), E10 (CMDB Integration)
**ALM L2 Category**: Change Management

---

## Overview

The Change & Communications Agent ensures smooth change rollout, communication, and proper closure across ITSM, CMDB, and knowledge systems. It improves traceability and audit compliance while keeping stakeholders informed in real-time.

### Key Benefits

- Improves traceability and audit compliance
- Ensures stakeholders are kept informed in real-time
- Automates change record lifecycle management
- Reduces manual communication overhead

### Data Sources

- Intune, SCCM, SharePoint
- MCP Servers
- ServiceNow Change Management
- Email/Teams (notifications)

---

## Requirements

### 1. Change Record Integration

**ServiceNow Change Management**:
- Create change requests from deployment intents
- Update change records with deployment progress
- Close change records with evidence
- Link changes to affected CIs

**Change Types Supported**:
- Standard (pre-approved)
- Normal (CAB approval)
- Emergency (expedited)

### 2. Stakeholder Communication

**Notification Channels**:
- Email (SMTP/Exchange)
- Microsoft Teams
- Slack (optional)
- ServiceNow notifications

**Communication Templates**:
- Change scheduled notification
- Deployment started
- Deployment progress update
- Deployment completed
- Rollback initiated
- Change closed

### 3. Knowledge Base Updates

**Automatic Updates**:
- Create KB articles for common issues
- Update existing articles with new solutions
- Link deployments to relevant KB articles
- Generate post-implementation reviews

### 4. Audit Trail

**Tracked Events**:
- All communications sent
- Change record state transitions
- Stakeholder acknowledgments
- Evidence attachments

---

## Data Model

### Django Models

```python
# apps/change_communications/models.py

class ChangeRecord(TimeStampedModel, CorrelationIdModel):
    """Linked ServiceNow change record."""
    deployment_intent = models.ForeignKey('deployments.DeploymentIntent', on_delete=models.CASCADE)
    servicenow_number = models.CharField(max_length=50, unique=True)
    servicenow_sys_id = models.CharField(max_length=100)
    change_type = models.CharField(max_length=20)  # standard, normal, emergency
    state = models.CharField(max_length=50)  # new, assess, authorize, scheduled, implement, review, closed
    short_description = models.CharField(max_length=255)
    risk_level = models.CharField(max_length=20)
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True)
    actual_end = models.DateTimeField(null=True)
    close_code = models.CharField(max_length=50, null=True)
    close_notes = models.TextField(null=True)

class StakeholderGroup(TimeStampedModel):
    """Groups of stakeholders for communication."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    notification_channel = models.CharField(max_length=50)  # email, teams, slack
    channel_config = models.JSONField()  # email addresses, webhook URLs, etc.
    is_active = models.BooleanField(default=True)

class CommunicationTemplate(TimeStampedModel):
    """Templates for stakeholder communications."""
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50)  # scheduled, started, progress, completed, rollback, closed
    channel = models.CharField(max_length=50)
    subject_template = models.CharField(max_length=500)
    body_template = models.TextField()
    is_active = models.BooleanField(default=True)

class Communication(TimeStampedModel, CorrelationIdModel):
    """Record of sent communications."""
    change_record = models.ForeignKey(ChangeRecord, on_delete=models.CASCADE)
    template = models.ForeignKey(CommunicationTemplate, on_delete=models.SET_NULL, null=True)
    stakeholder_group = models.ForeignKey(StakeholderGroup, on_delete=models.SET_NULL, null=True)
    channel = models.CharField(max_length=50)
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent_at = models.DateTimeField()
    status = models.CharField(max_length=20)  # sent, delivered, failed
    error_message = models.TextField(null=True)

class KBArticleLink(TimeStampedModel):
    """Links between deployments and KB articles."""
    deployment_intent = models.ForeignKey('deployments.DeploymentIntent', on_delete=models.CASCADE)
    kb_article_number = models.CharField(max_length=50)
    kb_article_sys_id = models.CharField(max_length=100)
    link_type = models.CharField(max_length=50)  # created, updated, referenced
    created_by_agent = models.BooleanField(default=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "change_communications_workflow",
  "agent_type": "change_communications",
  "risk_level": "R2",
  "steps": [
    {
      "name": "create_change_record",
      "description": "Create ServiceNow change request from deployment intent",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review change record details before creation"
    },
    {
      "name": "identify_stakeholders",
      "description": "Identify affected stakeholders based on scope",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "send_scheduled_notification",
      "description": "Notify stakeholders of scheduled change",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "monitor_deployment",
      "description": "Monitor deployment progress and send updates",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "update_cmdb",
      "description": "Update CMDB with deployment results",
      "risk_level": "R2",
      "requires_approval": true
    },
    {
      "name": "generate_kb_article",
      "description": "Generate or update KB article if needed",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review KB article content before publishing"
    },
    {
      "name": "close_change_record",
      "description": "Close change record with evidence",
      "risk_level": "R2",
      "requires_approval": true
    },
    {
      "name": "send_closure_notification",
      "description": "Notify stakeholders of change closure",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "change_management_policy",
    "communication_standards"
  ]
}
```

---

## API Endpoints

```
# Change Records
GET/POST /api/change-communications/changes/
GET /api/change-communications/changes/{id}/
POST /api/change-communications/changes/{id}/sync/
POST /api/change-communications/changes/{id}/close/

# Stakeholder Groups
GET/POST /api/change-communications/stakeholders/
GET/PUT/DELETE /api/change-communications/stakeholders/{id}/

# Communication Templates
GET/POST /api/change-communications/templates/
GET/PUT/DELETE /api/change-communications/templates/{id}/
POST /api/change-communications/templates/{id}/preview/

# Communications
GET /api/change-communications/communications/
POST /api/change-communications/send/

# KB Articles
GET /api/change-communications/kb-articles/
POST /api/change-communications/kb-articles/generate/
```

---

## Frontend Components

### 1. Change Communications Dashboard

```
Change Management > Communications
├── Active Changes
│   ├── Change cards with status
│   ├── Deployment progress
│   └── Quick actions
├── Communication Queue
│   ├── Pending notifications
│   ├── Recently sent
│   └── Failed (retry option)
├── KB Articles
│   ├── Recently generated
│   └── Pending review
└── Metrics
    ├── Changes this week
    ├── Communications sent
    └── Stakeholder reach
```

### 2. Change Record Detail

```
Change Record CHG0012345
├── Header (number, state, risk)
├── Deployment Link
├── Timeline
│   ├── Created
│   ├── Scheduled notification sent
│   ├── Deployment started
│   ├── Progress updates
│   └── Closed
├── Stakeholders
│   ├── Groups notified
│   └── Communication history
├── Evidence
│   ├── Attached files
│   └── CMDB updates
└── Actions
    ├── Send notification
    ├── Update status
    └── Close change
```

### 3. Stakeholder Group Management

```
Settings > Stakeholder Groups
├── Group list
├── Create/Edit Group
│   ├── Name and description
│   ├── Channel selection
│   ├── Channel configuration
│   │   ├── Email: addresses
│   │   ├── Teams: webhook URL
│   │   └── Slack: channel
│   └── Test notification
└── Scope mapping (which groups for which deployments)
```

---

## Communication Templates

### Example: Deployment Scheduled

```
Subject: [EUCORA] Change ${change_number} Scheduled: ${application_name} v${version}

Body:
A change has been scheduled for ${application_name}.

**Change Details:**
- Change Number: ${change_number}
- Application: ${application_name}
- Version: ${version}
- Scheduled Start: ${planned_start}
- Scheduled End: ${planned_end}
- Affected Devices: ${device_count}

**Description:**
${short_description}

**Impact:**
${impact_description}

Please reach out to ${contact_email} if you have any questions.

---
This is an automated notification from EUCORA.
```

---

## Acceptance Criteria

- [ ] ServiceNow change record creation/update
- [ ] Stakeholder groups configurable
- [ ] Communication templates working
- [ ] Email notifications functional
- [ ] Teams notifications functional
- [ ] KB article generation
- [ ] Change record lifecycle management
- [ ] Full audit trail
- [ ] ≥90% test coverage
