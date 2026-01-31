# Persona Requirements — Application & Portfolio Management

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Phase**: 0 — Foundation
**Document Version**: 1.0
**Date**: 2026-01-30

---

## Persona Definitions

### 1. Application Manager

**Role Summary**: Owns end-to-end lifecycle for 1-N enterprise applications from packaging request → deployment → monitoring → incident response.

#### Responsibilities
- **Application Registration**: Define application metadata, supported platforms, dependencies, update cadence
- **Packaging Coordination**: Submit packaging requests to Packaging Engineers, review artifacts
- **Deployment Planning**: Create deployment intents, coordinate with stakeholders, manage schedules
- **CAB Submissions**: Compile evidence packs, submit CAB requests, respond to feedback
- **Health Monitoring**: Monitor application health metrics, respond to degradation alerts
- **License Management**: Own license entitlements for applications, optimize utilization
- **Incident Response**: Triage deployment failures, coordinate rollbacks, document root causes
- **Dependency Management**: Identify and track application dependencies, coordinate updates

#### Key Workflows

**Workflow 1: New Application Deployment**
```
1. Register Application
   ├─ Define: name, description, category, owner, portfolio
   ├─ Select: supported platforms (Windows, macOS, Linux, iOS, Android)
   ├─ Specify: dependencies (runtime, build, optional)
   ├─ Set: update cadence (monthly, quarterly, ad-hoc)
   └─ Assign: license entitlements (SKU, quantity)

2. Request Packaging
   ├─ Submit packaging request to Packaging Engineer
   ├─ Provide: installer files, documentation, detection rules
   ├─ Specify: signing requirements, target platforms
   └─ Track: packaging status (pending → in_progress → completed)

3. Review Artifact
   ├─ Validate: artifact integrity (hash, signature)
   ├─ Review: SBOM, vulnerability scan results
   ├─ Approve/Reject: artifact quality
   └─ Request revisions if needed

4. Create Deployment Intent
   ├─ Select: artifact, target ring, scope
   ├─ Configure: rollout schedule, batch size, throttling
   ├─ Define: rollback plan (plane-specific strategies)
   └─ AI Deployment Advisor: recommends ring strategy

5. Submit CAB Request (if risk > 50)
   ├─ AI CAB Evidence Generator: compiles evidence pack
   ├─ Review: evidence completeness, risk factors
   ├─ Submit: CAB approval request
   └─ Track: approval status (pending → approved/rejected/conditional)

6. Monitor Deployment
   ├─ Real-time metrics: success rate, time-to-compliance, errors
   ├─ Ring progression: Lab → Canary → Pilot → Dept → Global
   ├─ Promotion gates: success rate thresholds, compliance checks
   └─ Incident alerts: failures, anomalies, rollback triggers

7. Post-Deployment
   ├─ Application health tracking: installations, versions, compliance
   ├─ License reconciliation: consumption vs entitlements
   ├─ Incident management: root cause analysis, remediation
   └─ Continuous improvement: lessons learned, process updates
```

**Workflow 2: Application Health Monitoring**
```
1. Daily Health Check
   ├─ View: application health dashboard
   ├─ Metrics: total installations, healthy %, degraded %, critical %
   ├─ Alerts: health degradation, compliance violations, incidents
   └─ AI Application Management Agent: identifies anomalies

2. Investigate Degradation
   ├─ Drill-down: affected devices, error patterns, version distribution
   ├─ Correlate: deployment events, system changes, dependencies
   ├─ AI Incident Responder: root cause analysis
   └─ Determine: remediation strategy

3. Remediate
   ├─ Create remediation task: reinstall, update, rollback
   ├─ Target: affected devices/users
   ├─ Execute: via agent task framework
   └─ Verify: health restoration

4. Document
   ├─ Incident report: root cause, impact, remediation
   ├─ Update: application health history
   └─ Share: lessons learned with Portfolio Manager
```

**Workflow 3: License Optimization**
```
1. Monthly License Review
   ├─ View: license consumption dashboard
   ├─ Metrics: entitled, consumed, remaining, utilization %
   ├─ Alerts: overconsumption, underutilization, expiring
   └─ AI License Management Agent: optimization opportunities

2. Right-Size Entitlements
   ├─ Identify: over-entitled SKUs (entitled >> consumed)
   ├─ Calculate: savings potential (unused licenses × cost)
   ├─ Request: entitlement reduction from Portfolio Manager
   └─ Track: savings realized

3. Harvest Unused Licenses
   ├─ Identify: inactive assignments (no usage in 90 days)
   ├─ Review: user status, business justification
   ├─ Revoke: eligible assignments
   └─ Reallocate: reclaimed licenses to pending requests
```

