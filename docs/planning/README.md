# EUCORA Planning Documentation

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

---

## Overview

This directory contains strategic planning documentation for EUCORA enhancements and development phases.

---

## Document Index

### Strategic Foundation (Phase 1)

| Document | Description | Status |
|----------|-------------|--------|
| `00-strategic-overview.md` | Strategic vision for Application Lifecycle & Portfolio Management | Active |
| `01-persona-requirements.md` | Stakeholder persona definitions and requirements | Active |
| `02-portfolio-data-model.md` | Portfolio management data model design | Active |
| `03-ui-wireframes.md` | UI/UX wireframe specifications | Active |
| `04-ai-agent-specifications.md` | AI agent capabilities and use cases | Active |

### Phase 2 Enhancement Roadmap

| Document | Description | Priority | Status |
|----------|-------------|----------|--------|
| `05-enhancement-roadmap-phase2.md` | **Master roadmap for Phase 2 enhancements** | — | Active |
| `10-document-management-rag.md` | E1: Policy document upload with RAG pipeline | P1-Critical | Ready |
| `11-storage-configuration.md` | E2: Multi-cloud storage (MinIO/S3/Azure) | P1-Critical | Ready |
| `12-comprehensive-rbac.md` | E3: 9-persona RBAC with strict isolation | P0-Blocker | Ready |
| `13-1e-dex-integration.md` | E4: 1E DEX Platform integration | P2-High | Ready |
| `14-application-policy-ui.md` | E5: Deployment policy configuration UI | P1-Critical | Ready |
| `15-application-stack-ux.md` | E6: Best-in-class application stack visualization | P2-High | Ready |
| `16-vector-storage-pgvector.md` | E7: pgvector for AI knowledge retrieval | P1-Critical | Ready |
| `17-ai-agent-workflows.md` | E8: Autonomous R1, approval-gated R2/R3 workflows | P1-Critical | Ready |
| `18-powershell-production-audit.md` | E9: Script hardening and endpoint validation | P1-Critical | Ready |
| `19-cmdb-integration-agent.md` | E10: CMDB data maintenance and validation agent | P2-High | Ready |
| `20-change-communications-agent.md` | E11: Change rollout and stakeholder communications | P2-High | Ready |
| `21-documentation-agent.md` | E12: Auto-documentation from codebases | P3-Medium | Ready |
| `22-automation-advisor-agent.md` | E13: ROI-based automation opportunity detection | P3-Medium | Ready |
| `23-discovery-agent.md` | E14: Application inventory and gap analysis | P2-High | Ready |
| `24-iam-security-agent.md` | E15: Identity access anomaly detection | P2-High | Ready |
| `25-request-coordination-agent.md` | E16: Service request tracking and escalation | P3-Medium | Ready |
| `26-secops-agent.md` | E17: Vulnerability remediation and SIEM integration | P1-Critical | Ready |
| `27-sre-agent.md` | E18: Self-healing, SLO monitoring, runbook automation | P1-Critical | Ready |
| `28-sla-governance-agent.md` | E19: Natural language SLA creation, KPI tracking | P2-High | Ready |
| `29-planning-agent.md` | E20: Deployment planning, ring strategy, blast radius | P2-High | Ready |
| `30-kb-triage-agent.md` | E21: AI ticket triage, knowledge synthesis | P1-Critical | Ready |

### Operational Documents

| Document | Description | Status |
|----------|-------------|--------|
| `BLOCKING-ISSUES-TRACKER.md` | Current blocking issues | Active |
| `CONNECTOR-AUDIT-STATUS.md` | Connector implementation status | Active |
| `CRITICAL-ASSESSMENT-JAN-2026.md` | Critical assessment and priorities | Active |
| `EXECUTION-TIMELINE-2026.md` | Execution timeline | Active |
| `MASTER-IMPLEMENTATION-PLAN-2026.md` | Master implementation plan | Active |
| `SOW-ALIGNED-PRODUCTION-READINESS.md` | SOW alignment and production readiness | Active |
| `WEEK-BY-WEEK-EXECUTION-PLAN.md` | Detailed weekly execution plan | Active |

---

## Phase 2 Enhancement Summary (40 Weeks Total)

