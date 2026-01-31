# AI Agent Specifications — Application & Portfolio Management

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Phase**: 0 — Foundation
**Document Version**: 1.0
**Date**: 2026-01-30

---

## Overview

This document specifies three new AI agent types to support Application & Portfolio Management workflows:

1. **Application Management Agent**: Assists Application Managers with lifecycle orchestration, dependency management, and health monitoring
2. **Portfolio Management Agent**: Assists Portfolio Managers with optimization, team performance analysis, and strategic planning
3. **License Management Agent**: Provides comprehensive license optimization with true-up forecasting and compliance automation

All agents follow the **"AI recommends, human decides"** governance model: NO autonomous actions — all recommendations require explicit human approval.

---

## 1. Application Management Agent

### Agent Type ID
```python
APPLICATION_MANAGEMENT = "application_management", "Application Management Agent"
```

### Purpose
Assist Application Managers with orchestrating deployments, managing dependencies, monitoring application health, and responding to incidents.

### Core Capabilities

#### 1.1 Dependency Analysis & Compatibility Checking

**Use Case**: Application Manager wants to deploy Office 365 update, needs to ensure no conflicts with in-flight deployments or dependent applications.

**Agent Capabilities**:
- Analyze application dependency graph (ApplicationDependency model)
- Identify downstream dependencies (applications that depend on this one)
- Check for in-flight deployments that may conflict
- Recommend deployment timing to minimize blast radius

**Example Prompt Template**:
```
You are an Application Management Agent assisting {application_manager_name} with deploying {application_name} version {version}.

## Context
- Application: {application_name}
- Version: {version}
- Target Ring: {target_ring}
- Scheduled Start: {scheduled_start}

## Dependencies
{dependency_graph_json}

## In-Flight Deployments
{in_flight_deployments_json}

## Task
Analyze dependencies and in-flight deployments. Identify potential conflicts or risks. Recommend:
1. Safe deployment timing (avoid conflicts)
2. Coordination requirements (stakeholders to notify)
3. Dependency update sequence (if multiple apps need updates)
4. Rollback plan considerations (if dependencies fail)

Provide recommendations in JSON format:
{
  "status": "SAFE" | "WARNING" | "BLOCKED",
  "conflicts": [...],
  "recommendations": [...],
  "coordination_required": [...]
}
```

**API Integration**:
```python
POST /api/v1/ai/agents/application-management/analyze-dependencies/
{
  "application_id": "uuid",
  "version": "2.5.1",
  "target_ring": "RING_2",
  "scheduled_start": "2027-02-15T09:00:00Z"
}

Response:
{
  "status": "WARNING",
  "conflicts": [
    {
      "type": "in_flight_deployment",
      "application": "Microsoft Teams",
      "issue": "Shared dependency on .NET 8.0, Teams deployment scheduled for same window"
    }
  ],
  "recommendations": [
    {
      "action": "delay_deployment",
      "reason": "Wait for Microsoft Teams deployment to complete (ETA: 2027-02-16)",
      "priority": "HIGH"
    },
    {
      "action": "coordinate_with_stakeholder",
      "stakeholder": "Sarah Chen (Teams App Manager)",
      "message": "Coordinate deployment schedules to avoid .NET dependency conflicts"
    }
  ],
  "coordination_required": [
    {
      "stakeholder": "Sarah Chen",
      "application": "Microsoft Teams",
      "reason": "Shared dependency coordination"
    }
  ]
}
```

#### 1.2 Health Anomaly Detection

**Use Case**: Application Manager notices application health degrading from 95% to 85% over 3 days. Agent analyzes metrics and identifies root cause.

**Agent Capabilities**:
- Analyze ApplicationHealth time-series data
- Correlate health degradation with deployment events, system changes
- Identify error patterns from DeploymentMetric.error_summary
- Recommend remediation strategies

**Example Prompt Template**:
```
You are an Application Management Agent analyzing health degradation for {application_name}.

## Health Metrics (Last 7 Days)
{health_metrics_timeseries_json}

## Recent Deployment Events
{deployment_events_json}

## Error Summary
{error_summary_json}

## Task
Analyze health degradation pattern. Identify root cause. Recommend remediation strategy.

Provide analysis in JSON format:
{
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "root_cause": {
    "primary": "...",
    "confidence": 0.0-1.0,
    "evidence": [...]
  },
  "affected_devices": [...],
  "remediation_recommendations": [...]
}
```

#### 1.3 Deployment Timing Optimization

**Use Case**: Application Manager wants to deploy Security Update for Adobe Acrobat. Agent recommends optimal timing based on risk calendar, user impact, and business cycles.

**Agent Capabilities**:
- Analyze historical deployment success rates by day/time
- Consider business cycles (avoid month-end, quarter-end)
- Factor in user impact (deploy during low-usage windows)
- Check risk calendar (avoid concurrent high-risk deployments)

