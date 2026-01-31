# SRE Team Training

**SPDX-License-Identifier: Apache-2.0**

## Learning Objectives

By the end of this training, you will be able to:
1. Use SRE Agent to configure monitoring and health checks
2. Define and monitor SLOs with error budget tracking
3. Create and execute self-healing rules
4. Manage runbooks and execute runbook automation
5. Understand self-healing approval workflows

---

## Key Concepts

### SRE Agent Overview

**Monitoring Integration**:
- Connects to Prometheus, Datadog, Azure Monitor, New Relic
- Collects metrics and health data
- Tracks service availability

**SLO Management**:
- Defines Service Level Objectives
- Tracks error budgets
- Monitors SLO compliance

**Self-Healing Automation**:
- Automated remediation based on health checks
- Self-healing rules with approval gates
- Automated runbook execution

---

## Hands-On Exercises

### Exercise 1: Configuring Health Checks

**Objective**: Set up health endpoint monitoring

**Steps**:
1. Navigate to **SRE** dashboard
2. Go to **Health Endpoints** tab
3. Click **Add Endpoint**
4. Configure endpoint:
   - Name and description
   - Application (optional)
   - URL and HTTP method
   - Expected status code
   - Timeout and check interval
5. Save and activate endpoint
6. Monitor health check results:
   - Go to **Health Check Results**
   - View check history
   - Review response times
   - Check status trends

**Expected Outcome**: Health endpoint configured and monitored

### Exercise 2: Defining SLOs

**Objective**: Create SLO definition and monitor compliance

**Steps**:
1. Navigate to **SRE** → **SLOs**
2. Click **Create SLO**
3. Define SLO:
   - Name and service name
   - SLO type (Availability, Latency, Error Rate, Throughput)
   - Target value (e.g., 99.9% availability)
   - Measurement window (default: 30 days)
4. Save and activate SLO
5. Monitor SLO compliance:
   - View SLO metrics
   - Check error budget status
   - Review burn rate
   - Monitor target compliance

**Expected Outcome**: SLO defined and compliance monitored

### Exercise 3: Creating Self-Healing Rules

**Objective**: Create self-healing rule for automated remediation

**Steps**:
1. Navigate to **SRE** → **Self-Healing Rules**
2. Click **Create Rule**
3. Configure rule:
   - Name and description
   - Trigger type (Health Check Failure, SLO Breach, Metric Threshold)
   - Trigger conditions (e.g., 3 consecutive failures)
   - Remediation script
   - Risk level (Low, Medium, High, Critical)
   - Approval requirement
4. Save and activate rule
5. Test rule:
   - Click **Test** on rule
   - Review test results
6. Monitor rule executions:
   - Go to **Self-Healing Executions**
   - Review execution history
   - Approve pending executions if needed

**Expected Outcome**: Self-healing rule created and tested

### Exercise 4: Managing Runbooks

**Objective**: Create and execute runbook

**Steps**:
1. Navigate to **SRE** → **Runbooks**
2. Click **Create Runbook**
3. Define runbook:
   - Name and category
   - Risk level
   - Steps (ordered list of actions)
   - Prerequisites and notes
4. Save and activate runbook
5. Execute runbook:
   - Select runbook
   - Click **Execute**
   - Provide trigger reason
   - Monitor execution progress
   - Complete steps as needed

**Expected Outcome**: Runbook created and executed

---

## Assessment Checklist

- [ ] Can configure health endpoints
- [ ] Can define SLOs
- [ ] Can monitor SLO compliance and error budgets
- [ ] Can create self-healing rules
- [ ] Can approve self-healing executions
- [ ] Can create and execute runbooks
- [ ] Understands monitoring platform integration
- [ ] Knows when approval is required for self-healing
- [ ] Can troubleshoot SLO breaches

---

## Quick Reference Card

### SRE Agent
- **Health Endpoints**: SRE → Health Endpoints
- **Health Check Results**: SRE → Health Check Results
- **SLOs**: SRE → SLOs
- **Error Budget**: SLO → Error Budget
- **Self-Healing Rules**: SRE → Self-Healing Rules
- **Self-Healing Executions**: SRE → Self-Healing Executions
- **Runbooks**: SRE → Runbooks
- **Runbook Executions**: SRE → Runbook Executions

### Common SLO Targets
- **Availability**: 99.9% (3 nines) or 99.99% (4 nines)
- **Latency**: P95 < 200ms
- **Error Rate**: < 0.1%
- **Throughput**: > 1000 requests/second

---

## Related Documentation

- [SRE Agent User Guide](../user-guides/sre-agent.md)
- [Agent Configuration Guide](../admin-guides/agent-configuration.md)
- [Integration Setup Guide](../admin-guides/integration-setup.md)
- [Monitoring Agents Guide](../admin-guides/monitoring-agents.md)
