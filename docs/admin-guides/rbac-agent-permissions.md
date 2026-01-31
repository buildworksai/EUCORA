# RBAC Agent Permissions Guide

**SPDX-License-Identifier: Apache-2.0**

## Overview

This guide provides instructions for configuring role-based access control (RBAC) for AI agents in EUCORA. It covers agent-specific permissions, scope-based access, and permission inheritance.

## Prerequisites

- Platform Admin role
- Understanding of EUCORA RBAC model
- List of roles and users requiring agent access

---

## RBAC Model Overview

### Roles

EUCORA defines 9 roles with agent-specific permissions:

1. **Platform Admin**: Full access to all agents and configuration
2. **Application Manager**: Access to planning, discovery, and request coordination agents
3. **Security Team**: Access to SecOps and IAM Security agents
4. **SRE Team**: Access to SRE agent
5. **Desktop Support**: Access to KB Triage agent
6. **Service Manager**: Access to SLA Governance agent
7. **IT Operations**: Access to automation advisor and documentation agents
8. **CAB Approver**: Approval permissions for agent workflows
9. **Auditor**: Read-only access to agent data

---

## Configuring Agent Permissions

### Role-Based Agent Permissions

**Step 1**: Navigate to **Settings** → **RBAC** → **Agent Permissions**
**Step 2**: Select role (e.g., Application Manager)
**Step 3**: Configure permissions for each agent:

#### CMDB Integration Agent
- **Read**: View CMDB connections and sync records
- **Write**: Create/edit CMDB connections
- **Execute**: Trigger CMDB syncs

#### Planning Agent
- **Read**: View deployment plans
- **Write**: Create/edit deployment plans
- **Execute**: Execute deployment plans
- **Approve**: Approve deployment plans

#### SecOps Agent
- **Read**: View vulnerabilities and alerts
- **Write**: Create remediation plans
- **Execute**: Execute remediation plans
- **Approve**: Approve remediation plans

#### SRE Agent
- **Read**: View SLOs and health checks
- **Write**: Create SLOs and self-healing rules
- **Execute**: Execute self-healing actions
- **Approve**: Approve self-healing executions

#### KB Triage Agent
- **Read**: View knowledge articles
- **Write**: Create/edit triage requests
- **Execute**: Perform triage operations

#### SLA Governance Agent
- **Read**: View SLA definitions
- **Write**: Create/edit SLA definitions
- **Approve**: Approve SLA definitions

#### Request Coordination Agent
- **Read**: View tracked requests
- **Write**: Create/edit requests
- **Execute**: Send communications

**Step 4**: Save permissions

### Permission Levels

Each agent supports three permission levels:

- **Read**: View agent data and reports
- **Write**: Create and modify agent data
- **Execute**: Execute agent operations

Some agents also support:
- **Approve**: Approve agent actions (for R2/R3 operations)

---

## Scope-Based Access Control

### Acquisition Boundary Scoping

**Step 1**: Navigate to **Settings** → **RBAC** → **Agent Scopes**
**Step 2**: Select role
**Step 3**: Configure acquisition boundaries:
- **Allowed Boundaries**: Select boundaries role can access
- **Default Boundary**: Default boundary for new resources

**Step 4**: Save scopes

### Business Unit Scoping

**Step 1**: Navigate to **Settings** → **RBAC** → **Agent Scopes**
**Step 2**: Select role
**Step 3**: Configure business units:
- **Allowed Business Units**: Select business units role can access
- **Restricted Business Units**: Business units explicitly restricted

**Step 4**: Save scopes

### Site Scoping

**Step 1**: Navigate to **Settings** → **RBAC** → **Agent Scopes**
**Step 2**: Select role
**Step 3**: Configure sites:
- **Allowed Sites**: Select sites role can access
- **Site Classes**: Restrict by site class (Online, Intermittent, Air-gapped)

**Step 4**: Save scopes

---

## Agent-Specific Permission Examples

### Application Manager Permissions

**Planning Agent**:
- Read: Yes
- Write: Yes
- Execute: Yes
- Approve: Yes (for own plans)

**Discovery Agent**:
- Read: Yes
- Write: Yes
- Execute: Yes

**Request Coordination Agent**:
- Read: Yes
- Write: Yes
- Execute: Yes

**Scope**: Limited to assigned business units

### Security Team Permissions

**SecOps Agent**:
- Read: Yes
- Write: Yes
- Execute: Yes
- Approve: Yes (for remediation plans)

**IAM Security Agent**:
- Read: Yes
- Write: Yes
- Execute: Yes (for security actions)

**Scope**: Organization-wide

### SRE Team Permissions

**SRE Agent**:
- Read: Yes
- Write: Yes
- Execute: Yes
- Approve: Yes (for self-healing rules)

**Scope**: Organization-wide

---

## Permission Inheritance

### Role Hierarchy

Permissions can inherit from parent roles:

**Step 1**: Navigate to **Settings** → **RBAC** → **Roles**
**Step 2**: Select role
**Step 3**: Configure parent role:
- **Parent Role**: Select parent role
- **Inherit Permissions**: Enable permission inheritance

**Step 4**: Override inherited permissions as needed
**Step 5**: Save role

### Permission Overrides

Override inherited permissions:

**Step 1**: Navigate to role permissions
**Step 2**: Find inherited permission
**Step 3**: Click **Override**
**Step 4**: Set new permission level
**Step 5**: Save override

---

## Testing Permissions

### Permission Testing

**Step 1**: Navigate to **Settings** → **RBAC** → **Test Permissions**
**Step 2**: Select user and role
**Step 3**: Select agent and operation
**Step 4**: Click **Test**
**Step 5**: Review test results:
- Permission granted/denied
- Scope restrictions
- Approval requirements

---

## Audit and Compliance

### Permission Audit Log

**Step 1**: Navigate to **Settings** → **RBAC** → **Audit Log**
**Step 2**: View permission changes:
- User/role
- Permission changed
- Old value
- New value
- Changed by
- Timestamp

**Step 3**: Export audit log for compliance

### Permission Reports

**Step 1**: Navigate to **Settings** → **RBAC** → **Reports**
**Step 2**: Generate reports:
- **Permission Summary**: Overview of all permissions
- **Role Permissions**: Permissions by role
- **User Permissions**: Permissions by user
- **Agent Permissions**: Permissions by agent

**Step 3**: Export reports

---

## Troubleshooting

### Permission Denied Errors

**Problem**: User receives permission denied error
**Solution**:
1. Verify user role assignment
2. Check agent permissions for role
3. Verify scope restrictions
4. Check approval requirements

### Scope Restrictions

**Problem**: User cannot access expected resources
**Solution**:
1. Verify scope configuration
2. Check acquisition boundary assignments
3. Verify business unit assignments
4. Check site restrictions

### Approval Workflow Issues

**Problem**: Approvals not routing correctly
**Solution**:
1. Verify approver role assignments
2. Check approval permissions
3. Verify workflow configuration
4. Check scope restrictions on approvers

---

## Related Documentation

- [Agent Configuration Guide](agent-configuration.md)
- [Workflow Management Guide](workflow-management.md)
- [RBAC Configuration](../infrastructure/rbac-configuration.md)