**Example Recommendations**:
```json
{
  "recommended_start": "2027-02-18T02:00:00Z",
  "rationale": [
    "Tuesday 2 AM: historical success rate 97% (vs 89% average)",
    "Avoid Monday (higher support load)",
    "Mid-month (avoid month-end accounting close)",
    "No other high-risk deployments scheduled this week"
  ],
  "alternative_windows": [
    {
      "start": "2027-02-20T02:00:00Z",
      "success_rate_expected": 0.95,
      "notes": "Thursday 2 AM, backup option"
    }
  ]
}
```

#### 1.4 Incident Correlation & Root Cause Analysis

**Use Case**: Multiple applications showing failures after deployment. Agent correlates incidents across applications to identify shared root cause (e.g., .NET runtime update broke dependencies).

**Agent Capabilities**:
- Correlate incidents across multiple applications
- Identify shared dependencies, system changes, or execution plane issues
- Generate incident report with timeline, impact, root cause
- Recommend preventive measures

**Example Output**:
```json
{
  "incident_id": "INC-2027-0042",
  "affected_applications": [
    "Microsoft Office 365",
    "Adobe Acrobat",
    "Zoom Client"
  ],
  "root_cause": {
    "category": "shared_dependency_failure",
    "component": ".NET 8.0 Runtime",
    "issue": "Deployment of .NET 8.0.3 broke compatibility with Office/Acrobat/Zoom",
    "confidence": 0.92
  },
  "timeline": [
    {"time": "2027-02-15 09:00", "event": ".NET 8.0.3 deployed to Ring 2"},
    {"time": "2027-02-15 10:30", "event": "Office 365 failures spike (Ring 2 devices)"},
    {"time": "2027-02-15 11:15", "event": "Acrobat failures spike (Ring 2 devices)"}
  ],
  "remediation": {
    "immediate": "Rollback .NET 8.0.3 to 8.0.2 for affected devices",
    "short_term": "Test .NET 8.0.3 compatibility with Office/Acrobat/Zoom in lab",
    "long_term": "Implement dependency compatibility matrix testing before Ring 2"
  },
  "preventive_measures": [
    "Add pre-deployment compatibility testing for shared runtimes",
    "Coordinate .NET updates with all dependent app managers",
    "Implement staged rollout for runtime updates (Lab → Canary only initially)"
  ]
}
```

### Agent Workflow Integration

**UI Integration Points**:

1. **Application Detail View → Deployment Tab**:
   - Button: "AI: Analyze Deployment Risks"
   - Opens modal with dependency analysis, timing recommendations

2. **Application Detail View → Health Tab**:
   - Button: "AI: Diagnose Health Issues"
   - Opens modal with root cause analysis, remediation recommendations

3. **Deployment Wizard → Schedule Step**:
   - AI suggestion: "Recommended deployment window: Tuesday 2 AM (97% success rate)"
   - Rationale tooltip with explanation

4. **Incident Detail View**:
   - Button: "AI: Correlate Incidents"
   - Opens modal with cross-application incident correlation

### Performance Requirements

- **Response Time**: ≤5 seconds for dependency analysis (cached dependency graph)
- **Response Time**: ≤10 seconds for health anomaly detection (query last 30 days metrics)
- **Accuracy**: ≥85% for root cause identification (validated against historical incidents)
- **Token Budget**: ≤10k tokens per recommendation (optimize prompt engineering)

---

## 2. Portfolio Management Agent

### Agent Type ID
```python
PORTFOLIO_MANAGEMENT = "portfolio_management", "Portfolio Management Agent"
```

### Purpose
Assist Portfolio Managers with portfolio optimization, team performance analysis, cost management, and strategic planning.

### Core Capabilities

#### 2.1 Portfolio Optimization Recommendations

**Use Case**: Portfolio Manager reviews their portfolio quarterly and asks agent to identify optimization opportunities (sunset, consolidate, upgrade).

**Agent Capabilities**:
- Analyze application health, usage, cost across portfolio
- Identify sunset candidates (low health, low usage, high cost)
- Recommend consolidation opportunities (duplicate functionality)
- Suggest upgrade paths (outdated versions with security vulnerabilities)
- Calculate ROI for each recommendation

**Example Prompt Template**:
```
You are a Portfolio Management Agent analyzing {portfolio_name} for optimization opportunities.

## Portfolio Applications (N={application_count})
{applications_summary_json}

## Portfolio Metrics
- Total Cost: ${total_cost}
- Avg Health Score: {avg_health_score}
- Compliance Score: {compliance_score}%

## Task
Identify optimization opportunities. Categorize as:
1. SUNSET: Applications to retire (low usage, high cost, redundant)
2. CONSOLIDATE: Duplicate functionality across multiple apps
3. UPGRADE: Outdated versions with security/compliance risks
4. RIGHT-SIZE: Over-provisioned licenses or entitlements

Provide recommendations in JSON format:
{
  "sunset_candidates": [...],
  "consolidation_opportunities": [...],
  "upgrade_priorities": [...],
  "license_optimization": [...]
}
```

