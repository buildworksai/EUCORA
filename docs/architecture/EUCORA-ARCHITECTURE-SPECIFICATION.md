# EUCORA — Enterprise Architecture Specification

**Document ID**: EUCORA-ARCH-2026-001
**Version**: 2.0.0
**Status**: APPROVED FOR SOW
**Classification**: CONFIDENTIAL — Customer Deliverable
**Effective Date**: January 25, 2026

**SPDX-License-Identifier: Apache-2.0**

---

## Document Control

| Version | Date | Author | Reviewer | Changes |
|---------|------|--------|----------|---------|
| 1.0.0 | Jan 2026 | BuildWorks.AI | Architecture Review Board | Initial draft |
| 2.0.0 | Jan 25, 2026 | BuildWorks.AI | Customer Architecture Team | SOW alignment |

### Approval Signatures

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Solution Architect | _________________ | _________________ | ________ |
| Technical Lead | _________________ | _________________ | ________ |
| Customer Architect | _________________ | _________________ | ________ |
| Project Sponsor | _________________ | _________________ | ________ |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Principles](#2-architecture-principles)
3. [System Context](#3-system-context)
4. [Logical Architecture](#4-logical-architecture)
5. [Component Architecture](#5-component-architecture)
6. [Data Architecture](#6-data-architecture)
7. [Integration Architecture](#7-integration-architecture)
8. [Security Architecture](#8-security-architecture)
9. [Infrastructure Architecture](#9-infrastructure-architecture)
10. [AI/ML Architecture](#10-aiml-architecture)
11. [Observability Architecture](#11-observability-architecture)
12. [Deployment Architecture](#12-deployment-architecture)
13. [Non-Functional Requirements](#13-non-functional-requirements)
14. [Technology Stack](#14-technology-stack)
15. [Architecture Decision Records](#15-architecture-decision-records)
16. [Appendices](#16-appendices)

---

## 1. Executive Summary

### 1.1 Purpose

This Architecture Specification defines the technical architecture for EUCORA (End-User Computing Orchestration & Reliability Architecture), an enterprise-grade platform for automated application packaging, deployment, governance, and AI-assisted remediation across heterogeneous endpoint environments.

### 1.2 Scope

This document covers:
- System architecture and component design
- Data models and integration patterns
- Security and compliance architecture
- Infrastructure and deployment topology
- AI/ML governance and execution framework
- Operational and observability requirements

### 1.3 Audience

| Audience | Purpose |
|----------|---------|
| Customer Architecture Team | SOW validation, technical alignment |
| Implementation Engineers | Development guidance |
| Operations Team | Deployment and operational planning |
| Security Team | Security review and approval |
| Executive Stakeholders | Investment decision support |

### 1.4 Product Vision

EUCORA serves as a **thin control plane** that standardizes governance, evidence, and determinism across endpoint execution tools (Intune, Jamf, SCCM, Landscape, Ansible). The platform delivers:

- **Automated Packaging & Deployment**: Multi-platform application lifecycle management
- **Deterministic Governance**: Evidence-based change control with CAB workflows
- **AI-Assisted Operations**: Human-in-loop remediation with explainable recommendations
- **Comprehensive License Management**: SAM-grade software asset tracking
- **Enterprise Observability**: Full telemetry, metrics, and audit capabilities

### 1.5 Key Architectural Characteristics

| Characteristic | Description |
|----------------|-------------|
| **Control Plane Separation** | Orchestration layer distinct from execution planes |
| **Evidence-First Governance** | All decisions backed by auditable evidence packs |
| **Deterministic Operations** | No "AI magic" — all scores explainable |
| **Human-in-Loop Safety** | High-risk actions require human approval |
| **Data Residency** | Self-hosted with zero cloud egress by default |
| **Zero-Trust Security** | Identity-bound access, continuous verification |

---

## 2. Architecture Principles

### 2.1 Core Principles

| ID | Principle | Rationale | Implications |
|----|-----------|-----------|--------------|
| **AP-01** | Thin Control Plane | Control plane handles policy, orchestration, evidence — not device management primitives | Execution planes (Intune, Jamf, etc.) remain authoritative for device operations |
| **AP-02** | Separation of Duties | Packaging ≠ Publishing ≠ Approval | Hard RBAC boundaries, no shared credentials |
| **AP-03** | Determinism | All risk scores computed from explicit, weighted factors | No opaque ML-driven decisions; all outcomes explainable |
| **AP-04** | Evidence-First | Every CAB submission includes complete evidence pack | Audit-ready from day one |
| **AP-05** | Idempotency | All deployment actions retryable safely | Connectors use idempotent keys |
| **AP-06** | Reconciliation over Hope | Continuous desired-vs-actual drift detection | Reconciliation loops, not one-time pushes |
| **AP-07** | Offline-First | Air-gapped and intermittent connectivity as first-class constraints | Site classification, offline-aware distribution |
| **AP-08** | Human-in-Loop | High-risk AI actions require human approval | R2/R3 risk actions blocked without approval |
| **AP-09** | Data Sovereignty | Customer controls all data residency | Self-hosted MinIO + PostgreSQL, no external egress |
| **AP-10** | Zero-Trust | No implicit trust between services, users, devices | mTLS, identity-bound access, continuous verification |

### 2.2 Architecture Constraints

| ID | Constraint | Source |
|----|------------|--------|
| **AC-01** | Single-tenant deployment only | Customer requirement |
| **AC-02** | No SaaS dependencies for core operations | Air-gapped support |
| **AC-03** | PostgreSQL as primary relational store | Operational familiarity |
| **AC-04** | S3-compatible object storage (MinIO) | Data residency |
| **AC-05** | Kubernetes-native deployment preferred | Production topology |
| **AC-06** | 100,000 devices per tenant minimum | Scale requirement |
| **AC-07** | Sub-second API response time | Performance requirement |
| **AC-08** | 99.5% platform availability | SLA requirement |

---

## 3. System Context

### 3.1 Context Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ENTERPRISE BOUNDARY                                 │
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   End       │  │   EUC       │  │   Service   │  │   Security  │           │
│  │   Users     │  │   Engineers │  │   Desk      │  │   Team      │           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                │                │                │                   │
│         ▼                ▼                ▼                ▼                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                         │   │
│  │                         EUCORA CONTROL PLANE                            │   │
│  │                                                                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │   │
│  │  │ Portal   │ │ API      │ │ Policy   │ │ AI       │ │ Audit    │      │   │
│  │  │ UI       │ │ Gateway  │ │ Engine   │ │ Services │ │ Services │      │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │   │
│  │                                                                         │   │
│  └────────────────────────────────┬────────────────────────────────────────┘   │
│                                   │                                            │
│         ┌─────────────────────────┼─────────────────────────┐                  │
│         │                         │                         │                  │
│         ▼                         ▼                         ▼                  │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐          │
│  │   INTUNE    │           │    JAMF     │           │    SCCM     │          │
│  │  (Windows)  │           │   (macOS)   │           │  (Legacy)   │          │
│  └──────┬──────┘           └──────┬──────┘           └──────┬──────┘          │
│         │                         │                         │                  │
│         └─────────────────────────┼─────────────────────────┘                  │
│                                   │                                            │
│                                   ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           ENDPOINT DEVICES                              │   │
│  │                                                                         │   │
│  │   ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐          │   │
│  │   │Windows │  │ macOS  │  │ Linux  │  │  iOS   │  │Android │          │   │
│  │   │ 10/11  │  │  13+   │  │Ubuntu  │  │iPadOS  │  │  Ent.  │          │   │
│  │   └────────┘  └────────┘  └────────┘  └────────┘  └────────┘          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
  ┌─────────────┐             ┌─────────────┐             ┌─────────────┐
  │  ITSM       │             │  Identity   │             │  SIEM       │
  │ ServiceNow  │             │  Azure AD   │             │  Splunk     │
  │ Jira        │             │  Okta       │             │  Sentinel   │
  └─────────────┘             └─────────────┘             └─────────────┘
```

### 3.2 External System Interfaces

| System | Interface Type | Data Flow | Protocol |
|--------|---------------|-----------|----------|
| **Microsoft Intune** | Bidirectional | App deployment, compliance, telemetry | Microsoft Graph API (REST) |
| **Jamf Pro** | Bidirectional | Package deployment, policy, inventory | Jamf Pro API (REST) |
| **Microsoft SCCM** | Bidirectional | Package distribution, collections | WMI/REST/PowerShell |
| **Canonical Landscape** | Bidirectional | Package management, compliance | Landscape API (REST) |
| **Ansible AWX/Tower** | Bidirectional | Playbook execution, inventory | AWX API (REST) |
| **Azure AD / Entra ID** | Inbound | User/group sync, authentication | OIDC/SCIM/Graph API |
| **ServiceNow** | Bidirectional | Incident sync, CMDB, approvals | REST/Webhooks |
| **Jira** | Bidirectional | Issue tracking, workflow integration | REST API |
| **Splunk/Sentinel** | Outbound | Security events, audit logs | Syslog/REST |
| **Apple Business Manager** | Inbound | Device enrollment, VPP licenses | ABM API |
| **Google Android Enterprise** | Bidirectional | Managed Play, device enrollment | Android Management API |

### 3.3 User Personas

| Persona | Primary Functions | Access Level |
|---------|-------------------|--------------|
| **Platform Administrator** | Platform configuration, integrations, policies | Full control plane |
| **Packaging Engineer** | Build, test, sign artifacts; publish to staging | Staging only |
| **Publisher** | Publish approved artifacts to production | Scoped production |
| **CAB Approver** | Review evidence, approve/deny changes | Approval workflow |
| **Security Reviewer** | SBOM/scan policy, exception approval | Security policies |
| **Endpoint Operations** | Monitor telemetry, trigger remediation | Device-scoped |
| **License Administrator** | Vendor/SKU management, entitlements | License module |
| **Auditor** | Read-only access to events and evidence | Audit trail |
| **End User** | Self-service portal, app requests | Self-service only |

---

## 4. Logical Architecture

### 4.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Admin       │  │ Self-Service│  │ API         │  │ Webhook     │        │
│  │ Portal      │  │ Portal      │  │ Consumers   │  │ Subscribers │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Authentication │ Authorization │ Rate Limiting │ Request Routing        ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           APPLICATION LAYER                                  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Packaging    │  │ Deployment   │  │ CAB Workflow │  │ Policy       │    │
│  │ Service      │  │ Service      │  │ Service      │  │ Engine       │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ License      │  │ Portfolio    │  │ Telemetry    │  │ AI Agent     │    │
│  │ Management   │  │ Management   │  │ Service      │  │ Service      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ User         │  │ Connector    │  │ Evidence     │  │ Event        │    │
│  │ Management   │  │ Service      │  │ Service      │  │ Store        │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           INTEGRATION LAYER                                  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Intune       │  │ Jamf         │  │ SCCM         │  │ Landscape    │    │
│  │ Connector    │  │ Connector    │  │ Connector    │  │ Connector    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Ansible      │  │ AD/Entra     │  │ ITSM         │  │ SIEM         │    │
│  │ Connector    │  │ Connector    │  │ Connector    │  │ Connector    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
┌────────────────────────────────────┼────────────────────────────────────────┐
│                           DATA LAYER                                         │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ PostgreSQL   │  │ MinIO        │  │ Redis        │  │ Prometheus   │    │
│  │ (Metadata)   │  │ (Artifacts)  │  │ (Cache/Queue)│  │ (Metrics)    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐                                         │
│  │ Loki         │  │ Tempo        │                                         │
│  │ (Logs)       │  │ (Traces)     │                                         │
│  └──────────────┘  └──────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Domain Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE DOMAINS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PACKAGING & DEPLOYMENT                            │    │
│  │                                                                      │    │
│  │  Package ──┬── PackageVersion ──── Artifact                         │    │
│  │            │                                                         │    │
│  │            └── DeploymentIntent ──┬── Ring ──── PromotionGate       │    │
│  │                                   │                                  │    │
│  │                                   └── Deployment ──── DeploymentEvent│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    GOVERNANCE & COMPLIANCE                           │    │
│  │                                                                      │    │
│  │  PolicyRule ──── RiskFactor ──── RiskAssessment                     │    │
│  │                                                                      │    │
│  │  CABApprovalRequest ──┬── CABApproval ──── ApprovalDecision         │    │
│  │                       │                                              │    │
│  │                       └── EvidencePack ──── EvidenceArtifact        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    LICENSE MANAGEMENT                                │    │
│  │                                                                      │    │
│  │  Vendor ──── LicenseSKU ──┬── Entitlement ──── Contract             │    │
│  │                           │                                          │    │
│  │                           ├── LicensePool ──── Assignment           │    │
│  │                           │                                          │    │
│  │                           └── ConsumptionSignal ──── ConsumptionUnit│    │
│  │                                                                      │    │
│  │  ReconciliationRun ──── ConsumptionSnapshot ──── LicenseAlert       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PORTFOLIO MANAGEMENT                              │    │
│  │                                                                      │    │
│  │  Application ──┬── ApplicationVersion ──── Vulnerability            │    │
│  │                │                                                     │    │
│  │                ├── ApplicationDependency                             │    │
│  │                │                                                     │    │
│  │                ├── ApplicationLicenseAssociation ──── LicenseSKU    │    │
│  │                │                                                     │    │
│  │                └── PortfolioRiskScore                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    TELEMETRY & DEVICES                               │    │
│  │                                                                      │    │
│  │  Device ──┬── DeviceHealth ──── TelemetryMetric                     │    │
│  │           │                                                          │    │
│  │           ├── SoftwareInventory                                      │    │
│  │           │                                                          │    │
│  │           └── DeviceUserMap ──── User                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    AI & AGENTS                                       │    │
│  │                                                                      │    │
│  │  AIModel ──── AgentExecution ──┬── AgentApproval                    │    │
│  │                                │                                     │    │
│  │                                └── ModelDriftMetric                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Component Architecture

### 5.1 Component Catalog

| Component | Responsibility | Technology | Scaling |
|-----------|---------------|------------|---------|
| **eucora-api-gateway** | Request routing, auth, rate limiting | Kong/Nginx | Horizontal |
| **eucora-portal-ui** | Admin and self-service web interface | React 18, TypeScript | Horizontal |
| **eucora-packaging-service** | Package intake, validation, SBOM | Django 5.1, Celery | Horizontal |
| **eucora-deployment-service** | Ring orchestration, deployment jobs | Django 5.1, Celery | Horizontal |
| **eucora-cab-service** | Approval workflows, risk assessment | Django 5.1 | Horizontal |
| **eucora-policy-engine** | Policy evaluation, compliance scoring | Django 5.1 | Horizontal |
| **eucora-license-service** | License management, reconciliation | Django 5.1, Celery | Horizontal |
| **eucora-portfolio-service** | Application portfolio management | Django 5.1 | Horizontal |
| **eucora-telemetry-service** | Telemetry ingestion, device health | Django 5.1, Redis | Horizontal |
| **eucora-ai-service** | AI agents, model registry, inference | Django 5.1, Python ML | Vertical + Horizontal |
| **eucora-connector-service** | Execution plane adapters | Django 5.1, Celery | Horizontal |
| **eucora-user-service** | User management, RBAC, AD sync | Django 5.1 | Horizontal |
| **eucora-evidence-service** | Evidence pack generation, storage | Django 5.1, MinIO | Horizontal |
| **eucora-event-store** | Immutable audit trail | Django 5.1, PostgreSQL | Horizontal |
| **eucora-scheduler** | Job scheduling, cron tasks | Celery Beat | Single (HA standby) |

### 5.2 Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT REQUESTS                                  │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            eucora-api-gateway                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│  │  Auth   │  │  RBAC   │  │  Rate   │  │ Routing │  │ Logging │           │
│  │  Filter │  │  Check  │  │  Limit  │  │  Rules  │  │  Filter │           │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
└─────────────────────────────────────┬────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  Packaging    │           │  Deployment   │           │  CAB          │
│  Service      │           │  Service      │           │  Service      │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        │    ┌──────────────────────┼──────────────────────┐    │
        │    │                      │                      │    │
        ▼    ▼                      ▼                      ▼    ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  Policy       │◄─────────►│  Evidence     │◄─────────►│  Event        │
│  Engine       │           │  Service      │           │  Store        │
└───────────────┘           └───────────────┘           └───────────────┘
        │                           │                           │
        │    ┌──────────────────────┼──────────────────────┐    │
        │    │                      │                      │    │
        ▼    ▼                      ▼                      ▼    ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  Connector    │           │  Telemetry    │           │  AI Agent     │
│  Service      │           │  Service      │           │  Service      │
└───────┬───────┘           └───────────────┘           └───────────────┘
        │
        │    ┌──────────────────────┬──────────────────────┐
        │    │                      │                      │
        ▼    ▼                      ▼                      ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│   Intune      │           │    Jamf       │           │    SCCM       │
│   Connector   │           │   Connector   │           │   Connector   │
└───────────────┘           └───────────────┘           └───────────────┘
```

### 5.3 Service Contracts

#### 5.3.1 Deployment Service API

```yaml
openapi: 3.0.3
info:
  title: EUCORA Deployment Service API
  version: 2.0.0

paths:
  /api/deployments/intents/:
    post:
      summary: Create deployment intent
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/DeploymentIntent'
      responses:
        '201':
          description: Intent created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DeploymentIntentResponse'

  /api/deployments/intents/{id}/promote/:
    post:
      summary: Promote to next ring
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Promotion initiated
        '403':
          description: Promotion gates not met

components:
  schemas:
    DeploymentIntent:
      type: object
      required:
        - package_id
        - target_scope
        - rings
      properties:
        package_id:
          type: string
          format: uuid
        target_scope:
          type: object
          properties:
            regions:
              type: array
              items:
                type: string
            business_units:
              type: array
              items:
                type: string
            device_groups:
              type: array
              items:
                type: string
        rings:
          type: array
          items:
            $ref: '#/components/schemas/RingConfig'
        schedule:
          $ref: '#/components/schemas/Schedule'
        rollback_policy:
          $ref: '#/components/schemas/RollbackPolicy'

    RingConfig:
      type: object
      properties:
        ring_number:
          type: integer
          minimum: 0
          maximum: 4
        success_threshold:
          type: number
          minimum: 0
          maximum: 100
        time_to_compliance_hours:
          type: integer
        size_limit:
          type: integer
```

#### 5.3.2 License Service API

```yaml
paths:
  /api/licenses/summary/:
    get:
      summary: Get global license summary
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  total_entitled:
                    type: integer
                  total_consumed:
                    type: integer
                  total_remaining:
                    type: integer
                  last_reconciled_at:
                    type: string
                    format: date-time
                  health_status:
                    type: string
                    enum: [ok, degraded, failed, stale]

  /api/licenses/reconcile/run/:
    post:
      summary: Trigger reconciliation run
      responses:
        '202':
          description: Reconciliation started
          content:
            application/json:
              schema:
                type: object
                properties:
                  run_id:
                    type: string
                    format: uuid
                  status:
                    type: string
```

---

## 6. Data Architecture

### 6.1 Data Store Strategy

| Store | Technology | Purpose | Data Characteristics |
|-------|------------|---------|---------------------|
| **Relational Metadata** | PostgreSQL 15+ | Structured entities, relationships | ACID, normalized |
| **Object Storage** | MinIO (S3-compatible) | Artifacts, evidence packs, SBOMs | Immutable, versioned |
| **Time-Series Metrics** | Prometheus + Thanos | Device telemetry, performance | High-cardinality, retention |
| **Structured Logs** | Loki | Application logs, audit trail | Append-only, indexed |
| **Distributed Traces** | Tempo | Request tracing, debugging | Sampled, correlated |
| **Cache/Queue** | Redis | Session cache, task queue | Ephemeral, pub/sub |

### 6.2 Core Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DEPLOYMENT DOMAIN                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────┐       ┌────────────┐       ┌────────────┐                  │
│  │  Package   │1─────*│  Package   │1─────*│  Artifact  │                  │
│  │            │       │  Version   │       │            │                  │
│  └────────────┘       └─────┬──────┘       └────────────┘                  │
│                             │                                               │
│                             │1                                              │
│                             │                                               │
│                             ▼                                               │
│  ┌────────────┐       ┌────────────┐       ┌────────────┐                  │
│  │ Deployment │*─────1│ Deployment │1─────*│    Ring    │                  │
│  │   Event    │       │   Intent   │       │            │                  │
│  └────────────┘       └─────┬──────┘       └─────┬──────┘                  │
│                             │                    │                          │
│                             │1                   │1                         │
│                             │                    │                          │
│                             ▼                    ▼                          │
│                       ┌────────────┐       ┌────────────┐                  │
│                       │   CAB      │       │ Promotion  │                  │
│                       │  Approval  │       │   Gate     │                  │
│                       │  Request   │       │            │                  │
│                       └────────────┘       └────────────┘                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           LICENSE DOMAIN                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────┐       ┌────────────┐       ┌────────────┐                  │
│  │   Vendor   │1─────*│ License    │1─────*│Entitlement │                  │
│  │            │       │    SKU     │       │            │                  │
│  └────────────┘       └─────┬──────┘       └────────────┘                  │
│                             │                                               │
│                    ┌────────┼────────┐                                      │
│                    │        │        │                                      │
│                    ▼        ▼        ▼                                      │
│              ┌─────────┐ ┌──────┐ ┌────────┐                                │
│              │ License │ │Signal│ │Snapshot│                                │
│              │  Pool   │ │      │ │        │                                │
│              └────┬────┘ └──┬───┘ └────────┘                                │
│                   │         │                                               │
│                   ▼         │                                               │
│              ┌─────────┐    │                                               │
│              │Assignment│◄──┘                                               │
│              └─────────┘                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Data Classification & Retention

| Classification | Examples | Encryption | Retention | Erasure Support |
|----------------|----------|------------|-----------|-----------------|
| **P0 Sensitive** | User identifiers, device names | At rest + in transit | Policy-driven | GDPR/DPDP compliant |
| **P1 Operational** | Telemetry, incident metadata | At rest + in transit | 90-365 days | Supported |
| **P2 Derived** | Feature vectors, embeddings | At rest | 730 days | Supported |
| **P3 Non-Sensitive** | Model metadata, metrics | In transit | 730 days | N/A |
| **P4 Audit** | Audit logs, evidence packs | At rest + in transit | 730 days min | Immutable |

### 6.4 Data Residency Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CUSTOMER DATA BOUNDARY                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        DATA LAYER (Self-Hosted)                       │  │
│  │                                                                       │  │
│  │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │  │
│  │   │  PostgreSQL   │    │    MinIO      │    │    Redis      │       │  │
│  │   │               │    │               │    │               │       │  │
│  │   │ • Metadata    │    │ • Artifacts   │    │ • Cache       │       │  │
│  │   │ • Audit logs  │    │ • Evidence    │    │ • Sessions    │       │  │
│  │   │ • Config      │    │ • SBOMs       │    │ • Task queue  │       │  │
│  │   └───────────────┘    └───────────────┘    └───────────────┘       │  │
│  │                                                                       │  │
│  │   ┌───────────────┐    ┌───────────────┐    ┌───────────────┐       │  │
│  │   │  Prometheus   │    │     Loki      │    │    Tempo      │       │  │
│  │   │               │    │               │    │               │       │  │
│  │   │ • Metrics     │    │ • Logs        │    │ • Traces      │       │  │
│  │   │ • Telemetry   │    │ • Audit       │    │ • Spans       │       │  │
│  │   └───────────────┘    └───────────────┘    └───────────────┘       │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    NO EXTERNAL EGRESS BY DEFAULT                      │  │
│  │                                                                       │  │
│  │   • All data remains within customer boundary                        │  │
│  │   • No cloud telemetry aggregation                                   │  │
│  │   • External API calls require explicit opt-in                       │  │
│  │   • AI/ML training data stays local                                  │  │
│  │                                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Integration Architecture

### 7.1 Connector Framework

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CONNECTOR FRAMEWORK                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      BaseConnector (Abstract)                         │  │
│  │                                                                       │  │
│  │  + test_connection() → bool                                          │  │
│  │  + sync_inventory() → SyncResult                                     │  │
│  │  + push_intent(intent) → SyncResult                                  │  │
│  │  + get_compliance_status(scope) → ComplianceReport                   │  │
│  │  + rollback(deployment_id) → SyncResult                              │  │
│  │  + get_idempotency_key(operation, params) → str                      │  │
│  │                                                                       │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│         ┌───────────────────────────┼───────────────────────────┐          │
│         │                           │                           │          │
│         ▼                           ▼                           ▼          │
│  ┌─────────────┐            ┌─────────────┐            ┌─────────────┐     │
│  │   Intune    │            │    Jamf     │            │    SCCM     │     │
│  │  Connector  │            │  Connector  │            │  Connector  │     │
│  │             │            │             │            │             │     │
│  │ Graph API   │            │ Jamf Pro API│            │ WMI/REST    │     │
│  └─────────────┘            └─────────────┘            └─────────────┘     │
│                                                                              │
│  ┌─────────────┐            ┌─────────────┐            ┌─────────────┐     │
│  │  Landscape  │            │   Ansible   │            │  AD/Entra   │     │
│  │  Connector  │            │  Connector  │            │  Connector  │     │
│  │             │            │             │            │             │     │
│  │Landscape API│            │  AWX API    │            │ Graph/SCIM  │     │
│  └─────────────┘            └─────────────┘            └─────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Connector Capabilities Matrix

| Connector | Sync Inventory | Push Deployment | Compliance Query | Rollback | Telemetry Pull |
|-----------|---------------|-----------------|------------------|----------|----------------|
| **Intune** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Jamf** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **SCCM** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Landscape** | ✓ | ✓ | ✓ | ✓ | Partial |
| **Ansible** | ✓ | ✓ | ✓ | ✓ | Via callback |
| **AD/Entra** | ✓ | N/A | N/A | N/A | N/A |
| **ServiceNow** | ✓ | ✓ | N/A | N/A | N/A |

### 7.3 Integration Patterns

#### 7.3.1 Idempotent Operations

All connector write operations use idempotent keys:

```python
class IdempotencyKeyGenerator:
    """Generates deterministic idempotency keys for connector operations."""

    @staticmethod
    def generate(connector_type: str, operation: str, params: dict) -> str:
        """
        Generate idempotency key from operation parameters.

        Key format: {connector}:{operation}:{hash(sorted_params)}
        Example: intune:deploy_app:abc123def456

        This ensures:
        - Retries don't create duplicates
        - Concurrent requests are safely handled
        - Operations can be traced to source
        """
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.sha256(sorted_params.encode()).hexdigest()[:12]
        return f"{connector_type}:{operation}:{param_hash}"
```

#### 7.3.2 Circuit Breaker Pattern

```python
class ConnectorCircuitBreaker:
    """Circuit breaker for connector resilience."""

    STATES = ['CLOSED', 'OPEN', 'HALF_OPEN']

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        self.state = 'CLOSED'
        self.failure_count = 0
        self.last_failure_time = None

    def can_execute(self) -> bool:
        """Check if request can proceed."""
        if self.state == 'CLOSED':
            return True
        if self.state == 'OPEN':
            if self._recovery_timeout_elapsed():
                self.state = 'HALF_OPEN'
                return True
            return False
        if self.state == 'HALF_OPEN':
            return True
        return False

    def record_success(self) -> None:
        """Record successful operation."""
        self.failure_count = 0
        self.state = 'CLOSED'

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

### 7.4 Reconciliation Loop Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RECONCILIATION LOOP                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. FETCH DESIRED STATE                                               │    │
│  │    • Query DeploymentIntent table                                    │    │
│  │    • Get expected app assignments per scope                          │    │
│  │    • Get expected version per ring                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 2. FETCH ACTUAL STATE                                                │    │
│  │    • Query execution plane via connector                             │    │
│  │    • Get current app assignments                                     │    │
│  │    • Get installed versions per device                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 3. COMPUTE DRIFT                                                     │    │
│  │    • Compare desired vs actual                                       │    │
│  │    • Classify drift: MISSING, EXTRA, MODIFIED                        │    │
│  │    • Generate DriftEvent records                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 4. TRIGGER REMEDIATION (if policy allows)                            │    │
│  │    • Auto-remediate MISSING (add assignment)                         │    │
│  │    • Flag EXTRA for review (potential security issue)                │    │
│  │    • Queue MODIFIED for re-deployment                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                     │                                        │
│                                     ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 5. EMIT EVENTS & METRICS                                             │    │
│  │    • Record drift events in Event Store                              │    │
│  │    • Update Prometheus metrics                                       │    │
│  │    • Send alerts if threshold exceeded                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Schedule: Every 15 minutes (configurable per connector)                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Security Architecture

### 8.1 Security Principles

| Principle | Implementation |
|-----------|----------------|
| **Zero Trust** | No implicit trust; verify every request |
| **Defense in Depth** | Multiple security layers |
| **Least Privilege** | Minimum necessary permissions |
| **Separation of Duties** | Distinct roles with non-overlapping privileges |
| **Audit Everything** | Complete audit trail for all actions |

### 8.2 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION FLOW                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐                                    ┌─────────────┐         │
│  │    User     │──────────────────────────────────►│   Identity  │         │
│  │   Browser   │◄──────────────────────────────────│   Provider  │         │
│  └──────┬──────┘   OIDC Flow (Auth Code + PKCE)    │ (Entra ID)  │         │
│         │                                           └─────────────┘         │
│         │ JWT Token                                                          │
│         ▼                                                                    │
│  ┌─────────────┐       ┌─────────────┐       ┌─────────────┐               │
│  │    API      │──────►│   Token     │──────►│    RBAC     │               │
│  │   Gateway   │       │ Validation  │       │   Engine    │               │
│  └─────────────┘       └─────────────┘       └──────┬──────┘               │
│                                                      │                       │
│                                                      ▼                       │
│                                               ┌─────────────┐               │
│                                               │ Permission  │               │
│                                               │   Check     │               │
│                                               └─────────────┘               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.3 RBAC Model

| Role | Permissions | Scope |
|------|-------------|-------|
| **platform_admin** | `*` | Global |
| **packaging_engineer** | `package.create`, `package.read`, `package.test` | Staging |
| **publisher** | `deployment.create`, `deployment.read`, `package.publish` | Scoped BU |
| **cab_approver** | `approval.approve`, `approval.reject`, `evidence.read` | Approval queue |
| **security_reviewer** | `policy.write`, `exception.approve`, `sbom.read` | Security domain |
| **license_admin** | `license.*` | License module |
| **endpoint_ops** | `telemetry.read`, `remediation.trigger` | Device scope |
| **auditor** | `*.read` | Audit trail |

### 8.4 Service-to-Service Security

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      mTLS SERVICE MESH                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐           mTLS           ┌─────────────┐                  │
│  │  Service A  │◄────────────────────────►│  Service B  │                  │
│  │             │                           │             │                  │
│  │  Client     │                           │  Server     │                  │
│  │  Cert       │                           │  Cert       │                  │
│  └─────────────┘                           └─────────────┘                  │
│                                                                              │
│  Certificate Authority: Internal PKI or Vault                               │
│  Rotation: Automatic (30-day lifecycle)                                     │
│  Verification: Mutual TLS required for all internal traffic                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.5 Secrets Management

| Secret Type | Storage | Rotation | Access |
|-------------|---------|----------|--------|
| Database credentials | Vault / K8s Secrets | 90 days | Service accounts only |
| API keys (connectors) | Vault (encrypted) | Per policy | Connector service |
| JWT signing keys | Vault | 30 days | API Gateway |
| Encryption keys | Vault | 365 days | Encryption service |
| Service certificates | Vault PKI | 30 days | Automatic |

### 8.6 Security Controls Matrix

| Control | Layer | Implementation |
|---------|-------|----------------|
| **Authentication** | Gateway | OIDC/OAuth2 with MFA |
| **Authorization** | Application | RBAC + ABAC |
| **Encryption (transit)** | Network | TLS 1.3, mTLS |
| **Encryption (rest)** | Storage | AES-256 |
| **Input Validation** | Application | Schema validation, sanitization |
| **Rate Limiting** | Gateway | Token bucket algorithm |
| **Audit Logging** | Application | Immutable append-only |
| **Vulnerability Scanning** | CI/CD | Trivy, Grype |
| **SBOM Generation** | CI/CD | SPDX format |
| **Secret Detection** | Pre-commit | detect-secrets |

---

## 9. Infrastructure Architecture

### 9.1 Deployment Topology Options

#### 9.1.1 Production (Kubernetes)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      KUBERNETES CLUSTER (Production)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        INGRESS LAYER                                 │    │
│  │   ┌────────────┐    ┌────────────┐    ┌────────────┐               │    │
│  │   │  Ingress   │    │    WAF     │    │   Cert     │               │    │
│  │   │ Controller │    │   Rules    │    │  Manager   │               │    │
│  │   └────────────┘    └────────────┘    └────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        APPLICATION LAYER                             │    │
│  │                                                                      │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│    │
│  │   │ api-gw   │ │ portal   │ │packaging │ │deployment│ │   cab    ││    │
│  │   │ (3 pods) │ │ (3 pods) │ │ (3 pods) │ │ (3 pods) │ │ (2 pods) ││    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│    │
│  │                                                                      │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│    │
│  │   │ license  │ │portfolio │ │telemetry │ │ ai-agent │ │connector ││    │
│  │   │ (2 pods) │ │ (2 pods) │ │ (3 pods) │ │ (2 pods) │ │ (3 pods) ││    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘│    │
│  │                                                                      │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐                           │    │
│  │   │  user    │ │evidence  │ │  event   │                           │    │
│  │   │ (2 pods) │ │ (2 pods) │ │ (2 pods) │                           │    │
│  │   └──────────┘ └──────────┘ └──────────┘                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        WORKER LAYER                                  │    │
│  │   ┌──────────────────┐    ┌──────────────────┐                      │    │
│  │   │  Celery Workers  │    │   Celery Beat    │                      │    │
│  │   │    (5 pods)      │    │    (1 pod HA)    │                      │    │
│  │   └──────────────────┘    └──────────────────┘                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        DATA LAYER (StatefulSets)                     │    │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐                   │    │
│  │   │ PostgreSQL │  │   MinIO    │  │   Redis    │                   │    │
│  │   │  Primary   │  │  (4 nodes) │  │  Cluster   │                   │    │
│  │   │ + Standby  │  │            │  │  (3 nodes) │                   │    │
│  │   └────────────┘  └────────────┘  └────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        OBSERVABILITY LAYER                           │    │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │    │
│  │   │ Prometheus │  │    Loki    │  │   Tempo    │  │  Grafana   │  │    │
│  │   │  + Thanos  │  │            │  │            │  │            │  │    │
│  │   └────────────┘  └────────────┘  └────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 9.1.2 Resource Requirements (Production)

| Component | CPU (cores) | Memory (GB) | Storage | Replicas |
|-----------|-------------|-------------|---------|----------|
| API Gateway | 2 | 4 | - | 3 |
| Portal UI | 1 | 2 | - | 3 |
| Application Services | 2 | 4 | - | 2-3 each |
| Celery Workers | 2 | 4 | - | 5 |
| PostgreSQL | 4 | 16 | 500GB SSD | 2 (HA) |
| MinIO | 2 | 8 | 2TB per node | 4 |
| Redis | 2 | 8 | 50GB | 3 |
| Prometheus | 2 | 16 | 500GB | 2 |
| Loki | 2 | 8 | 1TB | 3 |

**Total Minimum**: 40 cores, 120GB RAM, 8TB storage

### 9.2 High Availability Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      HIGH AVAILABILITY DESIGN                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        LOAD BALANCER (L7)                             │  │
│  │                                                                       │  │
│  │   Active health checks, sticky sessions, SSL termination             │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  │                                          │
│         ┌────────────────────────┼────────────────────────┐                │
│         │                        │                        │                │
│         ▼                        ▼                        ▼                │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │   Node 1    │          │   Node 2    │          │   Node 3    │        │
│  │             │          │             │          │             │        │
│  │  Services   │          │  Services   │          │  Services   │        │
│  │  Workers    │          │  Workers    │          │  Workers    │        │
│  └─────────────┘          └─────────────┘          └─────────────┘        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        DATABASE HA                                    │  │
│  │                                                                       │  │
│  │   ┌─────────────┐          ┌─────────────┐                           │  │
│  │   │ PostgreSQL  │ Streaming│ PostgreSQL  │                           │  │
│  │   │   Primary   │─────────►│   Standby   │                           │  │
│  │   │             │  Repl    │             │                           │  │
│  │   └─────────────┘          └─────────────┘                           │  │
│  │                                                                       │  │
│  │   Failover: Automatic via Patroni/pg_auto_failover                   │  │
│  │   RPO: 0 (synchronous replication)                                   │  │
│  │   RTO: < 30 seconds                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        OBJECT STORAGE HA                              │  │
│  │                                                                       │  │
│  │   MinIO Erasure Coding (4 nodes, 2 parity)                           │  │
│  │   Can tolerate 2 node failures                                       │  │
│  │   Cross-site replication available                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 Disaster Recovery

| Metric | Target | Implementation |
|--------|--------|----------------|
| **RPO** | ≤ 24 hours | PostgreSQL PITR, MinIO versioning |
| **RTO** | ≤ 8 hours | Automated failover, documented runbooks |
| **Backup Frequency** | Daily full, hourly incremental | Automated backup jobs |
| **Backup Retention** | 30 days | Configurable per compliance |
| **Recovery Testing** | Quarterly | Documented DR drills |

---

## 10. AI/ML Architecture

### 10.1 AI Governance Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AI GOVERNANCE FRAMEWORK                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        RISK CLASSIFICATION                            │  │
│  │                                                                       │  │
│  │   ┌──────────┐     ┌──────────┐     ┌──────────┐                    │  │
│  │   │    R1    │     │    R2    │     │    R3    │                    │  │
│  │   │   LOW    │     │  MEDIUM  │     │   HIGH   │                    │  │
│  │   │          │     │          │     │          │                    │  │
│  │   │ Auto-    │     │ Policy-  │     │ Mandatory│                    │  │
│  │   │ execute  │     │ dependent│     │ Approval │                    │  │
│  │   │ allowed  │     │ approval │     │ Required │                    │  │
│  │   └──────────┘     └──────────┘     └──────────┘                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        AGENT GUARDRAILS                               │  │
│  │                                                                       │  │
│  │   • All agents execute through guardrail framework                   │  │
│  │   • Allowed/forbidden actions defined per agent type                 │  │
│  │   • Maximum scope size enforced                                      │  │
│  │   • Timeout limits per operation                                     │  │
│  │   • Complete audit trail mandatory                                   │  │
│  │   • Evidence pack required for recommendations                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Model Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODEL LIFECYCLE                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐     │
│    │  Data  │───►│Training│───►│Validate│───►│ Deploy │───►│Monitor │     │
│    │Collect │    │        │    │        │    │        │    │        │     │
│    └────────┘    └────────┘    └────────┘    └────────┘    └────┬───┘     │
│                                                                   │         │
│                                                                   │         │
│    ┌──────────────────────────────────────────────────────────────┘         │
│    │                                                                         │
│    ▼                                                                         │
│    ┌────────┐    ┌────────┐                                                 │
│    │ Drift  │───►│Retrain │                                                 │
│    │Detected│    │   or   │                                                 │
│    │        │    │Rollback│                                                 │
│    └────────┘    └────────┘                                                 │
│                                                                              │
│  Model Registry tracks:                                                     │
│  • model_id, version, dataset_version                                       │
│  • training_params, validation_report                                       │
│  • risk_level, approver, deployment_date                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 AI Agent Catalog

| Agent | Purpose | Risk Level | Approval Required |
|-------|---------|------------|-------------------|
| **Incident Classifier** | Categorize incidents with confidence | R1 | No |
| **Remediation Advisor** | Recommend scripts/actions | R2 | Policy-based |
| **Risk Assessor** | Compute deployment risk scores | R1 | No |
| **License Inventory Extractor** | Extract entitlements from contracts | R2 | Yes |
| **Consumption Discovery** | Identify consumption from telemetry | R1 | No |
| **Optimization Advisor** | Recommend license optimization | R2 | Yes |
| **Anomaly Detector** | Detect license/compliance anomalies | R1 | No |
| **Dependency Inference** | Infer application dependencies | R1 | No |

### 10.4 Human-in-Loop Enforcement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      APPROVAL WORKFLOW                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────┐                                                           │
│   │ AI Agent    │                                                           │
│   │ Execution   │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────┐     R1 (Low)      ┌─────────────┐                        │
│   │   Risk      │────────────────────►│  Execute   │                        │
│   │   Check     │                     │  Directly  │                        │
│   └──────┬──────┘                     └─────────────┘                        │
│          │                                                                   │
│          │ R2/R3 (Medium/High)                                              │
│          ▼                                                                   │
│   ┌─────────────┐                                                           │
│   │  Generate   │                                                           │
│   │  Evidence   │                                                           │
│   │   Pack      │                                                           │
│   └──────┬──────┘                                                           │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────┐                     ┌─────────────┐                        │
│   │  Submit to  │────────────────────►│   Approver  │                        │
│   │  Approval   │                     │   Reviews   │                        │
│   │   Queue     │◄────────────────────│             │                        │
│   └──────┬──────┘    Approve/Reject   └─────────────┘                        │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────┐                     ┌─────────────┐                        │
│   │  Execute    │                     │   Log &     │                        │
│   │  (if        │────────────────────►│   Audit     │                        │
│   │  approved)  │                     │             │                        │
│   └─────────────┘                     └─────────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Observability Architecture

### 11.1 Observability Stack

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OBSERVABILITY ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        DATA COLLECTION                                │  │
│  │                                                                       │  │
│  │   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │  │
│  │   │   Metrics   │    │    Logs     │    │   Traces    │             │  │
│  │   │ (StatsD/    │    │ (Structured │    │ (OTLP/      │             │  │
│  │   │  Prometheus)│    │  JSON)      │    │  Jaeger)    │             │  │
│  │   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │  │
│  │          │                  │                  │                     │  │
│  └──────────┼──────────────────┼──────────────────┼─────────────────────┘  │
│             │                  │                  │                        │
│             ▼                  ▼                  ▼                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        OTEL COLLECTOR                                 │  │
│  │   Processing, batching, export to backends                           │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  │                                          │
│         ┌────────────────────────┼────────────────────────┐                │
│         │                        │                        │                │
│         ▼                        ▼                        ▼                │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐        │
│  │ Prometheus  │          │    Loki     │          │   Tempo     │        │
│  │  + Thanos   │          │             │          │             │        │
│  │             │          │             │          │             │        │
│  │  Metrics    │          │    Logs     │          │   Traces    │        │
│  │  15d local  │          │   90d       │          │   30d       │        │
│  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘        │
│         │                        │                        │                │
│         └────────────────────────┼────────────────────────┘                │
│                                  │                                          │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          GRAFANA                                      │  │
│  │                                                                       │  │
│  │   Dashboards │ Alerts │ Explore │ Correlations                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Key Metrics & SLIs

| Category | Metric | Target |
|----------|--------|--------|
| **Availability** | Platform uptime (30d rolling) | ≥ 99.5% |
| **Latency** | API response time (p95) | ≤ 500ms |
| **Latency** | API response time (p99) | ≤ 1000ms |
| **Error Rate** | HTTP 5xx rate | ≤ 0.1% |
| **Deployment** | Success rate | ≥ 98% |
| **Agent Coverage** | Active agents / total devices | ≥ 97% |
| **Telemetry Freshness** | Max staleness | ≤ 5 minutes |
| **License Reconciliation** | Freshness | ≤ 1 hour |
| **AI Classification** | Accuracy | ≥ 85% |
| **Model Override Rate** | Rejection rate | ≤ 40% |

### 11.3 Alerting Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **HighErrorRate** | 5xx > 1% for 5m | Critical | Page on-call |
| **HighLatency** | p95 > 1s for 10m | Warning | Notify Slack |
| **DeploymentFailures** | Failure rate > 5% | Warning | Notify team |
| **AgentHeartbeatMissing** | No heartbeat > 15m | Warning | Auto-remediate |
| **DatabaseHighLoad** | CPU > 80% for 10m | Warning | Scale review |
| **DiskSpaceLow** | < 20% free | Critical | Immediate action |
| **CertificateExpiry** | < 7 days | Warning | Rotation required |
| **LicenseOverconsumption** | Consumed > Entitled | Critical | Alert License Admin |

---

## 12. Deployment Architecture

### 12.1 Ring-Based Rollout Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      RING-BASED DEPLOYMENT                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐      │
│  │ Ring 0  │──►│ Ring 1  │──►│ Ring 2  │──►│ Ring 3  │──►│ Ring 4  │      │
│  │  Lab    │   │ Canary  │   │ Pilot   │   │  Dept   │   │ Global  │      │
│  │         │   │         │   │         │   │         │   │         │      │
│  │ ~10     │   │ ~100    │   │ ~1000   │   │ ~10000  │   │ ~100000 │      │
│  │ devices │   │ devices │   │ devices │   │ devices │   │ devices │      │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘      │
│       │             │             │             │             │             │
│       │             │             │             │             │             │
│       ▼             ▼             ▼             ▼             ▼             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      PROMOTION GATES                                 │   │
│  │                                                                      │   │
│  │  Ring 0 → 1: Automated tests pass                                   │   │
│  │  Ring 1 → 2: Success ≥ 98%, Time-to-compliance ≤ 24h               │   │
│  │  Ring 2 → 3: Success ≥ 97%, No security incidents                  │   │
│  │  Ring 3 → 4: Success ≥ 99%, CAB approval (if Risk > 50)            │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ROLLBACK TRIGGERS                               │   │
│  │                                                                      │   │
│  │  • Success rate < threshold                                         │   │
│  │  • Security incident detected                                       │   │
│  │  • Manual halt by CAB                                               │   │
│  │  • Time-to-compliance exceeded                                      │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.2 Site Classification

| Class | Connectivity | Distribution Strategy |
|-------|-------------|----------------------|
| **Online** | Stable cloud access | Direct MDM delivery, Delivery Optimization |
| **Intermittent** | Limited/periodic connectivity | Local caching, batch sync |
| **Air-Gapped** | No cloud access | Controlled transfer, hash verification |

### 12.3 Platform-Specific Packaging

| Platform | Primary Format | Secondary | Distribution Channel |
|----------|---------------|-----------|---------------------|
| **Windows** | MSIX / IntuneWin | MSI/EXE | Intune / SCCM DP |
| **macOS** | Signed PKG | DMG | Intune / Jamf |
| **Linux** | APT/DEB | RPM | Landscape / Ansible |
| **iOS** | App Store / LOB | VPP | Intune (ABM) |
| **Android** | Managed Play | APK | Intune (Android Enterprise) |

---

## 13. Non-Functional Requirements

### 13.1 Performance Requirements

| Requirement | Specification | Validation Method |
|-------------|---------------|-------------------|
| **API Latency (p95)** | ≤ 500ms | Load testing |
| **API Latency (p99)** | ≤ 1000ms | Load testing |
| **Concurrent Users** | 500 simultaneous | Load testing |
| **Telemetry Ingestion** | 10,000 events/second | Stress testing |
| **Database Query Time** | ≤ 100ms (95th percentile) | Query profiling |
| **Report Generation** | ≤ 30 seconds | Functional testing |

### 13.2 Scalability Requirements

| Dimension | Current | Target | Growth Strategy |
|-----------|---------|--------|-----------------|
| **Devices** | 10,000 | 100,000 | Horizontal scaling |
| **Users** | 1,000 | 10,000 | Session management |
| **Packages** | 100 | 10,000 | Object storage scaling |
| **Daily Deployments** | 100 | 10,000 | Queue scaling |
| **Telemetry Data** | 10GB/day | 1TB/day | Time-series partitioning |

### 13.3 Reliability Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **Availability** | 99.5% | HA deployment, auto-failover |
| **MTTR** | ≤ 4 hours (manual) | Runbooks, on-call |
| **MTTR** | ≤ 2 hours (AI-assisted) | Automated remediation |
| **Data Durability** | 99.999999999% | MinIO erasure coding |
| **Backup RPO** | ≤ 24 hours | Daily backups |
| **Backup RTO** | ≤ 8 hours | Documented restore |

### 13.4 Security Requirements

| Requirement | Specification | Compliance |
|-------------|---------------|------------|
| **Authentication** | OIDC/OAuth2 with MFA | SOC2, ISO 27001 |
| **Authorization** | RBAC with least privilege | SOC2 |
| **Encryption (transit)** | TLS 1.3 | NIST, FIPS |
| **Encryption (rest)** | AES-256 | NIST, FIPS |
| **Audit Logging** | Immutable, 730-day retention | GDPR, SOC2 |
| **Vulnerability Scanning** | Zero critical/high in production | SOC2 |
| **Secret Management** | Vault/K8s Secrets, rotation | SOC2 |

### 13.5 Compliance Requirements

| Framework | Scope | Implementation |
|-----------|-------|----------------|
| **GDPR** | Data residency, erasure, consent | Self-hosted, erasure API |
| **India DPDP** | Data processing, minimization | Local storage, PII masking |
| **SOC2 Type II** | Security, availability, confidentiality | Controls documented |
| **ISO 27001** | ISMS controls | Policy alignment |
| **NIST 800-53** | Zero trust, audit | Control mapping |

---

## 14. Technology Stack

### 14.1 Backend Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Language** | Python | 3.11+ | Application code |
| **Framework** | Django | 5.1.x | Web framework |
| **API** | Django REST Framework | 3.15.x | REST API |
| **Task Queue** | Celery | 5.4.x | Async tasks |
| **Scheduler** | django-celery-beat | 2.8.x | Periodic tasks |
| **Database** | PostgreSQL | 15+ | Relational data |
| **Cache/Queue** | Redis | 7.x | Caching, message broker |
| **Object Storage** | MinIO | Latest | S3-compatible storage |

### 14.2 Frontend Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Language** | TypeScript | 5.x | Type-safe JavaScript |
| **Framework** | React | 18.x | UI framework |
| **Build Tool** | Vite | 5.x | Fast builds |
| **State Management** | Zustand | 4.x | Global state |
| **Data Fetching** | TanStack Query | 5.x | Server state |
| **Forms** | React Hook Form | 7.x | Form handling |
| **Styling** | Tailwind CSS | 3.x | Utility-first CSS |
| **Components** | Radix UI | Latest | Accessible primitives |

### 14.3 Infrastructure Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Container Runtime** | Docker | Containerization |
| **Orchestration** | Kubernetes | Container orchestration |
| **Service Mesh** | Istio/Linkerd (optional) | mTLS, traffic management |
| **Ingress** | Nginx/Kong | API gateway |
| **Secrets** | HashiCorp Vault / K8s Secrets | Secret management |
| **CI/CD** | GitHub Actions / GitLab CI | Automation |

### 14.4 Observability Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Metrics** | Prometheus + Thanos | Metrics collection & storage |
| **Logs** | Loki | Log aggregation |
| **Traces** | Tempo | Distributed tracing |
| **Visualization** | Grafana | Dashboards & alerting |
| **Instrumentation** | OpenTelemetry | Unified telemetry |

---

## 15. Architecture Decision Records

### ADR-001: Thin Control Plane Architecture

**Status**: Accepted

**Context**: EUCORA needs to orchestrate deployments across multiple execution planes (Intune, Jamf, SCCM, etc.) without replacing their native capabilities.

**Decision**: Implement a thin control plane that handles policy, orchestration, and evidence while delegating device management primitives to execution planes.

**Consequences**:
- (+) Leverages existing MDM investments
- (+) Avoids device management complexity
- (+) Clear separation of concerns
- (-) Dependent on execution plane availability
- (-) Feature set limited by connector capabilities

---

### ADR-002: Evidence-First Governance

**Status**: Accepted

**Context**: Enterprise change control requires defensible audit trails for all deployment decisions.

**Decision**: All deployments must include complete evidence packs with artifact hashes, SBOM, scan results, test evidence, and approval records.

**Consequences**:
- (+) Audit-ready from day one
- (+) Supports regulatory compliance
- (+) Enables deterministic risk assessment
- (-) Increased storage requirements
- (-) Additional processing overhead

---

### ADR-003: Human-in-Loop for High-Risk AI Actions

**Status**: Accepted

**Context**: AI-assisted remediation must not introduce uncontrolled automation risks.

**Decision**: Classify AI actions by risk level (R1/R2/R3). R2 actions require policy-based approval. R3 actions require mandatory human approval.

**Consequences**:
- (+) Safety by design
- (+) Maintains human accountability
- (+) Enables gradual automation trust
- (-) Slower execution for high-risk actions
- (-) Requires approval workflow infrastructure

---

### ADR-004: Self-Hosted Data Residency

**Status**: Accepted

**Context**: Enterprise customers require data sovereignty and control over sensitive endpoint telemetry.

**Decision**: All data storage (PostgreSQL, MinIO, Prometheus, Loki) deployed within customer boundary. No cloud egress by default.

**Consequences**:
- (+) Full data sovereignty
- (+) Supports air-gapped deployments
- (+) No external dependencies
- (-) Customer responsible for infrastructure
- (-) No shared analytics across deployments

---

### ADR-005: Ring-Based Deployment Model

**Status**: Accepted

**Context**: Enterprise deployments require controlled rollout with measurable promotion gates.

**Decision**: Implement 5-ring deployment model (Lab → Canary → Pilot → Department → Global) with configurable promotion gates.

**Consequences**:
- (+) Risk mitigation through phased rollout
- (+) Measurable success criteria
- (+) Automatic rollback on failure
- (-) Longer deployment timelines
- (-) Complex state management

---

## 16. Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **CAB** | Change Advisory Board — approval authority for high-risk changes |
| **Control Plane** | EUCORA orchestration layer (policy, evidence, coordination) |
| **Execution Plane** | MDM/endpoint management tools (Intune, Jamf, SCCM, etc.) |
| **Evidence Pack** | Complete audit bundle for a deployment decision |
| **Ring** | Deployment phase with specific scope and success criteria |
| **Reconciliation** | Process of comparing desired state vs actual state |
| **Drift** | Deviation between desired and actual state |
| **SBOM** | Software Bill of Materials — component inventory |

### Appendix B: Reference Documents

| Document | Location |
|----------|----------|
| Product Requirements Document | `docs/customer-requirements/Product Requirements Document (PRD).md` |
| Technical Architecture Specification | `docs/customer-requirements/TECHNICAL ARCHITECTURE SPECIFICATION.md` |
| License Management Requirements | `docs/customer-requirements/License-management.md` |
| AI Governance Blueprint | `docs/customer-requirements/AI Governance & Compliance Blueprint.md` |
| Data & Telemetry Architecture | `docs/customer-requirements/Data & Telemetry Architecture.md` |
| Platform Operating Model | `docs/customer-requirements/Platform Operating Model (Runbook, AIOps, SRE).md` |

### Appendix C: API Specification

Complete OpenAPI specifications available at:
- `/api/docs/` — Swagger UI
- `/api/schema/` — OpenAPI 3.0 schema

### Appendix D: Compliance Mapping

| Requirement | GDPR | SOC2 | ISO 27001 | NIST 800-53 |
|-------------|------|------|-----------|-------------|
| Audit Logging | Art. 30 | CC7.2 | A.12.4 | AU-2, AU-3 |
| Access Control | Art. 32 | CC6.1 | A.9.2 | AC-2, AC-3 |
| Encryption | Art. 32 | CC6.7 | A.10.1 | SC-8, SC-28 |
| Data Retention | Art. 17 | CC7.4 | A.8.3 | SI-12 |
| Incident Response | Art. 33 | CC7.3 | A.16.1 | IR-4, IR-6 |

---

**Document End**

*This Architecture Specification is a controlled document. Changes require Architecture Review Board approval.*
