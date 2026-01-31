# Application Manager Training

**SPDX-License-Identifier: Apache-2.0**

## Learning Objectives

By the end of this training, you will be able to:
1. Use Planning Agent to create deployment plans from natural language requests
2. Use Discovery Agent to discover and normalize applications
3. Use Request Coordination Agent to track service requests and monitor SLA compliance
4. Coordinate deployment workflows across multiple agents
5. Understand risk classification and approval workflows

---

## Key Concepts

### Agent Overview

**Planning Agent (E20)**:
- Generates deployment plans from natural language
- Assigns devices to deployment rings
- Performs blast radius analysis
- Creates rollback plans

**Discovery Agent (E14)**:
- Discovers applications from multiple sources
- Normalizes application names
- Identifies license and patch gaps

**Request Coordination Agent (E16)**:
- Tracks ServiceNow requests
- Monitors SLA compliance
- Manages escalations
- Coordinates stakeholder communications

### Risk Classification

- **R1 (Autonomous)**: Low-risk operations that execute automatically
- **R2 (Approval Required)**: Medium-risk operations requiring approval
- **R3 (Mandatory Approval)**: High-risk operations requiring CAB approval

---

## Hands-On Exercises

### Exercise 1: Creating a Deployment Plan

**Objective**: Create a deployment plan using natural language

**Steps**:
1. Navigate to **Planning** dashboard
2. Click **Generate Plan**
3. Enter request: "Deploy Office 365 v2.4 to IT department first, then Finance. Start with 10 devices in Ring 1."
4. Review generated plan:
   - Application and version
   - Ring assignments
   - Risk assessment
   - AI reasoning
5. Modify plan if needed
6. Submit for approval

**Expected Outcome**: Deployment plan created with ring assignments and risk assessment

### Exercise 2: Discovering Applications

**Objective**: Discover applications and identify gaps

**Steps**:
1. Navigate to **Discovery** dashboard
2. Go to **Sources** tab
3. Verify discovery sources are configured
4. Go to **Runs** tab
5. Click **Start Discovery**
6. Select source (e.g., SCCM)
7. Monitor discovery progress
8. Review discovered applications:
   - Application list
   - Normalized applications
   - License gaps
   - Patch gaps

**Expected Outcome**: Applications discovered with gaps identified

### Exercise 3: Tracking Service Requests

**Objective**: Track service requests and monitor SLA compliance

**Steps**:
1. Navigate to **Request Coordination** dashboard
2. Go to **Requests** tab
3. View request list with SLA status
4. Select a request
5. Review request details:
   - Status and priority
   - SLA due date
   - Escalation status
   - Stakeholders
6. Add stakeholders if needed
7. Send communication to stakeholders
8. Monitor SLA compliance

**Expected Outcome**: Request tracked with SLA monitoring

### Exercise 4: Coordinating Multi-Agent Workflow

**Objective**: Coordinate deployment using multiple agents

**Steps**:
1. Create deployment plan (Planning Agent)
2. Verify application inventory (Discovery Agent)
3. Check vulnerabilities (SecOps Agent - if accessible)
4. Create change record (Change Communications Agent)
5. Track deployment request (Request Coordination Agent)
6. Monitor deployment progress
7. Send completion notifications

**Expected Outcome**: Deployment coordinated across multiple agents

---

## Assessment Checklist

- [ ] Can create deployment plan from natural language request
- [ ] Can assign devices to deployment rings
- [ ] Can perform blast radius analysis
- [ ] Can discover applications from multiple sources
- [ ] Can identify license and patch gaps
- [ ] Can track service requests
- [ ] Can monitor SLA compliance
- [ ] Can coordinate multi-agent workflows
- [ ] Understands risk classification (R1/R2/R3)
- [ ] Knows when approval is required

---

## Quick Reference Card

### Planning Agent
- **Create Plan**: Planning → Generate Plan
- **View Plans**: Planning → Plans
- **Ring Assignment**: Planning → Rings
- **Blast Radius**: Planning → Blast Radius

### Discovery Agent
- **Start Discovery**: Discovery → Runs → Start Discovery
- **View Applications**: Discovery → Applications
- **License Gaps**: Discovery → License Gaps
- **Patch Gaps**: Discovery → Patch Gaps

### Request Coordination Agent
- **View Requests**: Request Coordination → Requests
- **Add Stakeholders**: Request → Stakeholders
- **Send Communication**: Request → Communications
- **Monitor SLA**: Request Coordination → Dashboard

---

## Related Documentation

- [Planning Agent User Guide](../user-guides/planning-agent.md)
- [Discovery Agent User Guide](../user-guides/discovery-agent.md)
- [Request Coordination Agent User Guide](../user-guides/request-coordination-agent.md)
- [Workflow Management Guide](../admin-guides/workflow-management.md)