**Example Output**:
```json
{
  "summary": {
    "total_opportunities": 12,
    "potential_savings": 145000,
    "risk_reduction": "23% fewer critical vulnerabilities"
  },
  "sunset_candidates": [
    {
      "application": "Legacy CRM System",
      "rationale": [
        "Usage: 12 active users (down from 150 last year)",
        "Cost: $25k/year licenses",
        "Alternative: Salesforce already deployed with CRM capabilities",
        "Health: 65% (degraded)"
      ],
      "savings": 25000,
      "migration_effort": "LOW (12 users)",
      "recommendation": "Migrate 12 users to Salesforce, sunset Legacy CRM by Q2"
    }
  ],
  "consolidation_opportunities": [
    {
      "applications": ["Microsoft Teams", "Slack", "Zoom Chat"],
      "rationale": [
        "Redundant chat/collaboration functionality",
        "Teams has highest adoption (85% of users)",
        "Slack: $15k/year, Zoom Chat included in Zoom licenses"
      ],
      "savings": 15000,
      "recommendation": "Standardize on Microsoft Teams, sunset Slack"
    }
  ],
  "upgrade_priorities": [
    {
      "application": "Java Runtime",
      "current_version": "8u202",
      "recommended_version": "17.0.6",
      "rationale": [
        "Current version EOL since 2022",
        "12 critical CVEs (CVSS ≥ 9.0)",
        "Compliance violation (corporate policy requires supported versions)"
      ],
      "urgency": "CRITICAL",
      "affected_devices": 2300
    }
  ],
  "license_optimization": [
    {
      "sku": "Microsoft 365 E5",
      "entitled": 500,
      "consumed": 350,
      "wasted": 150,
      "cost_per_license": 57,
      "potential_savings": 8550,
      "recommendation": "Reduce E5 entitlements from 500 to 400 (retain 50 buffer)"
    }
  ]
}
```

#### 2.2 Team Performance Insights & Coaching

**Use Case**: Portfolio Manager reviews quarterly team performance and asks agent to identify Application Managers needing coaching or support.

**Agent Capabilities**:
- Analyze ApplicationManagerPerformance metrics across team
- Identify underperformers (composite score < 70)
- Diagnose performance issues (low success rate, slow velocity, poor license efficiency)
- Generate coaching recommendations (training, resource allocation, process improvements)

**Example Output**:
```json
{
  "team_summary": {
    "total_managers": 8,
    "avg_composite_score": 82.5,
    "top_performer": {
      "name": "Sarah Chen",
      "score": 94.2
    },
    "needs_support": [
      {
        "name": "Mike Johnson",
        "score": 68.5
      }
    ]
  },
  "underperformers": [
    {
      "manager": "Mike Johnson",
      "composite_score": 68.5,
      "performance_breakdown": {
        "success_rate": 87,  // Target: 95%
        "avg_health_score": 78,  // Target: 90%
        "license_utilization": 62,  // Target: 70-85%
        "time_to_deployment": 19,  // Target: 14 days
        "mttr": 6.5  // Target: 4 hours
      },
      "root_causes": [
        "Success rate below target (87% vs 95%): 3 failed deployments last quarter",
        "Slow deployment velocity (19 days vs 14 target): CAB submissions often incomplete",
        "Low license utilization (62%): Over-entitled across multiple SKUs"
      ],
      "coaching_recommendations": [
        {
          "area": "CAB Evidence Preparation",
          "issue": "CAB submissions often rejected due to incomplete evidence packs",
          "recommendation": "Training: 'CAB Submission Best Practices' workshop",
          "expected_impact": "Reduce CAB rejection rate, improve time-to-deployment"
        },
        {
          "area": "License Management",
          "issue": "Applications consistently under-utilized (avg 62%)",
          "recommendation": "Coaching session: License right-sizing and forecasting techniques",
          "expected_impact": "Improve license efficiency to 70-85% range"
        },
        {
          "area": "Deployment Testing",
          "issue": "3 failed deployments due to inadequate Ring 0 validation",
          "recommendation": "Process improvement: Implement mandatory Ring 0 validation checklist",
          "expected_impact": "Improve success rate to 95%+"
        }
      ]
    }
  ],
  "top_performers": [
    {
      "manager": "Sarah Chen",
      "composite_score": 94.2,
      "strengths": [
        "Success rate: 98% (best in team)",
        "Avg time-to-deployment: 11 days (3 days ahead of target)",
        "License efficiency: 79% (optimal range)"
      ],
      "best_practices": [
        "Uses AI Packaging Assistant for all artifact creation (reduces errors)",
        "Proactive dependency analysis before every deployment (avoids conflicts)",
        "Monthly license reviews with harvesting campaigns (maintains optimal utilization)"
      ]
    }
  ]
}
```

#### 2.3 Cost Optimization & Budget Planning

**Use Case**: Portfolio Manager preparing for annual budget planning. Agent analyzes current spend, forecasts future costs, and identifies optimization opportunities.

**Agent Capabilities**:
- Analyze total portfolio cost (licenses + deployment overhead + support)
- Forecast future costs based on growth trends
- Identify cost optimization opportunities (vendor consolidation, license model changes)
- Generate budget proposal with justification