#### Key Metrics (Application Manager Scorecard)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Deployment Success Rate** | ≥95% | (successful_deployments / total_deployments) × 100 |
| **Time-to-Deployment** | ≤14 days | Avg days from CAB submission → Global completion |
| **Application Health Score** | ≥90% | % installations with healthy status |
| **License Utilization** | 70-85% | (consumed / entitled) × 100 |
| **Incident MTTR** | ≤4 hours | Avg time from incident detection → resolution |
| **Compliance Score** | ≥95% | % devices compliant with policy |
| **CAB Approval Rate** | ≥90% | (approved_cab_requests / total_cab_requests) × 100 |
| **Rollback Frequency** | ≤5% | (rollbacks / total_deployments) × 100 |

#### UI Components

**Application Manager Dashboard** (new page)
- **My Applications Grid**: List of owned applications with health, deployment status, license utilization
- **Active Deployments**: In-flight deployments with real-time metrics
- **Health Alerts**: Degraded applications requiring attention
- **License Consumption**: Per-application license usage with optimization flags
- **Performance Scorecard**: Personal KPI dashboard with trend charts
- **Quick Actions**: Create deployment, request packaging, submit CAB request

**Application Detail View**
- **Overview Tab**: Metadata, owner, portfolio, dependencies
- **Versions Tab**: Release history with artifact details
- **Deployments Tab**: Full deployment history with metrics
- **Health Tab**: Installation metrics, version distribution, incidents
- **Licenses Tab**: Entitlements, consumption, alerts
- **Dependencies Tab**: Dependency graph visualization

---

### 2. Portfolio Manager

**Role Summary**: Oversees M application managers and their N applications, focused on portfolio optimization, cost management, team performance, and strategic planning.

#### Responsibilities
- **Portfolio Strategy**: Define application portfolio vision, priorities, retirement roadmap
- **Budget Management**: Own portfolio budget, track costs (licenses + deployment overhead), optimize spend
- **Team Leadership**: Manage application managers, assess performance, provide coaching
- **License Optimization**: Consolidate vendor licensing, negotiate ELAs, forecast true-up costs
- **Risk Oversight**: Monitor portfolio-level risk, approve high-risk deployments, enforce governance
- **Compliance**: Ensure portfolio compliance with enterprise policies, respond to audits
- **Vendor Management**: Manage vendor relationships, optimize licensing terms, track renewals

#### Key Workflows

**Workflow 1: Portfolio Health Review (Monthly)**
```
1. Portfolio Dashboard Review
   ├─ Overall health score: aggregate across all applications
   ├─ Application grid: color-coded by health (healthy, degraded, critical)
   ├─ Cost analysis: total portfolio cost breakdown
   └─ Compliance scorecard: % compliant applications

2. Identify Issues
   ├─ Critical applications: health < 70%
   ├─ High-cost applications: cost > budget threshold
   ├─ Non-compliant applications: compliance < 95%
   └─ AI Portfolio Management Agent: prioritizes action items

3. Deep Dive
   ├─ Application details: health metrics, deployment history, incidents
   ├─ Application Manager performance: scorecard, trends
   ├─ Root cause analysis: AI Incident Responder insights
   └─ Corrective actions: coaching, resource allocation, process changes

4. Report to Leadership
   ├─ Portfolio health summary: executive dashboard
   ├─ Cost optimization progress: savings realized
   ├─ Team performance: Application Manager rankings
   └─ Strategic recommendations: sunset, consolidate, upgrade
```

**Workflow 2: License True-Up Planning (Quarterly)**
```
1. Generate True-Up Forecast
   ├─ Select: vendor (Microsoft, Adobe, VMware, etc.)
   ├─ Forecast horizon: 6-12 months
   ├─ AI License Management Agent: models consumption growth
   └─ Output: forecasted consumption, additional licenses needed, estimated cost

2. Analyze Mitigation Strategies
   ├─ Right-sizing: reduce over-entitled SKUs
   ├─ License harvesting: reclaim unused licenses
   ├─ Model migration: change license models (user → device, etc.)
   ├─ Bundle optimization: upgrade/downgrade bundles
   └─ Calculate: potential savings per strategy

3. Execute Optimizations
   ├─ Approve: entitlement reductions
   ├─ Coordinate: license harvesting campaigns (Application Managers)
   ├─ Negotiate: vendor terms (with Procurement)
   └─ Track: savings realized vs forecast

4. Vendor Negotiation
   ├─ Prepare: usage data, cost analysis, benchmark comparisons
   ├─ AI License Management Agent: generates negotiation brief
   ├─ Meet: vendor account team (with Procurement)
   └─ Finalize: new ELA terms, cost savings
```

