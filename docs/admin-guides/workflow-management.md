# Workflow Management Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

This guide provides instructions for creating and managing agent workflows in EUCORA. Workflows orchestrate agent actions with approval gates and conditional logic.

## Prerequisites

- Platform Admin role
- Understanding of agent capabilities
- Workflow design requirements

---

## Workflow Concepts

### Workflow Components

- **Trigger**: Event that starts the workflow
- **Steps**: Individual actions in the workflow
- **Conditions**: Logic that determines workflow path
- **Approval Gates**: Points where approval is required
- **Actions**: Agent operations to execute

### Workflow States

- **Draft**: Workflow being created/edited
- **Active**: Workflow is active and can be triggered
- **Paused**: Workflow is temporarily disabled
- **Archived**: Workflow is no longer used

---

## Creating Workflows

### Basic Workflow Creation

**Step 1**: Navigate to **Settings** → **Workflows**
**Step 2**: Click **Create Workflow**
**Step 3**: Enter basic information:
- **Name**: Descriptive workflow name
- **Description**: Workflow purpose and description
- **Category**: Workflow category (e.g., Deployment, Security, Operations)

**Step 4**: Define trigger:
- **Trigger Type**: Select trigger type:
  - Event-based (e.g., "Vulnerability Detected")
  - Scheduled (e.g., "Daily at 2 AM")
  - Manual (user-initiated)
- **Trigger Conditions**: Define when workflow should trigger

**Step 5**: Add workflow steps:
- Click **Add Step**
- Select step type:
  - **Agent Action**: Execute agent operation
  - **Condition**: Branch based on condition
  - **Approval Gate**: Require approval
  - **Wait**: Wait for condition or time
  - **Notification**: Send notification

**Step 6**: Configure each step:
- **Step Name**: Descriptive name
- **Step Configuration**: Configure step-specific settings
- **On Success**: Next step on success
- **On Failure**: Next step on failure

**Step 7**: Save workflow

### Advanced Workflow Features

#### Conditional Branching

**Step 1**: Add **Condition** step
**Step 2**: Define condition:
- **Condition Type**: Select type (e.g., "Risk Score > 50")
- **Condition Expression**: Define expression
- **True Path**: Step to execute if true
- **False Path**: Step to execute if false

#### Approval Gates

**Step 1**: Add **Approval Gate** step
**Step 2**: Configure approval:
- **Approval Type**: Select type:
  - **Role-Based**: Require approval from specific role
  - **User-Based**: Require approval from specific user
  - **CAB Approval**: Require CAB approval
- **Approver Role/User**: Select approver
- **Timeout**: Approval timeout (hours)
- **Escalation**: Escalate if not approved in time

#### Parallel Execution

**Step 1**: Add **Parallel** step
**Step 2**: Define parallel branches:
- **Branch 1**: First parallel workflow
- **Branch 2**: Second parallel workflow
- **Wait for All**: Wait for all branches to complete
- **Wait for Any**: Proceed when any branch completes

---

## Workflow Templates

### Using Templates

**Step 1**: Navigate to **Settings** → **Workflows** → **Templates**
**Step 2**: Browse available templates:
- Vulnerability Remediation Workflow
- Deployment Planning Workflow
- Ticket Triage Workflow
- SLA Breach Response Workflow
- Change Communication Workflow

**Step 3**: Select template
**Step 4**: Review template steps
**Step 5**: Customize as needed:
- Modify steps
- Add/remove steps
- Change conditions
- Update approval gates

**Step 6**: Save as new workflow

### Creating Templates

**Step 1**: Create workflow
**Step 2**: Test workflow thoroughly
**Step 3**: Navigate to workflow details
**Step 4**: Click **Save as Template**
**Step 5**: Enter template information:
- **Template Name**: Template name
- **Description**: Template description
- **Category**: Template category
- **Tags**: Template tags

**Step 6**: Save template

---

## Workflow Examples

### Example 1: Vulnerability Remediation Workflow

