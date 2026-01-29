# STATEMENT OF WORK

## EUCORA — Enterprise Endpoint Application Packaging & Deployment Platform

---

**Document ID**: EUCORA-SOW-2026-001
**Version**: 1.0.0
**Effective Date**: ________________
**Contract Reference**: ________________

**SPDX-License-Identifier**: Proprietary

---

## PARTIES

**SERVICE PROVIDER** ("Provider"):
```
BuildWorks.AI
[Address]
[City, State, ZIP]
[Country]
```

**CUSTOMER** ("Customer"):
```
[Customer Legal Name]
[Address]
[City, State, ZIP]
[Country]
```

---

## TABLE OF CONTENTS

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Definitions](#2-definitions)
3. [Project Governance](#3-project-governance)
4. [Deliverables](#4-deliverables)
5. [Project Schedule](#5-project-schedule)
6. [Acceptance Criteria](#6-acceptance-criteria)
7. [Roles and Responsibilities](#7-roles-and-responsibilities)
8. [Technical Requirements](#8-technical-requirements)
9. [Quality Standards](#9-quality-standards)
10. [Change Management](#10-change-management)
11. [Risk Management](#11-risk-management)
12. [Pricing and Payment](#12-pricing-and-payment)
13. [Service Level Agreement](#13-service-level-agreement)
14. [Warranty and Support](#14-warranty-and-support)
15. [Intellectual Property](#15-intellectual-property)
16. [Confidentiality](#16-confidentiality)
17. [Compliance and Security](#17-compliance-and-security)
18. [Termination](#18-termination)
19. [Signatures](#19-signatures)
20. [Appendices](#20-appendices)

---

## 1. PURPOSE AND SCOPE

### 1.1 Purpose

This Statement of Work ("SOW") defines the terms, deliverables, and responsibilities for the implementation of EUCORA (End-User Computing Orchestration & Reliability Architecture), an enterprise-grade platform for automated application packaging, deployment, governance, and AI-assisted remediation across the Customer's endpoint environment.

### 1.2 Project Objectives

| ID | Objective | Success Metric |
|----|-----------|----------------|
| **OBJ-01** | Reduce EUC operational overhead through automation | ≥40% reduction in packaging time |
| **OBJ-02** | Standardize deployment across all OS platforms | Single workflow for Windows, macOS, Linux |
| **OBJ-03** | Improve incident resolution with AI assistance | ≥30% reduction in MTTR |
| **OBJ-04** | Enforce evidence-based change control | 100% CAB-approved evidence packs |
| **OBJ-05** | Implement enterprise license management | Real-time consumption visibility |
| **OBJ-06** | Achieve compliance with regulatory requirements | GDPR, DPDP, SOC2 alignment |
| **OBJ-07** | Support 100,000 devices at scale | Validated load testing |

### 1.3 Scope of Work

#### 1.3.1 In-Scope

| Category | Description |
|----------|-------------|
| **Core Platform** | Control plane installation, configuration, and integration |
| **Packaging Automation** | Multi-platform packaging factory (Windows, macOS, Linux) |
| **Deployment Orchestration** | Ring-based rollout with promotion gates |
| **Execution Plane Connectors** | Intune, Jamf, SCCM, Landscape, Ansible integration |
| **CAB Workflow** | Evidence-based approval workflows with risk scoring |
| **License Management** | Vendor/SKU tracking, consumption reconciliation, AI agents |
| **Application Portfolio** | Inventory, dependencies, portfolio risk scoring |
| **AI Agents** | Incident classification, remediation advisor, optimization |
| **User Management** | RBAC, AD integration foundation, admin portal |
| **Observability** | Prometheus, Loki, Tempo, Grafana dashboards |
| **Documentation** | Architecture, runbooks, training materials |
| **Training** | Administrator and operator training (see Section 4.9) |

#### 1.3.2 Out-of-Scope

| Item | Rationale |
|------|-----------|
| SaaS/multi-tenant deployment | Single-tenant self-hosted only |
| Hardware procurement | Customer responsibility |
| Network infrastructure changes | Customer responsibility |
| Third-party software licenses | Customer procurement |
| Custom integrations not listed | Change order required |
| End-user device provisioning | Execution plane responsibility |
| Legacy system migration | Separate engagement |

### 1.4 Assumptions

| ID | Assumption | Impact if Invalid |
|----|------------|-------------------|
| **ASM-01** | Customer has operational Azure AD/Entra ID | Delayed identity integration |
| **ASM-02** | Customer has Intune tenant with appropriate licenses | Limited Windows deployment |
| **ASM-03** | Customer provides Kubernetes cluster or VMs | Delayed deployment |
| **ASM-04** | Customer provides timely access to systems | Schedule slip |
| **ASM-05** | Customer provides dedicated project resources | Requirement gaps |
| **ASM-06** | Network connectivity between platform and endpoints | Functionality limitations |
| **ASM-07** | Customer provides test device population | Testing delays |

### 1.5 Constraints

| ID | Constraint | Mitigation |
|----|------------|------------|
| **CON-01** | Air-gapped site support required | Offline distribution design |
| **CON-02** | Data residency within Customer boundary | Self-hosted storage only |
| **CON-03** | No external cloud dependencies | Local AI inference |
| **CON-04** | Existing ITSM integration required | ServiceNow connector priority |

---

## 2. DEFINITIONS

| Term | Definition |
|------|------------|
| **Acceptance** | Customer's formal written approval that a Deliverable meets Acceptance Criteria |
| **Acceptance Criteria** | Specific, measurable conditions that must be satisfied for Acceptance |
| **Business Day** | Monday through Friday, excluding public holidays |
| **CAB** | Change Advisory Board — governance body for deployment approvals |
| **Change Order** | Written agreement to modify scope, schedule, or cost |
| **Control Plane** | EUCORA orchestration layer (policy, evidence, coordination) |
| **Deliverable** | A work product delivered under this SOW |
| **Evidence Pack** | Complete audit bundle for a deployment decision |
| **Execution Plane** | MDM/endpoint management tools (Intune, Jamf, SCCM) |
| **Go-Live** | Production deployment and operational handover |
| **Milestone** | A significant project checkpoint with associated Deliverables |
| **Ring** | Deployment phase with specific scope and success criteria |
| **SBOM** | Software Bill of Materials — component inventory |
| **SLA** | Service Level Agreement — performance commitments |
| **SOW** | This Statement of Work document |
| **Sprint** | Two-week development iteration |
| **UAT** | User Acceptance Testing |

---

## 3. PROJECT GOVERNANCE

### 3.1 Governance Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         STEERING COMMITTEE                               │
│                                                                          │
│   Customer: Executive Sponsor, IT Director                              │
│   Provider: Engagement Director, Solution Architect                      │
│                                                                          │
│   Frequency: Monthly or as needed                                       │
│   Authority: Scope changes, escalations, strategic decisions            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROJECT MANAGEMENT                               │
│                                                                          │
│   Customer: Project Manager, Technical Lead                             │
│   Provider: Project Manager, Technical Lead                              │
│                                                                          │
│   Frequency: Weekly                                                      │
│   Authority: Day-to-day decisions, risk management, status reporting    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         TECHNICAL TEAM                                   │
│                                                                          │
│   Customer: EUC Engineers, Security, Operations                         │
│   Provider: Development Team, DevOps, QA                                 │
│                                                                          │
│   Frequency: Daily standups, Sprint ceremonies                          │
│   Authority: Technical implementation decisions                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Communication Plan

| Communication | Participants | Frequency | Method | Owner |
|---------------|--------------|-----------|--------|-------|
| Daily Standup | Technical Team | Daily | Video call | Provider PM |
| Sprint Planning | Project Team | Bi-weekly | Video call | Provider PM |
| Sprint Review | Project Team + Stakeholders | Bi-weekly | Video call | Provider PM |
| Status Report | Project Managers | Weekly | Email + document | Provider PM |
| Steering Committee | Executives | Monthly | Video call | Customer Sponsor |
| Escalation | As needed | As needed | Email + call | Either party |

### 3.3 Decision Authority Matrix

| Decision Type | Technical Team | Project Manager | Steering Committee |
|---------------|----------------|-----------------|-------------------|
| Technical implementation approach | **Decide** | Inform | Inform |
| Sprint prioritization | Recommend | **Decide** | Inform |
| Scope change (<5% effort) | Recommend | **Decide** | Inform |
| Scope change (≥5% effort) | Recommend | Recommend | **Decide** |
| Schedule change (<1 week) | Recommend | **Decide** | Inform |
| Schedule change (≥1 week) | Recommend | Recommend | **Decide** |
| Budget change | Inform | Recommend | **Decide** |
| Resource change | Recommend | **Decide** | Inform |
| Risk acceptance | Recommend | Recommend | **Decide** |

### 3.4 Escalation Procedure

| Level | Timeframe | Escalation Path |
|-------|-----------|-----------------|
| **Level 1** | 0-2 Business Days | Technical Leads |
| **Level 2** | 2-5 Business Days | Project Managers |
| **Level 3** | 5-10 Business Days | Steering Committee |
| **Level 4** | >10 Business Days | Executive Sponsors |

---

## 4. DELIVERABLES

### 4.1 Deliverable Summary

| ID | Deliverable | Phase | Acceptance Method |
|----|-------------|-------|-------------------|
| **D-01** | Architecture Documentation | P1 | Document review |
| **D-02** | Core Platform Deployment | P1 | Functional testing |
| **D-03** | Execution Plane Connectors | P2 | Integration testing |
| **D-04** | AI Governance Framework | P2 | Functional testing |
| **D-05** | License Management Module | P3 | UAT |
| **D-06** | Application Portfolio Module | P3 | UAT |
| **D-07** | User Management Module | P3 | UAT |
| **D-08** | Enterprise Hardening | P4 | Security audit |
| **D-09** | Production Deployment | P4 | Go-Live checklist |
| **D-10** | Training & Documentation | P4 | Training delivery |

### 4.2 D-01: Architecture Documentation

**Description**: Complete technical architecture specification aligned with Customer requirements.

**Contents**:
- System architecture overview
- Component specifications
- Data architecture and models
- Integration patterns
- Security architecture
- Deployment topology
- Disaster recovery design

**Acceptance Criteria**:
- [ ] Document reviewed by Customer Architecture Team
- [ ] All Customer requirements traceable
- [ ] Security controls approved by Customer Security
- [ ] Integration patterns validated with execution planes

### 4.3 D-02: Core Platform Deployment

**Description**: Fully operational EUCORA control plane with base functionality.

**Components**:
| Component | Functionality |
|-----------|---------------|
| API Gateway | Authentication, routing, rate limiting |
| Portal UI | Admin and self-service interfaces |
| Packaging Service | Package intake, validation, SBOM |
| Deployment Service | Intent management, ring orchestration |
| CAB Service | Approval workflows, risk assessment |
| Policy Engine | Policy evaluation, compliance scoring |
| Evidence Service | Evidence pack generation, storage |
| Event Store | Immutable audit trail |
| Observability Stack | Prometheus, Loki, Tempo, Grafana |

**Acceptance Criteria**:
- [ ] All services deployed and healthy
- [ ] Authentication via Customer identity provider
- [ ] RBAC operational with defined roles
- [ ] Audit logging verified
- [ ] Health checks passing
- [ ] Observability dashboards operational
- [ ] Test coverage ≥90%

### 4.4 D-03: Execution Plane Connectors

**Description**: Production-ready connectors for all specified execution planes.

**Connectors**:
| Connector | Capabilities |
|-----------|-------------|
| **Intune** | App CRUD, assignment, compliance, telemetry |
| **Jamf** | Package deployment, policy, inventory |
| **SCCM** | Package distribution, collections, DPs |
| **Landscape** | Repo sync, package install, compliance |
| **Ansible** | AWX job templates, inventory sync |
| **AD/Entra ID** | User/group sync, authentication |
| **ServiceNow** | Incident sync, CMDB, approvals |

**Acceptance Criteria**:
- [ ] Each connector passes integration tests
- [ ] Idempotency verified for all write operations
- [ ] Circuit breaker patterns operational
- [ ] Drift detection functional
- [ ] Reconciliation loops operational
- [ ] Error handling verified
- [ ] Test coverage ≥90%

### 4.5 D-04: AI Governance Framework

**Description**: Complete AI agent framework with human-in-loop governance.

**Components**:
| Component | Functionality |
|-----------|---------------|
| Agent Execution Framework | Guardrails, execution, audit |
| Model Registry | Versioning, lineage, deployment |
| Human-in-Loop Approval UI | Evidence review, approve/reject |
| Drift Detection Pipeline | Performance monitoring, alerts |
| Incident Classifier Agent | Category, confidence, severity |
| Remediation Advisor Agent | Script recommendations, evidence |
| Risk Assessment Agent | Deterministic risk scoring |

**Acceptance Criteria**:
- [ ] All agents execute through guardrail framework
- [ ] R2/R3 actions blocked without approval
- [ ] Complete audit trail for all agent actions
- [ ] Model lineage tracked for deployed models
- [ ] Drift detection alerts operational
- [ ] Incident classification accuracy ≥85%
- [ ] Test coverage ≥90%

### 4.6 D-05: License Management Module

**Description**: Enterprise-grade Software Asset Management with AI-assisted reconciliation.

**Components**:
| Component | Functionality |
|-----------|---------------|
| License Data Model | Vendor, SKU, Entitlement, Pool, Consumption |
| Entitlement Management | CRUD with approval governance |
| Consumption Signal Ingestion | MDM/telemetry normalization |
| Reconciliation Engine | Deterministic truth builder |
| Sidebar Widget | Real-time Consumed/Entitled/Remaining |
| License Dashboard | Trends, alerts, drilldowns |
| License AI Agents | Inventory extractor, discovery, optimization |

**Acceptance Criteria**:
- [ ] Reconciliation produces deterministic results
- [ ] Snapshots are immutable with evidence
- [ ] Sidebar displays accurate, current counters
- [ ] Health indicator reflects reconciliation status
- [ ] Evidence packs exportable for audit
- [ ] AI agents follow guardrail framework
- [ ] All license model types supported (device, user, concurrent, subscription)
- [ ] Test coverage ≥90%

**Detailed Acceptance Tests**:
| ID | Test | Expected Result |
|----|------|-----------------|
| LM-01 | Create entitlement with 100 licenses | Entitlement created, audit logged |
| LM-02 | Ingest 50 consumption signals from Intune | Signals normalized, deduplicated |
| LM-03 | Run reconciliation | Snapshot created: Entitled=100, Consumed=50, Remaining=50 |
| LM-04 | Verify sidebar | Shows 50/100/50, health=OK, timestamp current |
| LM-05 | Ingest 60 additional signals (over-consumption) | Alert generated, sidebar shows warning |
| LM-06 | Export evidence pack | Complete pack with signals, rules, snapshot |
| LM-07 | Run optimization advisor | Recommendations generated, approval required |

### 4.7 D-06: Application Portfolio Module

**Description**: Application inventory with dependency mapping and portfolio risk scoring.

**Components**:
| Component | Functionality |
|-----------|---------------|
| Application Catalog | Normalized inventory, deduplication |
| Version Tracking | Versions, EOL, vulnerabilities |
| License Association | App-to-SKU mapping with evidence |
| Dependency Mapping | Runtime, shared, inferred dependencies |
| Portfolio Dashboard | Risk heatmap, stakeholder views |
| Portfolio AI Agents | Normalization, inference, risk analysis |

**Acceptance Criteria**:
- [ ] Applications deduplicated across sources
- [ ] Version drift detected and reported
- [ ] License associations auditable
- [ ] Dependency graph queryable
- [ ] Portfolio risk scores calculated
- [ ] Evidence export functional
- [ ] Test coverage ≥90%

### 4.8 D-07: User Management Module

**Description**: Comprehensive user administration with AD integration foundation.

**Components**:
| Component | Functionality |
|-----------|---------------|
| User Management UI | Create, edit, deactivate users |
| Role Management | Predefined + custom roles, permissions |
| Group Management | Hierarchical groups, role inheritance |
| AD Sync Foundation | User/group sync from AD |
| Session Management | Active sessions, force logout |
| Audit Dashboard | User action audit trail |

**Acceptance Criteria**:
- [ ] Admin can create/edit/deactivate users
- [ ] Roles assignable with permissions
- [ ] Groups support hierarchy
- [ ] AD sync pulls users/groups on schedule
- [ ] Sessions trackable and revocable
- [ ] All actions audit logged
- [ ] Test coverage ≥90%

### 4.9 D-08: Enterprise Hardening

**Description**: Production-grade security, reliability, and compliance hardening.

**Components**:
| Component | Deliverable |
|-----------|-------------|
| HA/DR | Documentation, tested failover procedures |
| Secrets Management | Vault/K8s integration, rotation procedures |
| mTLS | Service mesh with mutual TLS |
| SBOM | Automated generation in CI/CD |
| Vulnerability Scanning | Trivy/Grype integration, zero critical/high |
| Backup/Restore | Documented and tested procedures |
| Break-Glass | Emergency access procedures |
| Load Testing | 100,000 device scale validation |

**Acceptance Criteria**:
- [ ] Zero critical/high CVEs in production image
- [ ] SBOM generated for all components
- [ ] Backup/restore tested and documented
- [ ] mTLS enabled for all internal services
- [ ] Secrets rotatable without downtime
- [ ] Load test validates 100k device scale
- [ ] DR procedures documented and tested
- [ ] Security audit passed

### 4.10 D-09: Production Deployment

**Description**: Complete production deployment with operational handover.

**Components**:
| Component | Deliverable |
|-----------|-------------|
| Production Environment | Deployed, configured, validated |
| E2E Test Suite | All critical paths tested |
| Monitoring | Dashboards, alerts configured |
| Incident Response | Procedures documented |
| Runbooks | Complete operational runbooks |

**Acceptance Criteria**:
- [ ] All services deployed and healthy in production
- [ ] E2E tests pass in production
- [ ] Monitoring dashboards operational
- [ ] Alerts configured and tested
- [ ] Runbooks reviewed and approved
- [ ] On-call procedures documented
- [ ] Go-Live checklist 100% complete

### 4.11 D-10: Training & Documentation

**Description**: Comprehensive training program and documentation package.

**Training Modules**:
| Module | Audience | Duration | Format |
|--------|----------|----------|--------|
| Platform Administration | IT Admins | 8 hours | Instructor-led |
| Packaging & Deployment | EUC Engineers | 8 hours | Instructor-led |
| CAB Workflow | Approvers | 4 hours | Instructor-led |
| License Management | License Admins | 4 hours | Instructor-led |
| AI Agent Operations | Operations | 4 hours | Instructor-led |
| Troubleshooting | Support | 8 hours | Instructor-led |

**Documentation Package**:
| Document | Description |
|----------|-------------|
| Administrator Guide | Platform administration procedures |
| User Guide | End-user self-service portal guide |
| API Reference | Complete API documentation |
| Runbook Library | Operational procedures |
| Troubleshooting Guide | Common issues and resolutions |
| Architecture Document | Technical architecture reference |

**Acceptance Criteria**:
- [ ] All training modules delivered
- [ ] Training materials provided to Customer
- [ ] Documentation package complete
- [ ] Knowledge transfer sessions completed
- [ ] Customer team certified operational

---

## 5. PROJECT SCHEDULE

### 5.1 Project Timeline

| Phase | Name | Duration | Start | End |
|-------|------|----------|-------|-----|
| **P1** | Foundation | 3 weeks | Week 1 | Week 3 |
| **P2** | Integration | 3 weeks | Week 2 | Week 5 |
| **P3** | Features | 4 weeks | Week 4 | Week 8 |
| **P4** | Hardening | 4 weeks | Week 8 | Week 12 |

**Total Duration**: 12 weeks

### 5.2 Detailed Schedule

```
Week     1    2    3    4    5    6    7    8    9   10   11   12
         |----|----|----|----|----|----|----|----|----|----|----|----|
P1       ████████████████████
  D-01   ████████                                                      Architecture
  D-02        ████████████████                                         Core Platform

P2            ████████████████████████
  D-03        ████████████████████████                                 Connectors
  D-04             ████████████████████                                AI Framework

P3                      ████████████████████████████
  D-05                  ████████████████                               License Mgmt
  D-06                       ████████████████                          Portfolio
  D-07                            ████████████████                     User Mgmt

P4                                          ████████████████████████
  D-08                                      ████████████████           Hardening
  D-09                                           ████████████████      Production
  D-10                                                ████████████████ Training
         |----|----|----|----|----|----|----|----|----|----|----|----|
```

### 5.3 Milestones

| ID | Milestone | Target Date | Deliverables | Exit Criteria |
|----|-----------|-------------|--------------|---------------|
| **M1** | Architecture Approved | End Week 2 | D-01 | Customer sign-off |
| **M2** | Core Platform Operational | End Week 4 | D-02 | Functional testing pass |
| **M3** | Connectors Complete | End Week 5 | D-03 | Integration tests pass |
| **M4** | AI Framework Complete | End Week 5 | D-04 | Functional testing pass |
| **M5** | License Module Complete | End Week 7 | D-05 | UAT pass |
| **M6** | Portfolio Module Complete | End Week 8 | D-06 | UAT pass |
| **M7** | User Management Complete | End Week 8 | D-07 | UAT pass |
| **M8** | Security Audit Pass | End Week 10 | D-08 | Audit report clean |
| **M9** | Production Go-Live | End Week 11 | D-09 | Go-Live checklist |
| **M10** | Training Complete | End Week 12 | D-10 | Training delivery |

### 5.4 Dependencies

| Dependency | Provider | Required By | Impact if Delayed |
|------------|----------|-------------|-------------------|
| Kubernetes cluster / VMs | Customer | Week 1 | Platform deployment blocked |
| Azure AD/Entra ID access | Customer | Week 1 | Authentication blocked |
| Intune tenant access | Customer | Week 2 | Connector development blocked |
| Jamf Pro access | Customer | Week 2 | Connector development blocked |
| Test device population | Customer | Week 3 | Integration testing blocked |
| ServiceNow access | Customer | Week 3 | ITSM integration blocked |
| Security audit scheduling | Customer | Week 8 | Hardening sign-off delayed |
| Training scheduling | Customer | Week 10 | Training delivery delayed |

---

## 6. ACCEPTANCE CRITERIA

### 6.1 General Acceptance Criteria

All Deliverables must meet the following general criteria:

| Criterion | Requirement |
|-----------|-------------|
| **Functionality** | All specified features operational |
| **Performance** | Meets NFR specifications |
| **Security** | Zero critical/high vulnerabilities |
| **Quality** | Test coverage ≥90% |
| **Documentation** | Complete and accurate |
| **Compliance** | Meets regulatory requirements |

### 6.2 Acceptance Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ACCEPTANCE PROCESS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. DELIVERY                                                            │
│     Provider delivers Deliverable with supporting evidence              │
│                        │                                                │
│                        ▼                                                │
│  2. REVIEW (5 Business Days)                                            │
│     Customer reviews Deliverable against Acceptance Criteria            │
│                        │                                                │
│         ┌──────────────┴──────────────┐                                │
│         │                             │                                 │
│         ▼                             ▼                                 │
│  3a. ACCEPTANCE                 3b. REJECTION                           │
│      Customer signs              Customer provides                      │
│      Acceptance Form             written deficiency list                │
│         │                             │                                 │
│         │                             ▼                                 │
│         │                      4. REMEDIATION                           │
│         │                         Provider addresses                    │
│         │                         deficiencies                          │
│         │                             │                                 │
│         │                             ▼                                 │
│         │                      5. RE-DELIVERY                           │
│         │                         Return to step 2                      │
│         │                             │                                 │
│         └──────────────┬──────────────┘                                │
│                        │                                                │
│                        ▼                                                │
│  6. MILESTONE COMPLETE                                                  │
│     Proceed to next milestone                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Acceptance Timeframes

| Activity | Timeframe |
|----------|-----------|
| Customer review period | 5 Business Days |
| Provider remediation (minor) | 3 Business Days |
| Provider remediation (major) | 5 Business Days |
| Re-review period | 3 Business Days |
| Escalation trigger | 2 failed acceptance cycles |

### 6.4 Deemed Acceptance

If Customer does not provide written acceptance or rejection within the review period, the Deliverable shall be deemed accepted, unless Customer has provided written notice of extension with specific reasons.

---

## 7. ROLES AND RESPONSIBILITIES

### 7.1 Provider Responsibilities

| Role | Responsibilities |
|------|------------------|
| **Engagement Director** | Overall delivery accountability, escalation point |
| **Solution Architect** | Technical design, architecture decisions |
| **Project Manager** | Schedule, resources, status reporting, risk management |
| **Technical Lead** | Development oversight, code quality, technical decisions |
| **Development Team** | Feature implementation, testing, documentation |
| **DevOps Engineer** | Infrastructure, CI/CD, deployment |
| **QA Engineer** | Testing strategy, test execution, quality assurance |

### 7.2 Customer Responsibilities

| Role | Responsibilities |
|------|------------------|
| **Executive Sponsor** | Strategic direction, escalation authority, funding |
| **Project Manager** | Customer-side coordination, resource allocation |
| **Technical Lead** | Technical decisions, integration coordination |
| **EUC Engineers** | Domain expertise, requirements validation, UAT |
| **Security Team** | Security review, compliance validation |
| **Operations Team** | Operational requirements, runbook validation |
| **Infrastructure Team** | Environment provisioning, network access |

### 7.3 RACI Matrix

| Activity | Provider | Customer |
|----------|----------|----------|
| Architecture design | **R, A** | C, I |
| Architecture approval | I | **R, A** |
| Development | **R, A** | I |
| Testing (functional) | **R, A** | I |
| Testing (UAT) | C | **R, A** |
| Infrastructure provisioning | C | **R, A** |
| Security audit | C | **R, A** |
| Deployment (non-prod) | **R, A** | C |
| Deployment (production) | **R** | **A** |
| Training delivery | **R, A** | C |
| Documentation | **R, A** | C |
| Go-Live decision | C | **R, A** |

**Legend**: R=Responsible, A=Accountable, C=Consulted, I=Informed

---

## 8. TECHNICAL REQUIREMENTS

### 8.1 Infrastructure Requirements (Customer-Provided)

#### 8.1.1 Compute Requirements

| Environment | CPU (cores) | Memory (GB) | Storage | Quantity |
|-------------|-------------|-------------|---------|----------|
| **Development** | 16 | 64 | 500GB SSD | 1 |
| **Staging** | 32 | 128 | 1TB SSD | 1 |
| **Production** | 64 | 256 | 2TB SSD | 3 (HA) |

#### 8.1.2 Network Requirements

| Requirement | Specification |
|-------------|---------------|
| **Internal bandwidth** | ≥1 Gbps |
| **Internet egress** | Required for cloud MDM APIs |
| **Load balancer** | L7 with SSL termination |
| **DNS** | Internal DNS entries for services |
| **Firewall rules** | See Appendix A |

#### 8.1.3 Software Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Kubernetes | 1.28+ | Container orchestration |
| PostgreSQL | 15+ | Relational database |
| Redis | 7+ | Cache and message broker |
| Docker | 24+ | Container runtime |

### 8.2 Integration Requirements (Customer-Provided)

| System | Requirement | Provider Responsibility |
|--------|-------------|------------------------|
| **Azure AD/Entra ID** | App registration, API permissions | Connector implementation |
| **Microsoft Intune** | Admin consent, Graph API access | Connector implementation |
| **Jamf Pro** | API credentials, service account | Connector implementation |
| **SCCM** | Service account, WMI access | Connector implementation |
| **ServiceNow** | API credentials, table access | Connector implementation |

### 8.3 Security Requirements

| Requirement | Specification |
|-------------|---------------|
| **TLS Version** | 1.3 minimum |
| **Certificate Authority** | Customer PKI or Let's Encrypt |
| **Secret Storage** | HashiCorp Vault or K8s Secrets |
| **MFA** | Required for all admin access |
| **Audit Retention** | 730 days minimum |

---

## 9. QUALITY STANDARDS

### 9.1 Code Quality Standards

| Metric | Target | Enforcement |
|--------|--------|-------------|
| **Test Coverage** | ≥90% | CI/CD gate |
| **TypeScript Errors** | 0 | Pre-commit hook |
| **Linting Warnings** | 0 | Pre-commit hook |
| **Security Vulnerabilities** | 0 critical/high | CI/CD gate |
| **Technical Debt** | ≤5 min/file | SonarQube |
| **Cognitive Complexity** | ≤15/function | SonarQube |

### 9.2 Testing Standards

| Test Type | Coverage | Execution |
|-----------|----------|-----------|
| **Unit Tests** | ≥90% | Every commit |
| **Integration Tests** | ≥80% | Every PR |
| **E2E Tests** | Critical paths | Daily |
| **Performance Tests** | Key workflows | Weekly |
| **Security Tests** | OWASP Top 10 | Weekly |

### 9.3 Documentation Standards

| Document Type | Standard |
|---------------|----------|
| **Code Comments** | JSDoc/docstrings for public APIs |
| **API Documentation** | OpenAPI 3.0 specification |
| **Architecture** | C4 model diagrams |
| **Runbooks** | Structured with pre/post conditions |

---

## 10. CHANGE MANAGEMENT

### 10.1 Change Categories

| Category | Description | Approval Authority |
|----------|-------------|-------------------|
| **Minor** | <5% effort impact, no scope change | Project Manager |
| **Moderate** | 5-15% effort impact, scope clarification | Steering Committee |
| **Major** | >15% effort impact, scope expansion | Executive + Change Order |

### 10.2 Change Request Process

1. **Initiation**: Either party submits written Change Request
2. **Impact Assessment**: Provider analyzes scope, schedule, cost impact
3. **Review**: Project Managers review and recommend
4. **Approval**: Appropriate authority approves/rejects
5. **Documentation**: Approved changes documented in Change Log
6. **Implementation**: Changes incorporated into project plan

### 10.3 Change Request Form

| Field | Description |
|-------|-------------|
| Request ID | Unique identifier |
| Requestor | Name and organization |
| Date Submitted | Submission date |
| Description | Detailed change description |
| Justification | Business rationale |
| Impact Analysis | Scope, schedule, cost impacts |
| Recommendation | Project Manager recommendation |
| Decision | Approved/Rejected/Deferred |
| Approver | Name and date |

---

## 11. RISK MANAGEMENT

### 11.1 Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|----|------|------------|--------|------------|-------|
| **R-01** | Customer infrastructure delays | Medium | High | Early provisioning, cloud fallback | Customer PM |
| **R-02** | Integration API changes | Low | Medium | Version pinning, abstraction layer | Provider TL |
| **R-03** | Security audit findings | Medium | High | Early security review, remediation buffer | Provider TL |
| **R-04** | Resource availability | Medium | Medium | Cross-training, documentation | Both PMs |
| **R-05** | Scope creep | High | High | Change control process, backlog grooming | Provider PM |
| **R-06** | Performance at scale | Low | High | Early load testing, architecture review | Provider Arch |
| **R-07** | Data migration complexity | Medium | Medium | Phased migration, validation | Both TLs |

### 11.2 Risk Response Strategies

| Strategy | Description | When to Use |
|----------|-------------|-------------|
| **Avoid** | Eliminate the risk | High impact, controllable |
| **Mitigate** | Reduce likelihood or impact | Most risks |
| **Transfer** | Shift to third party | Specialized risks |
| **Accept** | Acknowledge and monitor | Low impact risks |

### 11.3 Risk Review

Risks will be reviewed:
- Weekly at Project Management meetings
- Bi-weekly at Sprint Reviews
- Monthly at Steering Committee meetings

---

## 12. PRICING AND PAYMENT

### 12.1 Pricing Summary

| Item | Description | Amount |
|------|-------------|--------|
| **Fixed Price** | Platform implementation (D-01 through D-09) | $________________ |
| **Training** | Training delivery (D-10) | $________________ |
| **Total Contract Value** | | $________________ |

### 12.2 Payment Schedule

| Milestone | Percentage | Amount | Due |
|-----------|------------|--------|-----|
| **Contract Signing** | 20% | $________ | Upon execution |
| **M2: Core Platform** | 20% | $________ | Week 4 |
| **M5: License Module** | 20% | $________ | Week 7 |
| **M8: Security Audit** | 20% | $________ | Week 10 |
| **M10: Training Complete** | 20% | $________ | Week 12 |

### 12.3 Payment Terms

- Invoices issued upon milestone acceptance
- Payment due within 30 days of invoice
- Late payments subject to 1.5% monthly interest

### 12.4 Expenses

Travel and expenses, if required, will be:
- Pre-approved by Customer
- Billed at cost with receipts
- Subject to Customer travel policy limits

---

## 13. SERVICE LEVEL AGREEMENT

### 13.1 Platform SLAs (Post Go-Live)

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Platform Availability** | 99.5% monthly | Uptime monitoring |
| **API Response Time (p95)** | ≤500ms | APM monitoring |
| **API Response Time (p99)** | ≤1000ms | APM monitoring |
| **Deployment Success Rate** | ≥98% | Platform metrics |
| **Incident Response (P1)** | ≤30 minutes | Ticket timestamps |
| **Incident Response (P2)** | ≤2 hours | Ticket timestamps |
| **Incident Resolution (P1)** | ≤4 hours | Ticket timestamps |
| **Incident Resolution (P2)** | ≤8 hours | Ticket timestamps |

### 13.2 Incident Severity Definitions

| Severity | Definition | Examples |
|----------|------------|----------|
| **P1 Critical** | Platform unavailable, all users affected | Complete outage, data loss |
| **P2 High** | Major feature unavailable, business impact | Connector failure, approval blocked |
| **P3 Medium** | Feature degraded, workaround available | Slow performance, UI glitch |
| **P4 Low** | Minor issue, no business impact | Cosmetic issue, documentation error |

### 13.3 Support Hours

| Support Type | Hours | Coverage |
|--------------|-------|----------|
| **P1 Critical** | 24x7 | Phone + email |
| **P2 High** | Business hours | Email + ticket |
| **P3/P4** | Business hours | Email + ticket |

Business hours: Monday-Friday, 9:00 AM - 6:00 PM Customer local time

---

## 14. WARRANTY AND SUPPORT

### 14.1 Warranty Period

Provider warrants that the Platform will perform in accordance with specifications for a period of **90 days** from Go-Live acceptance ("Warranty Period").

### 14.2 Warranty Coverage

During the Warranty Period, Provider will:
- Correct defects in functionality at no additional cost
- Provide patches for security vulnerabilities
- Provide reasonable support for operational issues

### 14.3 Warranty Exclusions

Warranty does not cover:
- Issues caused by Customer modifications
- Issues caused by Customer infrastructure
- Issues caused by third-party software
- Enhancements or new features
- Customer training beyond initial delivery

### 14.4 Post-Warranty Support

Post-warranty support available under separate Support Agreement with terms to be negotiated prior to warranty expiration.

---

## 15. INTELLECTUAL PROPERTY

### 15.1 Provider IP

Provider retains all rights to:
- EUCORA platform core code
- Frameworks, libraries, and tools
- Methodologies and processes
- Pre-existing intellectual property

### 15.2 Customer IP

Customer retains all rights to:
- Customer data and content
- Customer-specific configurations
- Customer-specific integrations (if developed separately)

### 15.3 License Grant

Provider grants Customer a perpetual, non-exclusive, non-transferable license to use the EUCORA platform for Customer's internal business purposes, subject to license terms.

### 15.4 Deliverable Ownership

| Deliverable Type | Ownership |
|------------------|-----------|
| Platform code | Provider (licensed to Customer) |
| Configuration | Customer |
| Documentation | Provider (licensed to Customer) |
| Customer data | Customer |
| Integrations | Per integration terms |

---

## 16. CONFIDENTIALITY

### 16.1 Confidential Information

"Confidential Information" includes:
- Technical specifications and architecture
- Business processes and requirements
- Pricing and commercial terms
- Customer data and configurations
- Security vulnerabilities and incidents

### 16.2 Obligations

Each party agrees to:
- Protect Confidential Information with reasonable care
- Use Confidential Information only for SOW purposes
- Limit disclosure to personnel with need-to-know
- Not disclose to third parties without consent

### 16.3 Exceptions

Confidentiality obligations do not apply to information that:
- Is publicly available
- Was known prior to disclosure
- Is independently developed
- Is required by law to disclose

### 16.4 Duration

Confidentiality obligations survive termination for **3 years**.

---

## 17. COMPLIANCE AND SECURITY

### 17.1 Regulatory Compliance

Provider will implement controls aligned with:

| Framework | Scope |
|-----------|-------|
| **GDPR** | Data residency, erasure, consent |
| **India DPDP** | Data processing, minimization |
| **SOC2 Type II** | Security, availability, confidentiality |
| **ISO 27001** | ISMS controls |

### 17.2 Security Controls

Provider will implement:
- Zero-trust architecture
- Encryption at rest and in transit
- RBAC with least privilege
- Audit logging and monitoring
- Vulnerability management
- Incident response procedures

### 17.3 Security Audit

Customer may conduct or commission security audit:
- Once per year at Customer expense
- With 30 days written notice
- During business hours
- With confidentiality protection for findings

### 17.4 Data Processing

Provider will:
- Process Customer data only as instructed
- Not transfer data outside Customer boundary
- Notify Customer of data breaches within 72 hours
- Delete Customer data upon termination

---

## 18. TERMINATION

### 18.1 Termination for Convenience

Either party may terminate with **60 days** written notice.

### 18.2 Termination for Cause

Either party may terminate immediately upon:
- Material breach not cured within 30 days of notice
- Insolvency or bankruptcy
- Force majeure exceeding 90 days

### 18.3 Effect of Termination

Upon termination:
- Provider delivers all completed Deliverables
- Provider provides transition assistance for 30 days
- Customer pays for accepted Deliverables and work-in-progress
- Confidentiality obligations survive

### 18.4 Transition Assistance

Provider will provide:
- Data export in standard formats
- Documentation handover
- Knowledge transfer sessions
- Reasonable support for transition

---

## 19. SIGNATURES

### 19.1 Provider Authorization

By signing below, Provider authorizes this Statement of Work and commits to deliver the specified Deliverables according to the terms herein.

```
BUILDWORKS.AI

Signature: _________________________________

Name: _________________________________

Title: _________________________________

Date: _________________________________
```

### 19.2 Customer Authorization

By signing below, Customer authorizes this Statement of Work and commits to provide the resources and access required for successful delivery.

```
[CUSTOMER LEGAL NAME]

Signature: _________________________________

Name: _________________________________

Title: _________________________________

Date: _________________________________
```

---

## 20. APPENDICES

### Appendix A: Network Requirements

#### A.1 Firewall Rules (Outbound)

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| EUCORA | graph.microsoft.com | 443 | HTTPS | Intune/Entra API |
| EUCORA | login.microsoftonline.com | 443 | HTTPS | Azure AD auth |
| EUCORA | *.jamfcloud.com | 443 | HTTPS | Jamf Pro API |
| EUCORA | Customer SCCM | 443/80 | HTTPS/HTTP | SCCM API |
| EUCORA | Customer ServiceNow | 443 | HTTPS | ITSM API |

#### A.2 Firewall Rules (Inbound)

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Users | EUCORA LB | 443 | HTTPS | Portal access |
| Agents | EUCORA LB | 443 | HTTPS | Telemetry ingestion |
| Webhooks | EUCORA LB | 443 | HTTPS | Event webhooks |

### Appendix B: Environment Specifications

#### B.1 Development Environment

| Component | Specification |
|-----------|---------------|
| **Kubernetes** | Single node, 16 cores, 64GB RAM |
| **PostgreSQL** | Single instance, 100GB storage |
| **MinIO** | Single instance, 200GB storage |
| **Redis** | Single instance |

#### B.2 Staging Environment

| Component | Specification |
|-----------|---------------|
| **Kubernetes** | 3 nodes, 32 cores total, 128GB RAM total |
| **PostgreSQL** | Primary + standby, 250GB storage |
| **MinIO** | 4 nodes, 500GB per node |
| **Redis** | 3 node cluster |

#### B.3 Production Environment

| Component | Specification |
|-----------|---------------|
| **Kubernetes** | 5+ nodes, 64 cores total, 256GB RAM total |
| **PostgreSQL** | Primary + standby, 500GB storage |
| **MinIO** | 4 nodes, 2TB per node |
| **Redis** | 3 node cluster |
| **Load Balancer** | HA pair |

### Appendix C: Acceptance Test Cases

#### C.1 Core Platform Tests

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| CP-01 | User login via Azure AD | Successful authentication, session created |
| CP-02 | Create package from MSI | Package created, SBOM generated |
| CP-03 | Create deployment intent | Intent created with correlation ID |
| CP-04 | Submit for CAB approval | Approval request created, evidence attached |
| CP-05 | Approve deployment | Deployment promoted to next ring |
| CP-06 | View audit trail | All actions visible with timestamps |

#### C.2 Connector Tests

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| CN-01 | Intune: Test connection | Connection successful |
| CN-02 | Intune: Sync inventory | Devices synced, count accurate |
| CN-03 | Intune: Push deployment | App published, assignment created |
| CN-04 | Jamf: Test connection | Connection successful |
| CN-05 | Jamf: Push package | Package uploaded, policy created |
| CN-06 | Drift detection | Drift events generated correctly |

#### C.3 License Management Tests

| ID | Test Case | Expected Result |
|----|-----------|-----------------|
| LM-01 | Create vendor/SKU | Entities created, audit logged |
| LM-02 | Create entitlement | Entitlement created with approval |
| LM-03 | Ingest consumption signals | Signals normalized, deduplicated |
| LM-04 | Run reconciliation | Snapshot created with evidence |
| LM-05 | Verify sidebar | Counters match snapshot |
| LM-06 | Over-consumption alert | Alert generated |
| LM-07 | Export evidence | Complete pack exported |

### Appendix D: Training Curriculum

#### D.1 Platform Administration (8 hours)

| Module | Duration | Topics |
|--------|----------|--------|
| Introduction | 1 hour | Architecture overview, components |
| User Management | 1 hour | Users, roles, groups, AD sync |
| Configuration | 2 hours | Connectors, policies, settings |
| Monitoring | 2 hours | Dashboards, alerts, troubleshooting |
| Maintenance | 2 hours | Backup, restore, upgrades |

#### D.2 Packaging & Deployment (8 hours)

| Module | Duration | Topics |
|--------|----------|--------|
| Packaging Basics | 2 hours | Package types, metadata, SBOM |
| Deployment Workflow | 2 hours | Intents, rings, promotion |
| CAB Process | 2 hours | Evidence, approval, risk scoring |
| Troubleshooting | 2 hours | Common issues, rollback |

#### D.3 License Management (4 hours)

| Module | Duration | Topics |
|--------|----------|--------|
| Concepts | 1 hour | SKUs, entitlements, consumption |
| Operations | 2 hours | Reconciliation, alerts, reports |
| AI Agents | 1 hour | Optimization, recommendations |

### Appendix E: Change Order Template

```
CHANGE ORDER

Change Order Number: CO-____
Date: ________________
Related SOW: EUCORA-SOW-2026-001

CHANGE DESCRIPTION:
_________________________________________________________________
_________________________________________________________________

JUSTIFICATION:
_________________________________________________________________
_________________________________________________________________

IMPACT ANALYSIS:
- Scope Impact: ________________________________________________
- Schedule Impact: _____________________________________________
- Cost Impact: $________________________________________________

APPROVALS:

Provider Project Manager: _________________ Date: ________
Customer Project Manager: _________________ Date: ________
Steering Committee (if required): _________ Date: ________
```

---

**END OF STATEMENT OF WORK**

*This Statement of Work, together with its Appendices, constitutes the complete agreement between the parties for the EUCORA implementation project.*
