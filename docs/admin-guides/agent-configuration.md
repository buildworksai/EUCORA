# Agent Configuration Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

This guide provides instructions for configuring AI agents in EUCORA, including AI provider setup, agent thresholds, workflow configuration, and monitoring.

## Prerequisites

- Platform Admin role
- Access to EUCORA admin interface
- AI provider credentials (OpenAI, Azure OpenAI, or local model)

---

## AI Provider Configuration

### 1. Configuring OpenAI

**Step 1**: Navigate to **Settings** → **AI Providers**
**Step 2**: Click **Add Provider**
**Step 3**: Select **OpenAI**
**Step 4**: Enter configuration:
- **Provider Name**: Descriptive name (e.g., "OpenAI Production")
- **API Key**: OpenAI API key (stored encrypted)
- **Model**: Select model (e.g., `gpt-4`, `gpt-3.5-turbo`)
- **Max Tokens**: Maximum tokens per request (default: 2000)
- **Temperature**: Model temperature (0.0-1.0, default: 0.7)

**Step 5**: Test connection
**Step 6**: Save and activate provider

### 2. Configuring Azure OpenAI

**Step 1**: Navigate to **Settings** → **AI Providers**
**Step 2**: Click **Add Provider**
**Step 3**: Select **Azure OpenAI**
**Step 4**: Enter configuration:
- **Provider Name**: Descriptive name
- **Endpoint URL**: Azure OpenAI endpoint (e.g., `https://your-resource.openai.azure.com`)
- **API Key**: Azure OpenAI API key
- **Deployment Name**: Model deployment name
- **API Version**: API version (default: `2023-05-15`)

**Step 5**: Test connection
**Step 6**: Save and activate provider

### 3. Configuring Local Models

**Step 1**: Navigate to **Settings** → **AI Providers**
**Step 2**: Click **Add Provider**
**Step 3**: Select **Local Model**
**Step 4**: Enter configuration:
- **Provider Name**: Descriptive name
- **Model Endpoint**: Local model API endpoint
- **API Key**: If required by local model
- **Model Type**: Model type (e.g., `llama`, `mistral`)

**Step 5**: Test connection
**Step 6**: Save and activate provider

---

## Agent Threshold Configuration

### Risk Classification Thresholds

Configure thresholds for agent risk classification:

**Step 1**: Navigate to **Settings** → **Agent Configuration** → **Risk Thresholds**
**Step 2**: Configure thresholds:

- **R1 (Autonomous) Threshold**: Maximum risk score for autonomous operations (default: 20)
- **R2 (Approval Required) Threshold**: Maximum risk score for approval workflow (default: 50)
- **R3 (Mandatory Approval) Threshold**: Operations above this require CAB approval (default: 50+)

**Step 3**: Save thresholds

### Agent-Specific Thresholds

Configure thresholds per agent:

**Step 1**: Navigate to **Settings** → **Agent Configuration** → **Agent Thresholds**
**Step 2**: Select agent (e.g., SecOps Agent)
**Step 3**: Configure agent-specific thresholds:
- **Auto-remediation Threshold**: Risk score for auto-remediation (SecOps)
- **SLO Breach Threshold**: SLO breach threshold for self-healing (SRE)
- **Anomaly Confidence Threshold**: Minimum confidence for anomaly alerts (IAM Security)

**Step 4**: Save configuration

---

## Workflow Configuration

### Creating Agent Workflows

**Step 1**: Navigate to **Settings** → **Workflows**
**Step 2**: Click **Create Workflow**
**Step 3**: Define workflow:
- **Name**: Workflow name
- **Description**: Workflow description
- **Trigger**: Workflow trigger (e.g., "Vulnerability Detected")
- **Steps**: Define workflow steps:
  1. Agent action
  2. Condition check
  3. Approval gate (if R2/R3)
  4. Next action

**Step 4**: Configure approval gates:
- **Approval Required**: Yes/No
- **Approver Role**: Role required for approval
- **Timeout**: Approval timeout (hours)

**Step 5**: Save and activate workflow

### Workflow Templates

Use pre-built workflow templates:

**Step 1**: Navigate to **Settings** → **Workflows** → **Templates**
**Step 2**: Browse available templates:
- Vulnerability Remediation Workflow
- Deployment Planning Workflow
- Ticket Triage Workflow
- SLA Breach Response Workflow

**Step 3**: Select template
**Step 4**: Customize as needed
**Step 5**: Save as new workflow

---

## Agent Monitoring Configuration

### Health Check Configuration

**Step 1**: Navigate to **Settings** → **Agent Configuration** → **Monitoring**
**Step 2**: Configure health checks:
- **Check Interval**: How often to check agent health (default: 5 minutes)
- **Timeout**: Health check timeout (default: 30 seconds)
- **Retry Count**: Number of retries before marking unhealthy (default: 3)

**Step 3**: Configure alerts:
- **Alert on Unhealthy**: Send alert when agent becomes unhealthy
- **Alert Recipients**: Email addresses for alerts
- **Alert Channels**: Alert channels (Email, Teams, Slack)

**Step 4**: Save configuration

### Performance Monitoring

**Step 1**: Navigate to **Settings** → **Agent Configuration** → **Performance**
**Step 2**: Configure performance thresholds:
- **Task Execution Time**: Alert if task takes longer than threshold
- **API Response Time**: Alert if API response time exceeds threshold
- **Error Rate**: Alert if error rate exceeds threshold

**Step 3**: Configure metrics collection:
- **Metrics Retention**: How long to retain metrics (default: 90 days)
- **Metrics Aggregation**: Aggregation interval (default: 1 hour)

**Step 4**: Save configuration

---

## Agent Permissions Configuration

### RBAC for Agents

Configure role-based access control for agents:

**Step 1**: Navigate to **Settings** → **RBAC** → **Agent Permissions**
**Step 2**: Select role (e.g., Application Manager)
**Step 3**: Configure agent permissions:
- **CMDB Integration Agent**: Read/Write/Execute
- **SecOps Agent**: Read/Write/Execute
- **Planning Agent**: Read/Write/Execute
- etc.

**Step 4**: Save permissions

### Scope-Based Access

Configure scope-based access for agents:

**Step 1**: Navigate to **Settings** → **RBAC** → **Agent Scopes**
**Step 2**: Select agent
**Step 3**: Configure allowed scopes:
- **Acquisition Boundaries**: Which boundaries agent can access
- **Business Units**: Which business units agent can access
- **Sites**: Which sites agent can access

**Step 4**: Save scopes

---

## Troubleshooting

### Agent Not Responding

**Problem**: Agent health check fails
**Solution**:
1. Check agent service status
2. Verify network connectivity
3. Check agent logs for errors
4. Verify AI provider connectivity

### Workflow Not Executing

**Problem**: Workflow doesn't trigger
**Solution**:
1. Verify workflow is activated
2. Check trigger conditions
3. Verify agent permissions
4. Check workflow logs

### AI Provider Errors

**Problem**: AI provider API errors
**Solution**:
1. Verify API credentials
2. Check API rate limits
3. Verify model availability
4. Check API endpoint connectivity

---

## Related Documentation

- [Integration Setup Guide](integration-setup.md)
- [Workflow Management Guide](workflow-management.md)
- [Monitoring Agents Guide](monitoring-agents.md)
- [RBAC Agent Permissions Guide](rbac-agent-permissions.md)
