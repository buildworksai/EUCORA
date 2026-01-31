# Request Coordination Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The Request Coordination Agent helps service desk teams track ServiceNow requests, monitor SLA compliance, manage escalations, and coordinate stakeholder communications. It ensures requests are handled efficiently and within SLA targets.

## Key Features

- **Request Tracking**: Syncs and tracks ServiceNow requests
- **SLA Monitoring**: Monitors request SLA compliance in real-time
- **Escalation Management**: Automated escalation based on SLA breaches and rules
- **Stakeholder Communications**: Sends status updates via Email, Teams, Slack, and ServiceNow
- **Request Coordination**: Coordinates multi-stakeholder requests

## Getting Started

### Accessing the Agent

1. Navigate to **Request Coordination** from the main dashboard
2. You'll see the Coordination Dashboard with active requests, SLA status, and escalations

### Prerequisites

- ServiceNow access for request sync
- Request Coordination Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Viewing Tracked Requests

**Step 1**: Navigate to **Requests** tab
**Step 2**: View request list with:
- ServiceNow number
- Request type
- Status and priority
- SLA due date
- Escalation status

**Step 3**: Filter by:
- Status (New, In Progress, Pending, Resolved, Closed)
- Priority (Critical, High, Medium, Low)
- Request type
- SLA status

**Step 4**: Click on request to view details

### 2. Adding Stakeholders

**Step 1**: Go to request details
**Step 2**: Navigate to **Stakeholders** tab
**Step 3**: Click **Add Stakeholder**
**Step 4**: Enter stakeholder details:
- Email address
- Name
- Role (Requestor, Approver, Reviewer, etc.)
- Notification preferences

**Step 5**: Save stakeholder
**Step 6**: Stakeholder receives automatic updates

### 3. Sending Communications

**Step 1**: Go to request details
**Step 2**: Navigate to **Communications** tab
**Step 3**: Click **Send Communication**
**Step 4**: Select:
- Communication template
- Channel (Email, Teams, Slack, ServiceNow)
- Recipients (stakeholders or custom)

**Step 5**: Review message preview
**Step 6**: Send communication
**Step 7**: Track delivery status

### 4. Managing Escalations

**View Escalations**:
1. Go to **Escalations** tab
2. View escalation list:
   - Request number
   - Escalation level
   - Escalation reason
   - Escalated at time

**Resolve Escalation**:
1. Select escalation
2. Review escalation details
3. Take corrective action
4. Mark escalation as resolved
5. Add resolution notes

### 5. Configuring Escalation Rules

**Step 1**: Navigate to **Escalation Rules** tab
**Step 2**: Click **Create Rule**
**Step 3**: Configure rule:
- Name and description
- Trigger condition:
  - SLA breach
  - Status change
  - Manual trigger
- Escalation level
- Notification settings

**Step 4**: Save and activate rule
**Step 5**: Rule triggers automatically when conditions are met

### 6. Monitoring SLA Compliance

**Step 1**: Go to **Requests** tab
**Step 2**: View SLA indicators:
- Green: On track
- Yellow: At risk
- Red: Breached

**Step 3**: Filter by SLA status:
- At risk requests
- Breached requests
- On track requests

**Step 4**: Take action on at-risk requests:
- Escalate if needed
- Update stakeholders
- Prioritize resolution

### 7. Viewing Coordination Reports

**Step 1**: Navigate to **Reports** → **Summary**
**Step 2**: Review summary statistics:
- Total requests
- Active requests
- Escalated requests
- SLA breaches

**Step 3**: View request trends:
- Requests by type
- Average resolution time
- SLA compliance rate
- Escalation frequency

## Configuration Options

### Communication Templates

- **Template Types**: Change notification, reminder, completion
- **Channel Support**: Email, Teams, Slack, ServiceNow
- **Variables**: Use variables for dynamic content

### Escalation Configuration

- **SLA Thresholds**: Configure when to escalate (e.g., 80% of SLA elapsed)
- **Escalation Levels**: Define escalation hierarchy
- **Notification Rules**: Configure who gets notified at each level

### Stakeholder Management

- **Default Stakeholders**: Auto-add stakeholders based on request type
- **Notification Preferences**: Configure per-stakeholder preferences
- **Role-Based Access**: Control stakeholder visibility

## Best Practices

1. **Monitor SLA Status Regularly**: Check at-risk requests daily
2. **Keep Stakeholders Informed**: Send regular status updates
3. **Escalate Early**: Don't wait for SLA breach to escalate
4. **Use Templates**: Standardize communications with templates
5. **Track Escalations**: Document escalation reasons and resolutions
6. **Review Rules**: Regularly review and update escalation rules

## Troubleshooting

### Request Sync Issues

**Problem**: Requests not syncing from ServiceNow
**Solution**: Verify ServiceNow connection and sync schedule

**Problem**: Request status not updating
**Solution**: Check sync frequency and ServiceNow API access

### Communication Issues

**Problem**: Communications not sending
**Solution**: Verify channel configuration and credentials

**Problem**: Stakeholders not receiving updates
**Solution**: Check notification preferences and email addresses

### Escalation Issues

**Problem**: Escalations not triggering
**Solution**: Verify escalation rules and trigger conditions

**Problem**: Escalation notifications not sent
**Solution**: Check notification configuration and stakeholder assignments

## Related Documentation

- [Request Coordination API Reference](../api/request-coordination-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/25-request-coordination-agent.md)