### Sprint 1-2: Foundation (Weeks 1-4)
- **E3**: Comprehensive RBAC (P0-Blocker)
- **E2**: Storage Configuration (P1-Critical)

### Sprint 3-4: Knowledge Infrastructure (Weeks 5-8)
- **E7**: Vector Storage (P1-Critical)
- **E1**: Document Management & RAG (P1-Critical)

### Sprint 5-6: AI & Workflows (Weeks 9-12)
- **E8**: AI Agent Workflows (P1-Critical)

### Sprint 7-8: Deployment Experience (Weeks 13-16)
- **E5**: Application Policy UI (P1-Critical)
- **E6**: Application Stack UX (P2-High)

### Sprint 9-10: Integration & Hardening (Weeks 17-20)
- **E4**: 1E DEX Integration (P2-High)
- **E9**: PowerShell Production Audit (P1-Critical)

### Sprint 11-12: ALM Agents - ITSM (Weeks 21-24)
- **E10**: CMDB Integration Agent (P2-High)
- **E11**: Change Communications Agent (P2-High)
- **E14**: Discovery Agent (P2-High)

### Sprint 13-14: ALM Agents - Knowledge & Automation (Weeks 25-28)
- **E12**: Documentation Agent (P3-Medium)
- **E13**: Automation Advisor Agent (P3-Medium)
- **E15**: IAM Security Agent (P2-High)

### Sprint 15-16: ALM Agents - Service Requests (Weeks 29-32)
- **E16**: Request Coordination Agent (P3-Medium)

### Sprint 17-18: ALM Agents - Security & Operations (Weeks 33-36)
- **E17**: SecOps Agent (P1-Critical)
- **E18**: SRE Agent - Self-Healing (P1-Critical)
- **E21**: KB & Triage Agent (P1-Critical)

### Sprint 19-20: ALM Agents - Governance & Planning (Weeks 37-40)
- **E19**: SLA Governance Agent (P2-High)
- **E20**: Planning Agent (P2-High)

---

## Enhancement Dependency Graph

```
                                  ┌──────────────────────────────────────────────────────────────────┐
E2 (Storage) ─────┬───────────────┼────────────────────────────────────> E4 (1E DEX)                │
                  │               │                                                                  │
                  └─────> E7 (pgvector) ────┬──> E1 (Documents) ──────┐                             │
                                            │                          │                             │
                                            ├──> E10 (CMDB) ─────────┼──> E11 (Change Comm) ────────┤
                                            │                          │          │                  │
E3 (RBAC) ──────────────┬──────────────────┼──> E5 (Policies) ───────┼──> E8 (AI Workflows) ←──────┤
                        │                  │         │                 │          │                  │
                        │                  │         └──> E6 (Stack) ──┘          │                  │
                        │                  │                                       │                  │
                        └──> E14 (Discovery) ──────────────────────────────────────┤                  │
                        │                                                          │                  │
                        └──> E15 (IAM Security) ───────────────────────────────────┤                  │
                                                                                   │                  │
                                E12 (Documentation) ←──────────────────────────────┘                  │
                                E13 (Automation Advisor) ←─────────────────────────────────────────────┘
                                E16 (Request Coordination) ←── E10, E11

E9 (PowerShell) ── Independent ──> Can start immediately
```

---

## Key Design Decisions

1. **RBAC is P0-Blocker**: All other enhancements depend on proper access control
2. **Storage before Documents**: Object storage must be configured before document upload
3. **pgvector before RAG**: Vector storage required for document semantic search
4. **Policies before Stack UX**: Policy configuration informs stack visualization
5. **All dependencies before AI Workflows**: Full context needed for agent execution

---

## Document Ownership

| Document Type | Owner | Reviewers |
|---------------|-------|-----------|
| Strategic Plans | EUCORA Advisory Team | Product Owner, Engineering Lead |
| Technical Specs | Implementation Team | Security Reviewer, CAB |
| Operational | Platform Team | Endpoint Ops, Auditor |

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-30 | 2.0 | Added Phase 2 enhancement planning documents |
| 2026-01-30 | 1.9 | Removed obsolete documents from `old/` directory |
| 2026-01-29 | 1.8 | Added strategic overview and persona requirements |