**Example Output**:
```json
{
  "current_year_summary": {
    "total_cost": 1250000,
    "breakdown": {
      "licenses": 950000,
      "deployment_overhead": 200000,
      "support": 100000
    },
    "budget": 1300000,
    "variance": 50000,
    "variance_percent": 3.8
  },
  "next_year_forecast": {
    "baseline_forecast": 1350000,
    "growth_drivers": [
      "Headcount growth: 15% (150 → 173 employees)",
      "New application: Salesforce CRM ($45k/year)",
      "Inflation: 3% on license renewals"
    ],
    "optimized_forecast": 1220000,
    "savings": 130000
  },
  "optimization_strategies": [
    {
      "strategy": "Vendor Consolidation",
      "description": "Consolidate Microsoft ELA (E3 + E5 → E5 only with volume discount)",
      "current_cost": 285000,
      "optimized_cost": 250000,
      "savings": 35000,
      "implementation": "Q2 2027 ELA renewal"
    },
    {
      "strategy": "License Harvesting",
      "description": "Reclaim unused licenses across all SKUs",
      "current_waste": 85000,
      "reclamation_potential": 60000,
      "savings": 60000,
      "implementation": "Quarterly harvesting campaigns"
    },
    {
      "strategy": "Sunset Legacy Applications",
      "description": "Retire 3 legacy applications (see portfolio optimization recommendations)",
      "current_cost": 50000,
      "savings": 45000,
      "implementation": "Q1-Q2 2027 migration"
    }
  ],
  "budget_proposal": {
    "requested_budget": 1250000,
    "justification": "Baseline growth offset by optimization strategies (-10.4%)",
    "confidence": 0.87,
    "risks": [
      "Headcount growth may exceed 15% (sales team expansion)",
      "Vendor price increases may exceed 3% inflation"
    ],
    "contingency_buffer": 50000
  }
}
```

#### 2.4 Risk Aggregation & Portfolio Health Monitoring

**Use Case**: Portfolio Manager wants real-time visibility into portfolio-level risks (high-risk deployments, compliance violations, security vulnerabilities).

**Agent Capabilities**:
- Aggregate risk scores across all portfolio applications
- Identify high-risk deployments requiring Portfolio Manager approval
- Flag compliance violations and security vulnerabilities
- Generate portfolio health heatmap

**Example Output**:
```json
{
  "portfolio_health": {
    "overall_score": 82,
    "trend": "STABLE",
    "applications_healthy": 45,
    "applications_degraded": 8,
    "applications_critical": 2
  },
  "risk_heatmap": [
    {
      "application": "Java Runtime",
      "risk_score": 85,
      "risk_category": "CRITICAL",
      "issues": [
        "12 critical CVEs (CVSS ≥ 9.0)",
        "EOL version (no vendor support)",
        "Compliance violation (corporate policy)"
      ],
      "urgency": "IMMEDIATE",
      "recommendation": "Emergency upgrade required"
    },
    {
      "application": "Adobe Acrobat",
      "risk_score": 68,
      "risk_category": "HIGH",
      "issues": [
        "Deployment failure rate: 15% (Ring 2)",
        "Rollback required for 45 devices",
        "Root cause: incompatibility with Windows 11 22H2"
      ],
      "urgency": "HIGH",
      "recommendation": "Halt Ring 3 promotion, investigate compatibility"
    }
  ],
  "compliance_violations": [
    {
      "application": "VPN Client",
      "policy": "All software must be on vendor-supported versions",
      "violation": "Version 5.0.03072 EOL since 2025-06-01",
      "affected_devices": 1200,
      "remediation": "Upgrade to version 5.1.00001 by 2027-03-31"
    }
  ],
  "pending_approvals": [
    {
      "application": "Microsoft Defender Update",
      "risk_score": 72,
      "status": "AWAITING_PORTFOLIO_MANAGER_APPROVAL",
      "submitted_by": "Mike Johnson",
      "submitted_at": "2027-02-15T14:30:00Z",
      "evidence_pack_url": "/evidence/e8a3f2c1"
    }
  ]
}
```

### Agent Workflow Integration

**UI Integration Points**:

1. **Portfolio Dashboard → Optimization Tab**:
   - Button: "AI: Analyze Optimization Opportunities"
   - Opens modal with sunset, consolidation, upgrade recommendations

2. **Portfolio Dashboard → Team Performance Tab**:
   - Button: "AI: Generate Coaching Insights"
   - Opens modal with underperformer analysis, coaching recommendations

3. **Portfolio Dashboard → Cost Analysis Tab**:
   - Button: "AI: Forecast Budget & Optimize Costs"
   - Opens modal with cost forecast, optimization strategies, budget proposal

4. **Portfolio Dashboard → Risk Heatmap**:
   - Auto-refreshed every 15 minutes
   - Clickable risk items drill down to application details

---

## 3. License Management Agent

### Agent Type ID
```python
LICENSE_MANAGEMENT = "license_management", "License Management Agent"
```

### Purpose
Provide comprehensive license optimization with true-up forecasting, compliance automation, and vendor negotiation intelligence. Deliver "absolute management capabilities" for license lifecycle.

### Core Capabilities

#### 3.1 True-Up Forecasting & Cost Prediction

**Use Case**: Portfolio Manager preparing for annual Microsoft ELA true-up. Agent forecasts consumption growth, estimates true-up cost, and recommends mitigation strategies.