**Workflow 3: Team Performance Management (Quarterly)**
```
1. Review Team Performance
   ├─ Application Manager rankings: by KPIs (success rate, velocity, health, etc.)
   ├─ Identify: top performers, underperformers, improvement areas
   ├─ AI Portfolio Management Agent: coaching recommendations
   └─ Trends: performance over time (6 months trailing)

2. Coaching & Development
   ├─ One-on-ones: discuss performance, challenges, goals
   ├─ Training: identify skill gaps, recommend courses
   ├─ Process improvements: bottleneck analysis, workflow optimization
   └─ Resource allocation: balance application portfolios across managers

3. Recognition & Accountability
   ├─ Top performers: public recognition, bonuses
   ├─ Underperformers: performance improvement plans
   ├─ Portfolio rebalancing: reassign applications if needed
   └─ Document: performance reviews, development plans
```

#### Key Metrics (Portfolio Manager Scorecard)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Portfolio Health Score** | ≥85/100 | Weighted avg of application health scores |
| **Total Portfolio Cost** | Within budget | Annual cost (licenses + deployment + support) |
| **License Utilization** | 70-85% | Avg utilization across all SKUs |
| **Cost Optimization Savings** | ≥10% YoY | Savings realized vs previous year |
| **Team Avg Success Rate** | ≥95% | Avg deployment success rate across Application Managers |
| **Team Avg Time-to-Deployment** | ≤14 days | Avg time-to-deployment across Application Managers |
| **Compliance Score** | ≥95% | % applications compliant with policy |
| **True-Up Forecast Accuracy** | ±5% | (actual_true_up / forecast_true_up) × 100 |

#### UI Components

**Portfolio Manager Dashboard** (new page)
- **Portfolio Health Overview**: Aggregate health score with trend chart
- **Application Grid**: All portfolio applications with health, cost, license utilization (filterable, sortable)
- **Cost Analysis**: Total cost breakdown (licenses, deployment, support) with drill-down
- **Team Performance Matrix**: Application Manager rankings with KPIs
- **License Optimization**: True-up forecast, optimization opportunities, savings potential
- **Risk Heatmap**: Applications with high risk scores or frequent failures
- **Compliance Scorecard**: % compliant applications, open violations, remediation status
- **Quick Actions**: Approve CAB requests, review true-up forecast, assign ownership

**Team Performance View**
- **Manager Rankings Table**: Application Managers sorted by composite score
- **KPI Comparison Chart**: Success rate, velocity, health, license efficiency
- **Trend Analysis**: Manager performance over time (6 months trailing)
- **Coaching Insights**: AI-generated recommendations for underperformers
- **Portfolio Balance**: Application distribution across managers

**License True-Up View**
- **Vendor Selection**: Dropdown (Microsoft, Adobe, VMware, etc.)
- **Forecast Chart**: Consumption trend with forecasted future usage
- **True-Up Impact**: Additional licenses needed, estimated cost
- **Mitigation Strategies**: Right-sizing, harvesting, model migration with savings potential
- **Negotiation Brief**: AI-generated vendor negotiation document (exportable)

---

### 3. Packaging Engineer (Enhanced)

**Role Summary**: Creates high-quality artifacts for Application Managers with automated scanning, signing, and evidence generation.

#### Responsibilities (Existing + New)
- **Artifact Creation**: Package applications per platform (Win32, MSIX, PKG, etc.)
- **SBOM Generation**: Automated SBOM creation (SPDX/CycloneDX)
- **Vulnerability Scanning**: Integrate with Trivy/Grype/Snyk for automated scans
- **Code Signing**: Sign artifacts with enterprise certificates (Authenticode, notarization, GPG)
- **Detection Rules**: Author detection rules (file, registry, product code)
- **Rollback Plans**: Document rollback strategies per execution plane
- **Quality Assurance**: Validate artifacts in lab environment (Ring 0)

#### Enhanced Workflows

**Workflow: Artifact Creation with AI Assistance**
```
1. Receive Packaging Request
   ├─ Request from: Application Manager
   ├─ Includes: installer files, documentation, requirements
   └─ Acknowledge: estimated completion time

2. AI Packaging Assistant
   ├─ Auto-detect: installer type (MSI, EXE, PKG, DEB, RPM)
   ├─ Generate: silent install/uninstall commands
   ├─ Generate: detection rules (file hash, version, registry key)
   ├─ Generate: SBOM from installer manifest
   └─ Review: AI-generated outputs, adjust if needed

3. Build Artifact
   ├─ Create: platform-specific package (Win32, MSIX, PKG, etc.)
   ├─ Sign: with enterprise certificate
   ├─ Scan: vulnerability analysis (Trivy/Grype)
   ├─ Validate: detection rules (test in lab)
   └─ Document: rollback plan per execution plane

4. Publish Artifact
   ├─ Upload: to artifact store (MinIO)
   ├─ Compute: SHA-256 hash
   ├─ Create: PackageArtifact record with evidence
   └─ Notify: Application Manager (artifact ready)

5. Lab Validation (Ring 0)
   ├─ Deploy: to lab devices (automated)
   ├─ Verify: installation success, detection accuracy
   ├─ Test: uninstall, rollback
   └─ Report: validation results to Application Manager
```