```
Trigger: Critical Vulnerability Detected
├─ Step 1: SecOps Agent - Create Remediation Plan
├─ Step 2: Approval Gate - Require Security Reviewer Approval
├─ Step 3: Planning Agent - Generate Deployment Plan
├─ Step 4: Approval Gate - Require CAB Approval (if Risk > 50)
├─ Step 5: Execute Remediation
├─ Step 6: Change Communications Agent - Notify Stakeholders
└─ Step 7: Request Coordination Agent - Track Request
```

### Example 2: Deployment Planning Workflow

```
Trigger: Deployment Request Submitted
├─ Step 1: Planning Agent - Generate Deployment Plan
├─ Step 2: Discovery Agent - Verify Application Inventory
├─ Step 3: SecOps Agent - Check Vulnerabilities
├─ Step 4: Condition - Risk Score > 50?
│   ├─ Yes: Approval Gate - Require CAB Approval
│   └─ No: Continue
├─ Step 5: Planning Agent - Perform Blast Radius Analysis
├─ Step 6: Planning Agent - Generate Rollback Plan
└─ Step 7: Approval Gate - Require Application Manager Approval
```

### Example 3: Ticket Triage Workflow

```
Trigger: New Ticket Created
├─ Step 1: KB Triage Agent - Perform AI Triage
├─ Step 2: KB Triage Agent - Search Knowledge Base
├─ Step 3: Condition: Found Resolution?
│   ├─ Yes: KB Triage Agent - Suggest Resolution
│   └─ No: KB Triage Agent - Escalate to Human
├─ Step 4: Request Coordination Agent - Update Request
└─ Step 5: Change Communications Agent - Notify Requestor
```

---

## Managing Workflows

### Activating/Deactivating Workflows

**Step 1**: Navigate to **Settings** → **Workflows**
**Step 2**: Select workflow
**Step 3**: Click **Activate** or **Deactivate**
**Step 4**: Confirm action

### Editing Workflows

**Step 1**: Navigate to workflow details
**Step 2**: Click **Edit**
**Step 3**: Make changes
**Step 4**: Save changes
**Note**: Active workflows can be edited, but changes take effect immediately

### Versioning Workflows

**Step 1**: Navigate to workflow details
**Step 2**: Click **Version History**
**Step 3**: View workflow versions
**Step 4**: Restore previous version if needed

### Testing Workflows

**Step 1**: Navigate to workflow details
**Step 2**: Click **Test Workflow**
**Step 3**: Provide test inputs
**Step 4**: Review test execution
**Step 5**: Review test results and logs

---

## Workflow Monitoring

### Viewing Workflow Executions

**Step 1**: Navigate to **Workflows** → **Executions**
**Step 2**: View execution list:
- Workflow name
- Trigger time
- Status (Running, Completed, Failed)
- Duration
- Steps completed

**Step 3**: Click on execution to view details:
- Step-by-step execution log
- Approval status
- Error messages (if any)

### Workflow Metrics

**Step 1**: Navigate to **Workflows** → **Metrics**
**Step 2**: View metrics:
- **Execution Count**: Number of executions
- **Success Rate**: Percentage of successful executions
- **Average Duration**: Average execution time
- **Approval Rate**: Percentage requiring approval
- **Average Approval Time**: Average time to approval

---

## Troubleshooting

### Workflow Not Triggering

**Problem**: Workflow doesn't trigger when expected
**Solution**:
1. Verify workflow is activated
2. Check trigger conditions
3. Verify trigger event is being generated
4. Check workflow logs

### Workflow Failing

**Problem**: Workflow execution fails
**Solution**:
1. Review execution logs
2. Check step configuration
3. Verify agent availability
4. Check external system connectivity

### Approval Timeout

**Problem**: Approvals timing out
**Solution**:
1. Increase approval timeout
2. Configure escalation rules
3. Verify approver availability
4. Check notification delivery

---

## Related Documentation

- [Agent Configuration Guide](agent-configuration.md)
- [Integration Setup Guide](integration-setup.md)
- [Monitoring Agents Guide](monitoring-agents.md)