**Agent Capabilities**:
- Model consumption growth trends (linear regression, exponential smoothing)
- Forecast license needs 6-12 months ahead
- Estimate true-up costs based on vendor pricing
- Recommend mitigation strategies (right-sizing, harvesting, model migration)
- Generate vendor negotiation brief

**Example Prompt Template**:
```
You are a License Management Agent forecasting true-up costs for {vendor_name}.

## Current State
- Vendor: {vendor_name}
- Contract Type: Enterprise License Agreement (ELA)
- Renewal Date: {renewal_date}
- Current Entitlements: {entitlements_json}
- Current Consumption: {consumption_json}
- Historical Consumption (12 months): {consumption_timeseries_json}

## Task
1. Forecast consumption for next 6 months using historical trends
2. Calculate additional licenses needed (forecast > entitled)
3. Estimate true-up cost impact
4. Recommend mitigation strategies to reduce true-up cost
5. Generate vendor negotiation brief

Provide forecast in JSON format:
{
  "forecast_summary": {...},
  "true_up_impact": {...},
  "mitigation_strategies": [...],
  "negotiation_brief": {...}
}
```

**Example Output**:
```json
{
  "forecast_summary": {
    "vendor": "Microsoft",
    "forecast_period": "2027-02 to 2027-07",
    "forecast_horizon_days": 180,
    "model_version": "v1.0",
    "confidence": 0.89
  },
  "current_state": {
    "entitled": 500,
    "consumed": 425,
    "utilization": 0.85,
    "waste": 75,
    "annual_cost": 285000
  },
  "forecast": {
    "consumption_forecast": 520,
    "growth_rate": 0.22,
    "growth_drivers": [
      "Headcount growth: 15% (historical trend)",
      "New Salesforce deployment: +30 E5 licenses",
      "Power BI adoption: +15 E5 licenses (advanced analytics)"
    ],
    "additional_licenses_needed": 20,
    "true_up_cost_estimate": 11400,
    "true_up_cost_per_license": 570
  },
  "mitigation_strategies": [
    {
      "strategy": "RIGHT_SIZING",
      "description": "Reduce over-entitled E3 licenses (150 entitled, 95 consumed)",
      "licenses_saved": 55,
      "cost_savings": 15675,
      "implementation": "Reduce E3 entitlements from 150 to 110 (retain 15% buffer)",
      "risk": "LOW",
      "timeline": "Immediate"
    },
    {
      "strategy": "LICENSE_HARVESTING",
      "description": "Reclaim E5 licenses from inactive users",
      "licenses_saved": 25,
      "cost_savings": 14250,
      "implementation": "Quarterly harvesting campaign (90-day inactivity threshold)",
      "risk": "LOW",
      "timeline": "Q2 2027"
    },
    {
      "strategy": "BUNDLE_OPTIMIZATION",
      "description": "Downgrade 40 E5 users to E3 (minimal advanced feature usage)",
      "licenses_saved_e5": 40,
      "licenses_added_e3": 40,
      "net_savings": 11400,
      "implementation": "Usage analysis shows 40 users not using Power BI, Advanced Threat Protection",
      "risk": "MEDIUM (user impact - require approval)",
      "timeline": "Q3 2027"
    }
  ],
  "mitigation_summary": {
    "total_licenses_saved": 120,
    "total_cost_savings": 41325,
    "net_true_up_cost": -29925,
    "recommendation": "Execute right-sizing and harvesting immediately. Bundle optimization requires user impact analysis."
  },
  "negotiation_brief": {
    "vendor": "Microsoft",
    "renewal_date": "2027-08-31",
    "current_annual_cost": 285000,
    "forecasted_cost_without_optimization": 296400,
    "optimized_cost_with_mitigations": 254675,
    "negotiation_points": [
      {
        "point": "Volume Discount Request",
        "justification": "Increased consumption (+22%) demonstrates commitment to Microsoft ecosystem",
        "ask": "Request 8% volume discount (current: 5%)",
        "potential_savings": 20376
      },
      {
        "point": "Multi-Year Commitment",
        "justification": "Offer 3-year ELA commitment in exchange for price lock",
        "ask": "Price freeze for 3 years (hedge against inflation)",
        "potential_savings": 25000
      },
      {
        "point": "Bundle Consolidation",
        "justification": "Simplify SKU management (E3 + E5 → E5 only with tiered pricing)",
        "ask": "Tiered E5 pricing (first 300: $570, next 200: $520)",
        "potential_savings": 10000
      }
    ],
    "negotiation_strategy": "Lead with multi-year commitment, emphasize growth and ecosystem adoption, request volume discount and price freeze",
    "walk_away_point": "Maximum acceptable cost: $280k (< 2% increase YoY)"
  }
}
```

#### 3.2 License Optimization Playbooks

**Use Case**: License Management Agent continuously monitors license utilization and proactively recommends optimization playbooks (right-sizing, harvesting, model migration).

