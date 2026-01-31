# E19: SLA Governance Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P2-High
**Sprint**: 19-20 (Weeks 37-40)
**Dependencies**: E3 (RBAC), E7 (pgvector), E8 (AI Workflows), E18 (SRE Agent)
**ALM L2 Category**: Service Level Management

---

## Overview

The SLA Governance Agent allows users to use natural language queries/commands to create new SLAs, update KPIs, and track performance trends. It offloads repeatable tasks to the agent such as creating a draft SLA given general inputs.

### Key Benefits

- Natural language SLA creation
- Automated KPI tracking
- Performance trend analysis
- Draft SLA generation from templates
- Contract compliance monitoring

### Data Sources

- ServiceNow ITSM
- SLA/KPI dashboards
- Contract repositories
- Performance metrics

---

## Requirements

### 1. Natural Language SLA Creation

**Capabilities**:
- Parse natural language SLA requirements
- Generate structured SLA definitions
- Map to service catalog items
- Create approval workflows

**Example Inputs**:
- "Create an SLA for the HR portal with 99.5% uptime during business hours"
- "Update the email service SLA to include 4-hour response time"
- "Show me all SLAs that are at risk this month"

### 2. KPI Management

**KPI Types**:
- Availability KPIs
- Performance KPIs
- Response time KPIs
- Resolution time KPIs
- Quality KPIs

**Capabilities**:
- Define KPIs from natural language
- Link KPIs to SLAs
- Calculate KPI values automatically
- Track trends over time

### 3. Performance Tracking

**Metrics**:
- SLA compliance rate
- Breach count and severity
- Near-miss tracking
- Trend analysis
- Predictive compliance

### 4. Contract Integration

**Capabilities**:
- Import SLA terms from contracts
- Map contract obligations to metrics
- Track contractual compliance
- Generate compliance evidence

---

## Data Model

### Django Models

```python
# apps/sla_governance/models.py

class ServiceCatalogItem(TimeStampedModel):
    """Service catalog item for SLA attachment."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    owner = models.CharField(max_length=255)
    status = models.CharField(max_length=20)
    servicenow_sys_id = models.CharField(max_length=100, null=True)

class SLADefinition(TimeStampedModel, CorrelationIdModel):
    """Service Level Agreement definition."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    service = models.ForeignKey(ServiceCatalogItem, on_delete=models.CASCADE)
    version = models.CharField(max_length=50)
    effective_from = models.DateField()
    effective_until = models.DateField(null=True)
    status = models.CharField(max_length=20)  # draft, pending_approval, active, expired

    # Natural language source
    original_request = models.TextField(null=True)

    # Approval
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_slas')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_slas')
    approved_at = models.DateTimeField(null=True)

class SLATarget(TimeStampedModel):
    """SLA target/objective."""
    sla = models.ForeignKey(SLADefinition, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    metric_type = models.CharField(max_length=50)  # availability, response_time, resolution_time, quality
    target_value = models.FloatField()
    target_unit = models.CharField(max_length=20)  # percent, hours, minutes, score
    measurement_period = models.CharField(max_length=20)  # daily, weekly, monthly
    applies_to = models.JSONField(null=True)  # time windows, customer segments, etc.

class KPIDefinition(TimeStampedModel):
    """Key Performance Indicator definition."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    formula = models.TextField()
    data_sources = models.JSONField()
    unit = models.CharField(max_length=50)
    direction = models.CharField(max_length=10)  # higher_better, lower_better
    thresholds = models.JSONField()  # warning, critical thresholds
    is_active = models.BooleanField(default=True)

class SLAKPILink(TimeStampedModel):
    """Link between SLA target and KPI."""
    sla_target = models.ForeignKey(SLATarget, on_delete=models.CASCADE)
    kpi = models.ForeignKey(KPIDefinition, on_delete=models.CASCADE)
    weight = models.FloatField(default=1.0)

class KPIMeasurement(TimeStampedModel):
    """KPI measurement value."""
    kpi = models.ForeignKey(KPIDefinition, on_delete=models.CASCADE)
    measurement_time = models.DateTimeField()
    value = models.FloatField()
    status = models.CharField(max_length=20)  # green, yellow, red
    data_points = models.JSONField(null=True)

class SLACompliance(TimeStampedModel, CorrelationIdModel):
    """SLA compliance record."""
    sla = models.ForeignKey(SLADefinition, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    overall_compliance = models.FloatField()
    target_compliances = models.JSONField()  # per-target compliance
    breach_count = models.IntegerField(default=0)
    near_miss_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20)  # compliant, at_risk, breached

class SLABreach(TimeStampedModel, CorrelationIdModel):
    """SLA breach incident."""
    sla = models.ForeignKey(SLADefinition, on_delete=models.CASCADE)
    target = models.ForeignKey(SLATarget, on_delete=models.CASCADE)
    breach_time = models.DateTimeField()
    severity = models.CharField(max_length=20)
    target_value = models.FloatField()
    actual_value = models.FloatField()
    root_cause = models.TextField(null=True)
    remediation = models.TextField(null=True)
    servicenow_incident = models.CharField(max_length=50, null=True)

class SLATemplate(TimeStampedModel):
    """SLA template for quick creation."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100)
    default_targets = models.JSONField()
    variables = models.JSONField()  # placeholders to fill
    is_active = models.BooleanField(default=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "sla_governance_workflow",
  "agent_type": "sla_governance",
  "risk_level": "R2",
  "steps": [
    {
      "name": "parse_request",
      "description": "Parse natural language SLA request",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "identify_service",
      "description": "Identify or create service catalog item",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_sla_draft",
      "description": "Generate SLA definition draft",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "define_targets",
      "description": "Define SLA targets and thresholds",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "link_kpis",
      "description": "Link or create KPIs for measurement",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "review_and_approve",
      "description": "Submit for review and approval",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review SLA definition before activation"
    },
    {
      "name": "activate_sla",
      "description": "Activate SLA and begin monitoring",
      "risk_level": "R2",
      "requires_approval": true
    }
  ],
  "policy_requirements": [
    "sla_policy",
    "contract_policy"
  ]
}
```

