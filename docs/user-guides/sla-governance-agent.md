# SLA Governance Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The SLA Governance Agent helps service managers define, monitor, and enforce Service Level Agreements (SLAs). It tracks SLA compliance, detects breaches, and integrates with ServiceNow service catalog for automated SLA management.

## Key Features

- **SLA Definition**: Create and manage SLA definitions with natural language support
- **KPI Tracking**: Monitor Key Performance Indicators (KPIs) linked to SLAs
- **Compliance Monitoring**: Track SLA compliance in real-time
- **Breach Detection**: Automatically detect and alert on SLA breaches
- **ServiceNow Integration**: Sync with ServiceNow service catalog

## Getting Started

### Accessing the Agent

1. Navigate to **SLA Governance** from the main dashboard
2. You'll see the SLA Dashboard with active SLAs, compliance status, and breach alerts

### Prerequisites

- ServiceNow service catalog access (optional, for service sync)
- SLA Governance Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Creating SLA Definition

**Step 1**: Navigate to **SLAs** tab
**Step 2**: Click **Create SLA**
**Step 3**: Enter basic information:
- Name and description
- Service (from service catalog)
- Version
- Effective dates

**Step 4**: Define SLA targets:
- Response time (e.g., 4 hours)
- Resolution time (e.g., 24 hours)
- Availability (e.g., 99.9%)
- Uptime (e.g., 99.5%)

**Step 5**: Submit for approval
**Step 6**: After approval, SLA becomes active

### 2. Using Natural Language SLA Creation

**Step 1**: Go to **SLAs** → **Parse Request**
**Step 2**: Enter natural language request:
  Example: "Service requests must be responded to within 4 hours and resolved within 24 hours. Availability must be 99.9%."

**Step 3**: Review parsed SLA definition:
- Extracted targets
- Service mapping
- Suggested KPIs

**Step 4**: Modify if needed
**Step 5**: Save and submit for approval

### 3. Configuring KPIs

**Step 1**: Navigate to **KPIs** tab
**Step 2**: Click **Create KPI**
**Step 3**: Define KPI:
- Name and type (Response Time, Resolution Time, Availability, Customer Satisfaction)
- Measurement method
- Target value
- Link to SLA (optional)

**Step 4**: Save KPI
**Step 5**: Link to SLA:
- Go to SLA details
- Add KPI link
- Configure measurement frequency

### 4. Monitoring SLA Compliance

**Step 1**: Go to **Compliance** tab
**Step 2**: View compliance records:
- SLA name
- Compliance period
- Overall compliance percentage
- Target compliance details

**Step 3**: Filter by:
- SLA
- Date range
- Compliance status

**Step 4**: Review compliance details:
- KPI-level compliance
- Breach history
- Trend analysis

### 5. Managing SLA Breaches

**Step 1**: Navigate to **Breaches** tab
**Step 2**: View breach list:
- SLA name
- Breach type (Response Time, Resolution Time, Availability)
- Breach time and duration
- Affected requests

**Step 3**: Review breach details:
- Root cause analysis
- Impact assessment
- Resolution notes

**Step 4**: Resolve breach:
- Add resolution notes
- Update status
- Document corrective actions

### 6. Viewing SLA Reports

**Step 1**: Go to **Reports** → **Summary**
**Step 2**: Review summary statistics:
- Total SLAs
- Active SLAs
- Overall compliance rate
- Breach count

**Step 3**: View compliance trends:
- Compliance over time
- Breach frequency
- KPI performance

## Configuration Options

### SLA Templates

- **Pre-defined Templates**: Use templates for common SLA types
- **Custom Templates**: Create templates for your organization
- **Template Variables**: Configure variables for dynamic SLA creation

### KPI Configuration

- **Measurement Frequency**: Configure how often KPIs are measured
- **Aggregation Method**: Choose aggregation (average, percentile, etc.)
- **Alert Thresholds**: Set alerts for KPI deviations

### Breach Detection

- **Detection Rules**: Configure automatic breach detection
- **Alert Configuration**: Set up breach alerts and notifications
- **Escalation Rules**: Define escalation for critical breaches

## Best Practices

1. **Define Realistic SLAs**: Base SLAs on historical performance data
2. **Link KPIs to SLAs**: Ensure KPIs accurately measure SLA targets
3. **Monitor Compliance Regularly**: Review compliance reports weekly
4. **Investigate Breaches Promptly**: Analyze root causes and implement fixes
5. **Update SLAs as Needed**: Review and update SLAs based on business changes
6. **Document Exceptions**: Document any approved SLA exceptions

## Troubleshooting

### SLA Definition Issues

**Problem**: Natural language parsing fails
**Solution**: Use more specific language or define SLA manually

**Problem**: SLA not activating
**Solution**: Verify approval status and effective dates

### Compliance Issues

**Problem**: Compliance not calculating correctly
**Solution**: Verify KPI measurements and SLA target definitions

**Problem**: Breaches not detected
**Solution**: Check breach detection rules and KPI measurement frequency

## Related Documentation

- [SLA Governance API Reference](../api/sla-governance-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/28-sla-governance-agent.md)