**Playbook 1: Right-Sizing**
```json
{
  "playbook": "RIGHT_SIZING",
  "description": "Reduce over-entitled SKUs where entitled >> consumed",
  "opportunities": [
    {
      "sku": "Adobe Creative Cloud All Apps",
      "entitled": 200,
      "consumed": 145,
      "waste": 55,
      "utilization": 0.725,
      "cost_per_license": 660,
      "annual_waste_cost": 36300,
      "recommendation": {
        "action": "Reduce entitlements from 200 to 160 (retain 10% buffer)",
        "licenses_to_reclaim": 40,
        "savings": 26400,
        "risk": "LOW",
        "justification": "Consumption stable at 145 for 6 months, 10% buffer sufficient"
      }
    }
  ]
}
```

**Playbook 2: License Harvesting**
```json
{
  "playbook": "LICENSE_HARVESTING",
  "description": "Reclaim licenses from inactive users/devices",
  "opportunities": [
    {
      "sku": "Microsoft 365 E5",
      "inactive_threshold_days": 90,
      "inactive_assignments": [
        {
          "principal_type": "user",
          "principal_id": "john.doe@company.com",
          "assigned_at": "2026-01-15",
          "last_activity": "2026-10-20",
          "inactive_days": 103,
          "justification": "No activity for 103 days, user on extended leave"
        },
        {
          "principal_type": "user",
          "principal_id": "jane.smith@company.com",
          "assigned_at": "2026-03-10",
          "last_activity": "2026-11-05",
          "inactive_days": 87,
          "justification": "Minimal activity (login only), user transitioned to contractor role"
        }
      ],
      "total_harvestable": 25,
      "savings": 14250,
      "recommendation": {
        "action": "Revoke E5 licenses from 25 inactive users",
        "approval_required": true,
        "approval_from": "HR & Application Manager",
        "timeline": "Q2 2027 harvesting campaign"
      }
    }
  ]
}
```

**Playbook 3: Model Migration**
```json
{
  "playbook": "MODEL_MIGRATION",
  "description": "Change license model to reduce costs (user → device, perpetual → subscription, etc.)",
  "opportunities": [
    {
      "sku_current": "Adobe Acrobat Pro (User-based)",
      "sku_proposed": "Adobe Acrobat Pro (Device-based)",
      "rationale": "50 shared workstations with rotating users (avg 3 users/device)",
      "licenses_current": 150,
      "licenses_proposed": 50,
      "cost_current": 22500,
      "cost_proposed": 9000,
      "savings": 13500,
      "considerations": [
        "Requires device-based licensing model (not all vendors support)",
        "User experience: Users must use shared workstations (not personal devices)",
        "Compliance: Ensure device-based licensing meets vendor audit requirements"
      ],
      "recommendation": {
        "action": "Migrate 50 shared workstations to device-based licensing",
        "pilot": "Test with 10 workstations for 30 days",
        "rollout": "Full migration by Q3 2027"
      }
    }
  ]
}
```

#### 3.3 Compliance Audit Evidence Generation

**Use Case**: Adobe audit request received. Portfolio Manager needs to generate complete evidence pack within 24 hours showing entitlements, consumption, and reconciliation history.

**Agent Capabilities**:
- Generate audit evidence pack with:
  - Entitlement records (contracts, purchase orders)
  - Consumption snapshots (point-in-time, immutable)
  - Reconciliation runs (historical validation)
  - Assignment records (user/device mappings)
- Export to vendor-required format (CSV, Excel, PDF)
- Include immutability hash for tamper-evidence
- Generate executive summary (1-page overview)

**Example Output**:
```json
{
  "audit_evidence_pack": {
    "audit_id": "ADOBE-2027-Q1",
    "vendor": "Adobe",
    "generated_at": "2027-02-20T15:30:00Z",
    "generated_by": "License Management Agent",
    "correlation_id": "ae72f491-8b2d-4c1a-9f3e-1a5e0c7d2f9b",
    "immutability_hash": "sha256:8f3a2c1e9b7d5f4a3c2e1d9b8f7a6e5d4c3b2a1f9e8d7c6b5a4f3e2d1c0b9a8",
    "file_references": {
      "entitlements": "/audit/ADOBE-2027-Q1/entitlements.xlsx",
      "consumption": "/audit/ADOBE-2027-Q1/consumption.xlsx",
      "assignments": "/audit/ADOBE-2027-Q1/assignments.xlsx",
      "reconciliation_history": "/audit/ADOBE-2027-Q1/reconciliation.pdf",
      "executive_summary": "/audit/ADOBE-2027-Q1/executive-summary.pdf"
    }
  },
  "executive_summary": {
    "vendor": "Adobe",
    "audit_period": "2026-02-01 to 2027-01-31",
    "total_entitlements": 350,
    "total_consumption_peak": 325,
    "utilization_avg": 0.89,
    "compliance_status": "COMPLIANT",
    "compliance_details": [
      "All consumption within entitlement limits",
      "No overconsumption detected",
      "Reconciliation runs completed monthly (12/12 months)",
      "All assignments documented with audit trail"
    ],
    "supporting_evidence": [
      "12 monthly reconciliation runs (immutable snapshots)",
      "325 assignment records with timestamps",
      "3 entitlement contracts (PO-2026-0042, PO-2026-0089, PO-2026-0127)"
    ]
  }
}
```

