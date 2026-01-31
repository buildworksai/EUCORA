# SRE Agent User Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

The SRE Agent provides site reliability engineering automation including monitoring integration, health checks, SLO tracking, self-healing automation, and runbook execution. It helps SRE teams maintain service reliability and automate incident response.

## Key Features

- **Monitoring Integration**: Connects to Prometheus, Datadog, Azure Monitor, and New Relic
- **Health Checks**: Automated health endpoint monitoring
- **SLO Tracking**: Service Level Objective monitoring and error budget tracking
- **Self-Healing**: Automated remediation based on health check failures and SLO breaches
- **Runbook Automation**: Automated runbook execution for common incidents

## Getting Started

### Accessing the Agent

1. Navigate to **SRE** from the main dashboard
2. You'll see the SRE Dashboard with health status, SLO compliance, and self-healing activity

### Prerequisites

- Monitoring platform credentials (Prometheus, Datadog, Azure Monitor, or New Relic)
- Application health endpoints configured
- SRE Agent permissions (granted by Platform Admin)

## Common Workflows

### 1. Configuring Monitoring Platforms

**Step 1**: Navigate to **Monitoring Platforms** tab
**Step 2**: Click **Add Platform**
**Step 3**: Select platform type:
- Prometheus
- Datadog
- Azure Monitor
- New Relic

**Step 4**: Enter connection details:
- API endpoint
- API key or authentication credentials
- Test connection

**Step 5**: Save and activate platform

### 2. Setting Up Health Endpoints

**Step 1**: Go to **Health Endpoints** tab
**Step 2**: Click **Add Endpoint**
**Step 3**: Configure endpoint:
- Name and description
- Application (optional)
- URL and HTTP method
- Expected status code
- Timeout and check interval

**Step 4**: Save and activate endpoint
**Step 5**: Health checks run automatically based on interval

### 3. Viewing Health Check Results

**Step 1**: Navigate to **Health Check Results**
**Step 2**: Filter by:
- Endpoint
- Status (Healthy, Degraded, Unhealthy)
- Time range

**Step 3**: Review health check history:
- Response times
- Status codes
- Error messages
- Trend analysis

**Step 4**: View endpoint history:
- Click on endpoint
- Select **History** tab
- Review historical health data

### 4. Configuring SLOs

**Step 1**: Go to **SLOs** tab
**Step 2**: Click **Create SLO**
**Step 3**: Define SLO:
- Name and service name
- SLO type (Availability, Latency, Error Rate, Throughput)
- Target value (e.g., 99.9% availability)
- Measurement window (default: 30 days)

**Step 4**: Save and activate SLO
**Step 5**: Monitor SLO metrics automatically

### 5. Monitoring SLO Compliance

**Step 1**: Navigate to **SLOs** tab
**Step 2**: View SLO list with compliance status
**Step 3**: Click on SLO to view:
- **Metrics**: Historical SLO measurements
- **Error Budget**: Remaining error budget and burn rate
- **Target Met**: Current compliance status

**Step 4**: Review error budget:
- Remaining error budget percentage
- Burn rate (error budget consumption rate)
- Projected breach date

### 6. Creating Self-Healing Rules

**Step 1**: Go to **Self-Healing Rules** tab
**Step 2**: Click **Create Rule**
**Step 3**: Configure rule:
- Name and description
- Trigger type:
  - Health check failure
  - SLO breach
  - Metric threshold
- Trigger conditions (e.g., 3 consecutive failures)
- Remediation script
- Risk level (Low, Medium, High, Critical)
- Approval requirement

**Step 4**: Save and activate rule
**Step 5**: Rule triggers automatically when conditions are met

### 7. Monitoring Self-Healing Executions

**Step 1**: Navigate to **Self-Healing Executions** tab
**Step 2**: View execution list:
- Rule that triggered
- Status (Pending, Approved, Executing, Completed, Failed)
- Trigger event details

**Step 3**: Approve pending executions (if approval required):
- Click on execution
- Review trigger event and remediation script
- Click **Approve** to execute

**Step 4**: Review execution logs:
- Execution status
- Script output
- Success/failure details

### 8. Managing Runbooks

**Step 1**: Go to **Runbooks** tab
**Step 2**: Click **Create Runbook**
**Step 3**: Define runbook:
- Name and category
- Risk level
- Steps (ordered list of actions)
- Prerequisites and notes

**Step 4**: Save and activate runbook

**Step 5**: Execute runbook:
- Select runbook
- Click **Execute**
- Provide trigger reason
- Monitor execution progress

### 9. Viewing SRE Reports

**Step 1**: Navigate to **Reports** → **Overview**
**Step 2**: Review summary statistics:
- Healthy vs unhealthy endpoints
- Active SLOs and compliance rate
- Active healing rules and recent executions

**Step 3**: View **SLO Status** report:
- SLO compliance by service
- Error budget status
- Breach risk assessment

**Step 4**: View **Healing Activity** report:
- Execution success rate
- Most triggered rules
- Average resolution time

## Configuration Options

### Health Check Configuration

- **Check Interval**: Frequency of health checks (default: 5 minutes)
- **Timeout**: Request timeout (default: 30 seconds)
- **Retry Logic**: Number of retries before marking unhealthy

### SLO Configuration

- **Measurement Window**: Time window for SLO calculation (default: 30 days)
- **Error Budget**: Percentage of allowed failures
- **Alert Thresholds**: Configure alerts for error budget consumption

### Self-Healing Configuration

- **Approval Thresholds**: Risk levels requiring approval
- **Execution Timeout**: Maximum execution time
- **Rollback Strategy**: Automatic rollback on failure

## Best Practices

1. **Monitor Critical Endpoints**: Set up health checks for all critical services
2. **Define Realistic SLOs**: Set achievable SLO targets based on historical data
3. **Test Self-Healing Rules**: Test rules in non-production before enabling
4. **Document Runbooks**: Keep runbooks updated with current procedures
5. **Review Error Budgets**: Monitor error budget consumption regularly
6. **Automate Low-Risk Actions**: Enable auto-approval for low-risk self-healing rules

## Troubleshooting

### Health Check Issues

**Problem**: Health checks always fail
**Solution**: Verify endpoint URL, network connectivity, and expected status code

**Problem**: Health checks timeout
**Solution**: Increase timeout value or optimize endpoint response time

### SLO Issues

**Problem**: SLO always shows breach
**Solution**: Review target value and measurement window settings

**Problem**: Error budget depleting too fast
**Solution**: Investigate root cause and adjust SLO target if needed

### Self-Healing Issues

**Problem**: Rule doesn't trigger
**Solution**: Verify trigger conditions and rule activation status

**Problem**: Remediation script fails
**Solution**: Review script logs and verify script permissions

## Related Documentation

- [SRE Agent API Reference](../api/sre-agent-api.yaml)
- [Admin Configuration Guide](../admin-guides/integration-setup.md)
- [Planning Document](../planning/27-sre-agent.md)