---

## Persona Interactions

### Interaction 1: Application Manager → Packaging Engineer
**Trigger**: Application Manager needs new artifact for deployment
**Flow**:
1. Application Manager submits packaging request via UI
2. Packaging Engineer receives notification
3. Packaging Engineer creates artifact with AI Packaging Assistant
4. Packaging Engineer publishes artifact
5. Application Manager receives notification (artifact ready)
6. Application Manager reviews artifact, approves/rejects

### Interaction 2: Application Manager → Portfolio Manager
**Trigger**: High-risk deployment requiring Portfolio Manager approval
**Flow**:
1. Application Manager creates deployment intent (risk > 75)
2. CAB request auto-submitted
3. Portfolio Manager notified (high-risk deployment in their portfolio)
4. Portfolio Manager reviews evidence pack, approves/rejects
5. If approved: deployment proceeds
6. Portfolio Manager monitors deployment metrics
7. Post-deployment: Portfolio Manager reviews performance impact

### Interaction 3: Portfolio Manager → Application Managers (All)
**Trigger**: Quarterly true-up planning
**Flow**:
1. Portfolio Manager generates license true-up forecast
2. AI License Management Agent identifies optimization opportunities
3. Portfolio Manager creates license harvesting campaign
4. All Application Managers notified (review unused licenses)
5. Application Managers identify inactive assignments, revoke
6. Portfolio Manager tracks progress, reports savings

---

## RACI Matrix

| Activity | Application Manager | Portfolio Manager | Packaging Engineer | CAB Approver |
|----------|:-------------------:|:-----------------:|:------------------:|:------------:|
| **Register Application** | R/A | C | I | I |
| **Request Packaging** | R/A | I | C | - |
| **Create Artifact** | C | I | R/A | - |
| **Create Deployment Intent** | R/A | C | I | I |
| **Submit CAB Request** | R/A | C | I | - |
| **Approve CAB Request (low risk)** | I | I | I | R/A |
| **Approve CAB Request (high risk)** | I | C | I | R/A |
| **Monitor Deployment** | R/A | I | I | I |
| **Respond to Incidents** | R/A | C | C | I |
| **Optimize Licenses** | R | A | - | - |
| **Portfolio Strategy** | C | R/A | I | I |
| **Team Performance Review** | C | R/A | I | I |

**Legend**: R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## Permissions Model

### Application Manager Permissions
```python
{
  "applications": ["read", "write"],  # Own applications only
  "deployments": ["read", "write", "execute"],  # Own deployments
  "cab": ["read", "write"],  # Submit CAB requests
  "evidence": ["read"],  # View evidence packs
  "licenses": ["read"],  # View license consumption
  "artifacts": ["read"],  # View artifacts, request packaging
  "audit": ["read"],  # View audit trail
}
```

### Portfolio Manager Permissions
```python
{
  "applications": ["read", "write", "admin"],  # All portfolio applications
  "deployments": ["read"],  # View all portfolio deployments
  "cab": ["read", "approve"],  # Approve high-risk CAB requests
  "evidence": ["read"],  # View evidence packs
  "licenses": ["read", "write", "admin"],  # Manage portfolio licenses
  "portfolios": ["read", "write", "admin"],  # Manage own portfolios
  "analytics": ["read"],  # View team performance analytics
  "audit": ["read"],  # View audit trail
}
```

### Packaging Engineer Permissions
```python
{
  "applications": ["read"],  # View application details
  "artifacts": ["read", "write", "admin"],  # Create, publish artifacts
  "evidence": ["write"],  # Generate evidence packs
  "packaging_requests": ["read", "write"],  # Manage packaging requests
  "audit": ["read"],  # View audit trail
}
```

---

## Next Steps

1. **Wireframes**: Create UI mockups for Application Manager and Portfolio Manager dashboards
2. **Data Model**: Design database schema for Portfolio, ApplicationOwnership, Performance metrics
3. **AI Specifications**: Define AI agent capabilities, prompts, and integration points
4. **User Stories**: Convert workflows into detailed user stories with acceptance criteria

---

**Document Owner**: Product Management
**Review Required From**: Application Manager (pilot user), Portfolio Manager (pilot user)
**Next Review Date**: 2026-02-06
