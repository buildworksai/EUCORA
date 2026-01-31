# IAM Security Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The IAM Security Agent helps security teams monitor identity provider access, detect security anomalies, track permission changes, and manage security alerts. It integrates with Entra ID, Okta, Active Directory, and ServiceNow IAM.

## Key Features

- **Identity Provider Monitoring**: Monitors sign-in events across multiple providers
- **Anomaly Detection**: AI-powered detection of suspicious activity patterns
- **Permission Change Tracking**: Tracks role assignments and permission changes
- **Security Alerts**: Generates alerts for security incidents
- **Automated Response**: Automated response actions for security threats

## Getting Started

### Accessing the Agent

1. Navigate to **IAM Security** from the main dashboard
2. You'll see the Security Dashboard with sign-in events, anomalies, and security alerts

### Prerequisites

- Identity provider access (Entra ID, Okta, AD, ServiceNow IAM)
- IAM Security Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Configuring Identity Providers

**Step 1**: Navigate to **Providers** tab
**Step 2**: Click **Add Provider**
**Step 3**: Select provider type:
- Entra ID (Azure AD)
- Okta
- Active Directory
- ServiceNow IAM

**Step 4**: Enter connection details:
- Provider name
- API endpoint
- Authentication credentials (OAuth, API key, etc.)
- Test connection

**Step 5**: Configure sync settings:
- Sign-in event sync frequency
- Permission change sync frequency

**Step 6**: Save and activate provider

### 2. Viewing Sign-In Events

**Step 1**: Go to **Sign-Ins** tab
**Step 2**: View sign-in event list:
- User principal
- IP address and location
- Sign-in time
- Success/failure status
- Failure reason (if failed)

**Step 3**: Filter by:
- Provider
- User principal
- Success status
- Date range

**Step 4**: Click on event to view details:
- Device information
- Application accessed
- Risk score
- Related anomalies

### 3. Reviewing Anomalies

**Step 1**: Navigate to **Anomalies** tab
**Step 2**: View anomaly list:
- Anomaly type:
  - Unusual Sign-In
  - Privilege Escalation
  - Suspicious Activity
- User principal
- Detected at time
- Confidence score
- Status (New, Investigating, Resolved, False Positive)

**Step 3**: Filter by:
- Provider
- Anomaly type
- Status
- Confidence score

**Step 4**: Click on anomaly to view details:
- Anomaly description
- Related events
- Risk assessment
- Recommended actions

### 4. Resolving Anomalies

**Step 1**: Go to anomaly details
**Step 2**: Review anomaly information:
- What triggered the anomaly
- Related sign-in events
- User activity history
- Risk assessment

**Step 3**: Investigate further:
- Review user's recent activity
- Check permission changes
- Verify with user if needed

**Step 4**: Resolve anomaly:
- Click **Resolve**
- Select resolution status:
  - **Resolved**: Legitimate activity, issue addressed
  - **False Positive**: Not a security issue
- Add resolution notes
- Save resolution

### 5. Tracking Permission Changes

**Step 1**: Go to **Permission Changes** tab
**Step 2**: View permission change list:
- User principal
- Change type:
  - Role Assignment
  - Permission Grant
  - Permission Revoke
- Resource affected
- Changed at time
- Changed by user

**Step 3**: Filter by:
- Provider
- User principal
- Change type
- Date range

**Step 4**: Review change details:
- Previous permissions
- New permissions
- Change reason
- Related anomalies

### 6. Managing Detection Rules

**Step 1**: Navigate to **Rules** tab
**Step 2**: View detection rules:
- Rule name
- Rule type:
  - Sign-In Anomaly
  - Privilege Change
  - Access Pattern
- Conditions
- Active status

**Step 3**: Create new rule:
- Click **Create Rule**
- Define rule conditions
- Set alert severity
- Save and activate rule

**Step 4**: Edit existing rules:
- Select rule
- Modify conditions
- Update severity
- Save changes

### 7. Reviewing Security Alerts

**Step 1**: Go to **Alerts** tab
**Step 2**: View alert list:
- Alert type (Anomaly, Permission Change, Policy Violation)
- Severity (Low, Medium, High, Critical)
- Title and description
- Alert time
- Status (New, Investigating, Resolved)

**Step 3**: Filter by:
- Provider
- Severity
- Status
- Alert type

**Step 4**: Click on alert to:
- View alert details
- Investigate related events
- Take response actions

### 8. Taking Security Actions

**Step 1**: Go to alert or anomaly details
**Step 2**: Navigate to **Actions** tab
**Step 3**: Available actions:
- **Revoke Access**: Revoke user access immediately
- **Require Password Reset**: Force password reset
- **Disable Account**: Temporarily disable account
- **Escalate**: Escalate to security team

**Step 4**: Select action
**Step 5**: Provide reason
**Step 6**: Confirm action
**Step 7**: Action executes and is logged

### 9. Viewing Security Reports

**Step 1**: Navigate to **Reports** → **Summary**
**Step 2**: Review summary statistics:
- Total sign-ins
- Failed sign-ins
- Active anomalies
- Critical alerts
- Permission changes

**Step 3**: View detailed reports:
- **Sign-In Report**: Sign-in activity trends
- **Anomaly Report**: Anomaly detection statistics
- **Permission Change Report**: Permission change audit trail
- **Security Alert Report**: Alert frequency and resolution

## Configuration Options

### Anomaly Detection

- **Detection Sensitivity**: Configure anomaly detection sensitivity
- **Confidence Thresholds**: Set minimum confidence for alerts
- **Detection Rules**: Configure custom detection rules

### Alert Configuration

- **Alert Severity**: Configure severity levels for different alert types
- **Notification Rules**: Configure who receives alerts
- **Response Actions**: Configure automated response actions

## Best Practices

1. **Monitor Sign-Ins Regularly**: Review sign-in events daily
2. **Investigate Anomalies Promptly**: Investigate anomalies within 24 hours
3. **Track Permission Changes**: Review permission changes weekly
4. **Use Detection Rules**: Configure rules for common threat patterns
5. **Document Resolutions**: Document anomaly resolution decisions
6. **Review Reports**: Review security reports monthly

## Troubleshooting

### Provider Connection Issues

**Problem**: Provider connection fails
**Solution**: Verify credentials and API access permissions

**Problem**: Sign-in events not syncing
**Solution**: Check sync schedule and API rate limits

### Anomaly Detection Issues

**Problem**: Too many false positives
**Solution**: Adjust detection sensitivity and confidence thresholds

**Problem**: Anomalies not detected
**Solution**: Review detection rules and sensitivity settings

### Alert Issues

**Problem**: Alerts not generating
**Solution**: Verify alert rules and severity configuration

**Problem**: Alerts not being sent
**Solution**: Check notification configuration and channel settings

## Related Documentation

- [IAM Security API Reference](../api/iam-security-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/24-iam-security-agent.md)