#### 3.4 Policy Enforcement & Auto-Remediation

**Use Case**: Corporate policy requires all expired license assignments to be revoked within 30 days. Agent automatically identifies expired assignments and creates remediation tasks.

**Agent Capabilities**:
- Monitor license assignments for policy violations:
  - Expired assignments (end_date < today)
  - Inactive assignments (no usage in 90 days)
  - Overconsumption (consumed > entitled)
  - Non-compliant assignments (user not in approved group)
- Generate auto-remediation tasks:
  - Revoke expired assignments
  - Notify Application Managers of inactive assignments
  - Alert Portfolio Managers of overconsumption
- Track remediation progress and compliance trends

**Example Output**:
```json
{
  "policy_enforcement_summary": {
    "policy": "Expired License Assignment Revocation",
    "enforcement_date": "2027-02-20",
    "violations_detected": 12,
    "remediation_tasks_created": 12,
    "auto_remediation_enabled": true
  },
  "violations": [
    {
      "assignment_id": "a8f3e2d1-9c7b-4a5f-8e3d-2c1a0b9f8e7d",
      "sku": "Microsoft 365 E5",
      "principal_type": "user",
      "principal_id": "john.doe@company.com",
      "assigned_at": "2026-01-15",
      "expired_at": "2027-01-15",
      "days_overdue": 36,
      "policy_violation": "Assignment expired > 30 days ago",
      "remediation_action": "REVOKE",
      "remediation_task_id": "TASK-2027-0042",
      "remediation_status": "AUTO_REMEDIATED",
      "remediated_at": "2027-02-20T10:30:00Z"
    }
  ],
  "compliance_trend": {
    "current_month_violations": 12,
    "previous_month_violations": 18,
    "trend": "IMPROVING",
    "target": 0,
    "compliance_score": 0.95
  }
}
```

### Agent Workflow Integration

**UI Integration Points**:

1. **License Dashboard → True-Up Tab**:
   - Button: "AI: Generate True-Up Forecast"
   - Inputs: Vendor, forecast horizon (6/12 months)
   - Outputs: Forecast chart, true-up cost estimate, mitigation strategies, negotiation brief

2. **License Dashboard → Optimization Tab**:
   - Auto-displayed: Optimization playbooks (right-sizing, harvesting, model migration)
   - For each playbook:
     - Summary card: SKU, waste, savings
     - Button: "Execute Playbook" (requires approval)

3. **License Dashboard → Compliance Tab**:
   - Button: "AI: Generate Audit Evidence Pack"
   - Inputs: Vendor, audit period
   - Outputs: ZIP file with evidence pack, executive summary PDF

4. **License Dashboard → Policy Enforcement Tab**:
   - Auto-displayed: Policy violations with auto-remediation status
   - Button: "AI: Enforce Policies Now" (trigger manual enforcement run)

---

## Governance & Approval Workflow

### Human-in-the-Loop Requirements

**ALL AI agent recommendations require explicit human approval before execution.**

**Approval Workflow**:
```
1. Agent generates recommendation
2. Recommendation displayed in UI with:
   - Summary (what will happen)
   - Rationale (why)
   - Impact analysis (affected users/devices/cost)
   - Risk assessment (LOW/MEDIUM/HIGH)
3. User reviews recommendation
4. User approves/rejects with comments
5. If approved: Action executed with correlation ID
6. If rejected: Feedback logged, agent learns from rejection
```

**Approval Authority Matrix**:

| Recommendation Type | Approval Authority | Escalation (if high risk) |
|---------------------|-------------------|---------------------------|
| Dependency analysis | Application Manager | Portfolio Manager (risk > 75) |
| Health remediation | Application Manager | Portfolio Manager (critical apps) |
| Deployment timing | Application Manager | - |
| Portfolio optimization | Portfolio Manager | - |
| Team performance coaching | Portfolio Manager | - |
| License true-up forecast | Portfolio Manager | CFO (cost > $100k) |
| License optimization | Application Manager | Portfolio Manager (cost > $10k) |
| Policy enforcement | Automated | Application Manager (manual override) |

---

## Integration Architecture

### Backend Components

**AI Agent Service** (`apps/ai_agents/services/agent_orchestrator.py`):
```python
class AgentOrchestrator:
    def execute_agent_task(
        self,
        agent_type: AIAgentType,
        task_type: str,
        context: dict,
        user: User,
    ) -> AIAgentTask:
        """
        Execute AI agent task with human approval workflow.
        """
        # 1. Generate prompt from template
        prompt = self._generate_prompt(agent_type, task_type, context)

        # 2. Call AI model provider (OpenAI, Anthropic, etc.)
        response = self._call_ai_model(prompt, agent_type)

        # 3. Parse response (JSON validation)
        recommendation = self._parse_response(response)

        # 4. Create AIAgentTask record
        task = AIAgentTask.objects.create(
            agent_type=agent_type,
            initiated_by=user,
            task_type=task_type,
            input_context=context,
            recommendation=recommendation,
            status=AIAgentTaskStatus.AWAITING_APPROVAL,
            correlation_id=uuid.uuid4(),
        )

        return task
```

