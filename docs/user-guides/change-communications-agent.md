# Change Communications Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The Change Communications Agent helps application managers coordinate change communications by managing ServiceNow change records, sending stakeholder notifications, and tracking communication delivery. It ensures stakeholders are informed about changes that affect them.

## Key Features

- **Change Record Management**: Syncs and tracks ServiceNow change records
- **Stakeholder Management**: Manages stakeholder groups and notification preferences
- **Multi-Channel Communications**: Sends notifications via Email, Teams, Slack, and ServiceNow
- **Communication Templates**: Uses templates for consistent messaging
- **KB Article Linking**: Links knowledge base articles to change communications

## Getting Started

### Accessing the Agent

1. Navigate to **Change Communications** from the main dashboard
2. You'll see the Communications Dashboard with active changes, scheduled communications, and delivery status

### Prerequisites

- ServiceNow change management access
- Change Communications Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Viewing Change Records

**Step 1**: Navigate to **Changes** tab
**Step 2**: View change list with:
- ServiceNow change number
- Short description
- State (New, Assess, Authorize, Scheduled, Implement, Review, Closed)
- Priority and risk
- Scheduled dates

**Step 3**: Filter by:
- State
- Priority (Low, Medium, High, Critical)
- Risk level
- Scheduled date range

**Step 4**: Click on change to view details

### 2. Managing Stakeholder Groups

**Step 1**: Go to **Stakeholders** tab
**Step 2**: Click **Create Group**
**Step 3**: Enter group details:
- Name and description
- Member email addresses
- Group type (IT, Business, End Users, etc.)

**Step 4**: Save group
**Step 5**: Groups can be assigned to changes for notifications

### 3. Creating Communication Templates

**Step 1**: Navigate to **Templates** tab
**Step 2**: Click **Create Template**
**Step 3**: Configure template:
- Name and template type:
  - Change Notification
  - Change Reminder
  - Change Completed
- Channel (Email, Teams, Slack)
- Subject line
- Body content (use variables for dynamic content)

**Step 4**: Preview template
**Step 5**: Save template

### 4. Sending Change Notifications

**Step 1**: Go to change details
**Step 2**: Navigate to **Communications** tab
**Step 3**: Click **Send Communication**
**Step 4**: Select:
- Communication template
- Channel (Email, Teams, Slack, ServiceNow)
- Recipients:
  - Stakeholder groups
  - Individual recipients
  - Custom list

**Step 5**: Review message preview
**Step 6**: Send communication
**Step 7**: Track delivery status

### 5. Linking KB Articles

**Step 1**: Go to change details
**Step 2**: Navigate to **KB Articles** tab
**Step 3**: Click **Link Article**
**Step 4**: Search for knowledge base article
**Step 5**: Select article
**Step 6**: Article link appears in change communications

### 6. Scheduling Communications

**Step 1**: Go to change details
**Step 2**: Navigate to **Communications** tab
**Step 3**: Click **Schedule Communication**
**Step 4**: Configure:
- Template and channel
- Recipients
- Send date and time
- Timezone

**Step 5**: Save scheduled communication
**Step 6**: Communication sends automatically at scheduled time

### 7. Viewing Communication History

**Step 1**: Go to change details
**Step 2**: Navigate to **Communications** tab
**Step 3**: View communication history:
- Sent communications
- Delivery status
- Open/click tracking (for emails)
- Recipient responses

**Step 4**: Filter by:
- Channel
- Status (Sent, Failed, Pending)
- Date range

### 8. Viewing Dashboard Summary

**Step 1**: Navigate to **Dashboard** → **Summary**
**Step 2**: Review summary statistics:
- Total changes
- Scheduled changes
- Communications sent
- Delivery success rate

**Step 3**: View change calendar:
- Upcoming changes
- Scheduled communications
- Change milestones

## Configuration Options

### Template Variables

- **Change Variables**: Change number, description, dates, state
- **Stakeholder Variables**: Recipient name, role, preferences
- **Custom Variables**: Add custom variables for specific needs

### Notification Rules

- **Auto-Notify Rules**: Automatically send notifications on state changes
- **Reminder Rules**: Send reminders before change implementation
- **Completion Rules**: Send notifications when change completes

### Channel Configuration

- **Email**: SMTP server configuration
- **Teams**: Microsoft Teams webhook or bot
- **Slack**: Slack webhook or app
- **ServiceNow**: ServiceNow API integration

## Best Practices

1. **Notify Early**: Send change notifications well in advance
2. **Use Templates**: Standardize communications with templates
3. **Target Audience**: Send relevant information to appropriate stakeholders
4. **Link KB Articles**: Provide self-service resources via KB links
5. **Track Delivery**: Monitor communication delivery and follow up if needed
6. **Send Reminders**: Send reminders before change implementation

## Troubleshooting

### Change Sync Issues

**Problem**: Changes not syncing from ServiceNow
**Solution**: Verify ServiceNow connection and sync schedule

**Problem**: Change state not updating
**Solution**: Check sync frequency and ServiceNow API access

### Communication Issues

**Problem**: Communications not sending
**Solution**: Verify channel configuration and credentials

**Problem**: Template variables not populating
**Solution**: Check template syntax and variable names

### Delivery Issues

**Problem**: Low delivery success rate
**Solution**: Verify recipient email addresses and channel configuration

**Problem**: Recipients not receiving communications
**Solution**: Check spam filters and channel-specific delivery settings

## Related Documentation

- [Change Communications API Reference](../api/change-communications-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/20-change-communications-agent.md)
