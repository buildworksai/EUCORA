# Service Manager Training

**SPDX-License-Identifier: Apache-2.0**

## Learning Objectives

By the end of this training, you will be able to:
1. Use SLA Governance Agent to define and manage SLAs
2. Configure KPIs and track KPI measurements
3. Monitor SLA compliance and detect breaches
4. Use natural language to create SLA definitions
5. Generate SLA compliance reports

---

## Key Concepts

### SLA Governance Agent Overview

**SLA Definition**:
- Create SLAs with natural language support
- Define SLA targets (response time, resolution time, availability)
- Link SLAs to service catalog items
- Version SLAs over time

**KPI Tracking**:
- Define KPIs linked to SLAs
- Track KPI measurements
- Monitor KPI compliance

**Compliance Monitoring**:
- Track SLA compliance in real-time
- Detect SLA breaches
- Generate compliance reports

---

## Hands-On Exercises

### Exercise 1: Creating SLA Definition

**Objective**: Create SLA using natural language

**Steps**:
1. Navigate to **SLA Governance** dashboard
2. Go to **SLAs** tab
3. Click **Create SLA**
4. Enter basic information:
   - Name and description
   - Service (from service catalog)
   - Version
   - Effective dates
5. Define SLA targets:
   - Response time (e.g., 4 hours)
   - Resolution time (e.g., 24 hours)
   - Availability (e.g., 99.9%)
   - Uptime (e.g., 99.5%)
6. Submit for approval
7. After approval, SLA becomes active

**Expected Outcome**: SLA definition created and activated

### Exercise 2: Using Natural Language SLA Creation

**Objective**: Create SLA from natural language request

**Steps**:
1. Navigate to **SLA Governance** → **SLAs** → **Parse Request**
2. Enter natural language request:
   - Example: "Service requests must be responded to within 4 hours and resolved within 24 hours. Availability must be 99.9%."
3. Review parsed SLA definition:
   - Extracted targets
   - Service mapping
   - Suggested KPIs
4. Modify if needed
5. Save and submit for approval

**Expected Outcome**: SLA created from natural language

### Exercise 3: Configuring KPIs

**Objective**: Define KPIs and link to SLA

**Steps**:
1. Navigate to **SLA Governance** → **KPIs**
2. Click **Create KPI**
3. Define KPI:
   - Name and type (Response Time, Resolution Time, Availability, Customer Satisfaction)
   - Measurement method
   - Target value
4. Save KPI
5. Link to SLA:
   - Go to SLA details
   - Add KPI link
   - Configure measurement frequency
6. Monitor KPI measurements:
   - Go to **Measurements** tab
   - Review measurement history
   - Check target compliance

**Expected Outcome**: KPIs defined and linked to SLA

### Exercise 4: Monitoring SLA Compliance

**Objective**: Monitor SLA compliance and detect breaches

**Steps**:
1. Navigate to **SLA Governance** → **Compliance**
2. View compliance records:
   - SLA name
   - Compliance period
   - Overall compliance percentage
   - Target compliance details
3. Filter by SLA and date range
4. Review compliance details:
   - KPI-level compliance
   - Breach history
   - Trend analysis
5. Go to **Breaches** tab
6. Review SLA breaches:
   - Breach type
   - Breach time and duration
   - Affected requests
   - Resolution status
7. Resolve breaches:
   - Add resolution notes
   - Update status
   - Document corrective actions

**Expected Outcome**: SLA compliance monitored and breaches resolved

---

## Assessment Checklist

- [ ] Can create SLA definitions
- [ ] Can use natural language to create SLAs
- [ ] Can configure KPIs
- [ ] Can link KPIs to SLAs
- [ ] Can monitor SLA compliance
- [ ] Can detect and resolve SLA breaches
- [ ] Can generate compliance reports
- [ ] Understands SLA approval workflow
- [ ] Knows how to update SLAs

---

## Quick Reference Card

### SLA Governance Agent
- **Create SLA**: SLA Governance → SLAs → Create
- **Parse Request**: SLA Governance → SLAs → Parse Request
- **Configure KPIs**: SLA Governance → KPIs
- **Monitor Compliance**: SLA Governance → Compliance
- **View Breaches**: SLA Governance → Breaches
- **Generate Reports**: SLA Governance → Reports

### Common SLA Targets
- **Response Time**: 4 hours (standard), 1 hour (critical)
- **Resolution Time**: 24 hours (standard), 4 hours (critical)
- **Availability**: 99.9% (standard), 99.99% (critical)
- **Uptime**: 99.5% (standard), 99.9% (critical)

---

## Related Documentation

- [SLA Governance Agent User Guide](../user-guides/sla-governance-agent.md)
- [Request Coordination Agent User Guide](../user-guides/request-coordination-agent.md)
- [Agent Configuration Guide](../admin-guides/agent-configuration.md)
