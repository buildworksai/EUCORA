# Platform Admin Training

**SPDX-License-Identifier: Apache-2.0**

## Learning Objectives

By the end of this training, you will be able to:
1. Configure AI providers and agent settings
2. Set up external integrations (ServiceNow, SIEM, monitoring)
3. Create and manage agent workflows
4. Configure RBAC permissions for agents
5. Monitor agent health and performance
6. Troubleshoot agent issues

---

## Key Concepts

### Agent Architecture

**AI Workflow Engine**:
- Orchestrates agent workflows
- Manages risk classification (R1/R2/R3)
- Handles approval workflows
- Publishes events to event store

**Agent Types**:
- **Wave 1 Agents** (E10-E16): Foundation agents
- **Wave 2 Agents** (E17-E21): Advanced agents

**Integration Points**:
- ServiceNow (CMDB, Change, Request, KB)
- SIEM platforms (Splunk, Sentinel, QRadar)
- Monitoring platforms (Prometheus, Datadog, Azure Monitor)
- Vulnerability scanners (Qualys, Nessus, Rapid7)

---

## Hands-On Exercises

### Exercise 1: Configuring AI Providers

**Objective**: Set up AI provider for agent operations

**Steps**:
1. Navigate to **Settings** → **AI Providers**
2. Click **Add Provider**
3. Select provider type (OpenAI, Azure OpenAI, Local)
4. Enter configuration:
   - Provider name
   - API credentials
   - Model selection
   - Configuration parameters
5. Test connection
6. Save and activate provider
7. Verify provider is available for agents

**Expected Outcome**: AI provider configured and available

### Exercise 2: Setting Up ServiceNow Integration

**Objective**: Configure ServiceNow integration for multiple agents

**Steps**:
1. Navigate to **Settings** → **Integrations** → **ServiceNow**
2. Configure CMDB connection:
   - Instance URL
   - Credentials
   - Table mappings
3. Configure Change Management connection
4. Configure Request Management connection
5. Configure Knowledge Base connection
6. Test each connection
7. Activate integrations
8. Verify data sync

**Expected Outcome**: ServiceNow integrations configured and syncing

### Exercise 3: Creating Agent Workflow

**Objective**: Create workflow for vulnerability remediation

**Steps**:
1. Navigate to **Settings** → **Workflows**
2. Click **Create Workflow**
3. Define workflow:
   - Name: "Vulnerability Remediation"
   - Trigger: "Critical Vulnerability Detected"
4. Add steps:
   - Step 1: SecOps Agent - Create Remediation Plan
   - Step 2: Approval Gate - Security Reviewer Approval
   - Step 3: Planning Agent - Generate Deployment Plan
   - Step 4: Approval Gate - CAB Approval (if Risk > 50)
   - Step 5: Execute Remediation
   - Step 6: Change Communications - Notify Stakeholders
5. Configure approval gates
6. Save and activate workflow
7. Test workflow

**Expected Outcome**: Workflow created and tested

### Exercise 4: Configuring RBAC Permissions

**Objective**: Configure agent permissions for roles

**Steps**:
1. Navigate to **Settings** → **RBAC** → **Agent Permissions**
2. Select role (e.g., Application Manager)
3. Configure permissions for each agent:
   - Planning Agent: Read, Write, Execute, Approve
   - Discovery Agent: Read, Write, Execute
   - Request Coordination Agent: Read, Write, Execute
4. Configure scope restrictions:
   - Acquisition boundaries
   - Business units
   - Sites
5. Save permissions
6. Test permissions with test user

**Expected Outcome**: RBAC permissions configured and tested

### Exercise 5: Monitoring Agent Health

**Objective**: Set up agent health monitoring and alerts

**Steps**:
1. Navigate to **Settings** → **Agent Configuration** → **Monitoring**
2. Configure health checks:
   - Check interval: 5 minutes
   - Timeout: 30 seconds
   - Retry count: 3
3. Configure health alerts:
   - Alert on unhealthy
   - Alert recipients
   - Alert channels
4. Navigate to **Monitoring** → **Agent Health**
5. Review agent health status
6. Verify alerts are configured
7. Test alert by simulating failure

**Expected Outcome**: Agent health monitoring configured with alerts

---

## Assessment Checklist

- [ ] Can configure AI providers
- [ ] Can set up external integrations
- [ ] Can create agent workflows
- [ ] Can configure RBAC permissions
- [ ] Can monitor agent health
- [ ] Can troubleshoot agent issues
- [ ] Understands agent architecture
- [ ] Knows integration requirements
- [ ] Can configure alerts and monitoring

---

## Quick Reference Card

### Configuration
- **AI Providers**: Settings → AI Providers
- **Integrations**: Settings → Integrations
- **Workflows**: Settings → Workflows
- **RBAC**: Settings → RBAC
- **Monitoring**: Settings → Monitoring

### Monitoring
- **Agent Health**: Monitoring → Agent Health
- **Performance**: Monitoring → Agent Performance
- **Logs**: Monitoring → Logs
- **Integration Health**: Monitoring → Integration Health

### Troubleshooting
- **Health Checks**: Test agent health endpoints
- **Logs**: Review agent logs for errors
- **Connections**: Test external system connections
- **Permissions**: Verify RBAC permissions

---

## Related Documentation

- [Agent Configuration Guide](../admin-guides/agent-configuration.md)
- [Integration Setup Guide](../admin-guides/integration-setup.md)
- [Workflow Management Guide](../admin-guides/workflow-management.md)
- [RBAC Agent Permissions Guide](../admin-guides/rbac-agent-permissions.md)
- [Monitoring Agents Guide](../admin-guides/monitoring-agents.md)
- [Troubleshooting Agents Guide](../admin-guides/troubleshooting-agents.md)