---

## Natural Language Processing

### Example Conversations

**User**: "Create an SLA for the CRM application with 99.9% availability during business hours (8am-6pm EST) and 99% during off-hours."

**Agent Response**:
```
I'll create an SLA for the CRM application with the following targets:

**Service**: CRM Application
**Targets**:
1. Availability (Business Hours): 99.9%
   - Period: Monday-Friday, 8:00 AM - 6:00 PM EST
   - Measurement: Monthly

2. Availability (Off-Hours): 99.0%
   - Period: Evenings, weekends, holidays
   - Measurement: Monthly

Would you like me to:
- Add response time targets?
- Link to existing KPIs?
- Use a template for additional terms?

[Create Draft SLA]
```

**User**: "Show me all SLAs that are at risk this month"

**Agent Response**:
```
**SLAs At Risk (January 2026)**

| SLA | Service | Compliance | Error Budget | Status |
|-----|---------|------------|--------------|--------|
| CRM-SLA-001 | CRM App | 99.2% (target: 99.9%) | 12% remaining | ⚠️ At Risk |
| HR-SLA-003 | HR Portal | 98.5% (target: 99.5%) | 0% remaining | 🔴 Breached |

**Details for CRM-SLA-001**:
- 2 near-misses this month
- Primary issue: Database latency
- Recommended action: Scale database resources

[View Details] [Create Incident] [Adjust Target]
```

---

## API Endpoints

```
# SLA Definitions
GET/POST /api/sla-governance/slas/
GET/PUT/DELETE /api/sla-governance/slas/{id}/
POST /api/sla-governance/slas/{id}/approve/
POST /api/sla-governance/slas/{id}/activate/

# Natural Language
POST /api/sla-governance/parse-request/
POST /api/sla-governance/generate-sla/

# SLA Targets
GET/POST /api/sla-governance/slas/{id}/targets/

# KPIs
GET/POST /api/sla-governance/kpis/
GET /api/sla-governance/kpis/{id}/measurements/

# Compliance
GET /api/sla-governance/compliance/
GET /api/sla-governance/compliance/at-risk/
GET /api/sla-governance/compliance/{sla_id}/history/

# Breaches
GET /api/sla-governance/breaches/
POST /api/sla-governance/breaches/{id}/root-cause/

# Templates
GET/POST /api/sla-governance/templates/

# Reports
GET /api/sla-governance/reports/summary/
GET /api/sla-governance/reports/trends/
```

---

## Frontend Components

### 1. SLA Governance Dashboard

```
AI Agents > SLA Governance
├── Compliance Overview
│   ├── Overall compliance gauge
│   ├── At-risk SLAs
│   ├── Recent breaches
│   └── Trend chart
├── SLA Chat Interface
│   ├── Natural language input
│   ├── Conversation history
│   └── Quick actions
├── SLA Library
│   ├── Active SLAs
│   ├── Draft SLAs
│   ├── Expired SLAs
│   └── Templates
├── KPI Dashboard
│   ├── KPI cards
│   ├── Threshold status
│   └── Trend sparklines
└── Breach Analysis
    ├── Recent breaches
    ├── Root cause analysis
    └── Remediation tracking
```

---

## Acceptance Criteria

- [ ] Natural language SLA parsing
- [ ] SLA draft generation
- [ ] KPI definition and linking
- [ ] Compliance calculation
- [ ] Breach detection and alerting
- [ ] Trend analysis
- [ ] ServiceNow integration
- [ ] Template library
- [ ] Chat interface for NL queries
- [ ] ≥90% test coverage