**AI Model Provider Integration** (`apps/ai_agents/providers/`):
```python
# OpenAI provider
class OpenAIProvider:
    def generate_completion(self, prompt: str, model: str = "gpt-4") -> str:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content

# Anthropic provider
class AnthropicProvider:
    def generate_completion(self, prompt: str, model: str = "claude-3-opus") -> str:
        response = anthropic.Completion.create(
            model=model,
            prompt=prompt,
            max_tokens=4096,
        )
        return response.completion
```

### Frontend Components

**AI Agent Modal** (`frontend/src/components/ai/AIAgentModal.tsx`):
```tsx
interface AIAgentModalProps {
  agentType: string;
  taskType: string;
  context: Record<string, any>;
  onApprove: (taskId: string, comments: string) => void;
  onReject: (taskId: string, comments: string) => void;
}

export function AIAgentModal({ agentType, taskType, context, onApprove, onReject }) {
  // 1. Trigger AI agent task
  const { mutate: triggerTask, data: task } = useTriggerAIAgentTask();

  // 2. Display recommendation
  // 3. Approval/rejection buttons with comments

  return (
    <Modal>
      <h2>AI Recommendation: {task.recommendation.summary}</h2>
      <div>
        <h3>Rationale</h3>
        <p>{task.recommendation.rationale}</p>
      </div>
      <div>
        <h3>Impact</h3>
        <ul>
          {task.recommendation.impact.map((item) => <li>{item}</li>)}
        </ul>
      </div>
      <div>
        <h3>Risk: {task.recommendation.risk}</h3>
      </div>
      <div>
        <Button onClick={() => onApprove(task.id, comments)}>Approve</Button>
        <Button onClick={() => onReject(task.id, comments)}>Reject</Button>
      </div>
    </Modal>
  );
}
```

---

## Performance & Cost Optimization

### Token Budget Management

**Token Limits per Agent Type**:
- Application Management Agent: 10k tokens per recommendation
- Portfolio Management Agent: 15k tokens per recommendation
- License Management Agent: 20k tokens per recommendation (complex forecasting)

**Cost Optimization Strategies**:
- **Prompt Engineering**: Optimize prompts to reduce token usage (remove redundant context)
- **Caching**: Cache dependency graphs, health metrics for 5 minutes (reduce repeated queries)
- **Model Selection**: Use GPT-3.5-turbo for simple tasks (10x cheaper than GPT-4)
- **Rate Limiting**: Max 100 agent tasks per user per day (prevent abuse)

### Response Time Targets

| Agent Task | Target Response Time | Max Acceptable |
|------------|---------------------|----------------|
| Dependency Analysis | 5 seconds | 10 seconds |
| Health Anomaly Detection | 10 seconds | 20 seconds |
| Portfolio Optimization | 15 seconds | 30 seconds |
| True-Up Forecasting | 20 seconds | 45 seconds |
| Audit Evidence Generation | 30 seconds | 60 seconds |

---

## Security & Privacy

### Data Handling

**PII Protection**:
- User names/emails anonymized in AI prompts (replaced with IDs)
- Device hostnames anonymized
- Correlation IDs used for audit trail (not sent to AI model)

**Data Retention**:
- AI agent tasks retained for 90 days (audit trail)
- Recommendations stored in database (for learning/improvement)
- AI model provider logs: zero data retention (contractual requirement)

### Access Control

**Role-Based Access**:
- Application Managers: Can trigger agents for their applications only
- Portfolio Managers: Can trigger agents for their portfolios only
- Admins: Can trigger agents for all resources

**Audit Trail**:
- All AI agent tasks logged with correlation ID
- User who triggered task
- User who approved/rejected recommendation
- Timestamp, input context, recommendation, outcome

---

## Testing & Validation

### Unit Tests

**Agent Service Tests**:
- Prompt generation with various contexts
- AI model provider mock responses
- Recommendation parsing and validation
- Error handling (AI model timeout, malformed response)

### Integration Tests

**End-to-End Workflows**:
- Application Manager triggers dependency analysis → approves recommendation → deployment proceeds
- Portfolio Manager triggers portfolio optimization → approves sunset recommendation → application retired
- License Management Agent generates true-up forecast → Portfolio Manager reviews → mitigation strategies executed

### Accuracy Validation

**Benchmark Tests**:
- Dependency analysis: 85% accuracy (validated against manual analysis)
- Health anomaly detection: 80% root cause accuracy (validated against historical incidents)
- True-up forecasting: ±10% accuracy (validated against actual true-up costs)

---

## Next Steps

1. **Backend Implementation**: Create AI agent service layer, model provider integrations
2. **Prompt Engineering**: Design and test prompt templates for each agent capability
3. **Frontend Components**: Build AI agent modal, approval workflow UI
4. **Demo Data**: Seed AI agent tasks with sample recommendations
5. **User Testing**: Pilot with Application Managers and Portfolio Managers
6. **Iteration**: Refine prompts, improve accuracy based on user feedback

---

**Document Owner**: AI/ML Engineering Lead
**Review Required From**: Product Owner, Security Reviewer, Application Manager (pilot user)
**Next Review Date**: 2026-02-06
