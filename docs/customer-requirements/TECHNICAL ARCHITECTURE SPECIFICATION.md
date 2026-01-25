# EUCORA — Technical Architecture Specification (Production)

## 1. Objective & Scope
EUCORA is a self-hosted enterprise application for automated packaging, deployment, telemetry, and governance of EUC applications with AI-augmented remediation workflows.

This document defines the production architecture including deployment topology, data flows, security boundaries, integrations, and runtime services.

---

## 2. Architectural Principles
- Single-tenant deployment model (per customer instance)
- Zero-trust security alignment
- API-first design for all capabilities
- Human-in-loop change control enforcement
- Observability, auditability, and provenance by default
- Global regulatory alignment (GDPR, DPDP, SOC2, FedRAMP mappings)
- Remote-first (no LAN/VPN dependency)

---

## 3. High-Level Architecture Overview

**Primary Components**
1. **Core Orchestrator**
2. **Agent Runtime (Windows, macOS, Linux)**
3. **Packaging & App Store Service**
4. **Telemetry & Insights Engine**
5. **AI Reasoning & Recommender Service**
6. **Audit & Compliance Module**
7. **Identity & Access Layer**
8. **Admin & Self-Service Portal**
9. **Integration Connectors**
10. **Storage & Data Layer**

**External Dependencies**
- Identity Providers: Azure AD / AD / Okta
- ITSM: ServiceNow / Remedy / Jira
- EUC Tooling: SCCM, Intune, JAMF (optional)
- Object Storage: MinIO (S3 API)
- Observability Stack: Prometheus, Loki, Tempo, Grafana

---

## 4. Deployment Topology

**Supported Topologies**
- On-Prem Single VM (all-in-one)
- On-Prem Multi-Node (production)
- Kubernetes Self-Hosted (production preferred)

**Core Pods/Services (K8s)**
- `eucora-api-gateway`
- `orchestrator-service`
- `packaging-service`
- `deployment-service`
- `telemetry-service`
- `ai-service`
- `audit-service`
- `identity-service`
- `portal-ui`
- `connector-service`
- `observer-service`
- `scheduler-service`

**Stateful Services**
- `postgres`
- `minio`
- `redis`
- `otel-collector`
- `prometheus`
- `loki`
- `grafana`

---

## 5. Data Architecture

**5.1 Stores**
| Category | Backend |
|---|---|
| Relational metadata | PostgreSQL |
| Object artifacts | MinIO (S3 API) |
| Caching & Queues | Redis |
| Metrics | Prometheus |
| Logs | Loki |
| Traces | Tempo |

**5.2 Data Types**
- Device telemetry
- Software inventories
- Packaging manifests
- Deployment jobs & status
- AI inference context
- Audit records
- User actions
- Evidence bundle artifacts

**5.3 Regulatory Residency**
- Customer controls physical residency via MinIO + PostgreSQL
- No cross-tenant aggregation
- No cloud egress by default

---

## 6. Identity & Access

**Identity Models**
- Service-to-service (mTLS)
- User-to-service (OIDC/OAuth2)
- Device-to-service (mutual auth via Agent keys)

**Access Controls**
- RBAC core model
- ABAC optional extension (device posture, department, risk level)
- SCIM integration optional

**Supported Providers**
- Azure AD (OIDC)
- AD DS (LDAP + SSO bridge)
- Okta (OIDC)

---

## 7. Agent Architecture

**Supported OS Targets**
- Windows 10/11
- macOS 13+
- Linux (Ubuntu/RHEL)

**Agent Capabilities**
- Packaging
- Deployment
- Telemetry ingestion
- Remediation scripts
- Offline queueing
- Delta update support
- Evidence capture

**Agent → Platform Communication**
- HTTPS/2 + mTLS
- MQTT optional for async events
- Offline-first with replays

---

## 8. AI Architecture (Internal)

**Components**
- `classifier-model` (incident/device classification)
- `policy-engine` (automation rules + approvals)
- `recommender-model` (script/KB suggestions)
- `drift-detector` (model performance monitoring)

**Data Flow**
1. Telemetry/incident ingested
2. Pre-processing & feature extraction
3. AI inference (recommendations)
4. Policy evaluation
5. Evidence bundle generation
6. Human approval or auto-resolve

**Training Data Security**
- Masked PII
- No external training egress by default
- Local retraining pipeline supported

---

## 9. Security Architecture

**Zero-Trust Alignment**
- No implicit trust between services
- Identity-bound access (users, devices, services)
- Continuous verification of state

**Hardening Requirements**
- TLS 1.2+
- mTLS service mesh (Istio/Linkerd optional)
- Secrets → Vault or Kubernetes Secrets
- SBOM for all components
- Sigstore or Cosign image signing

**Audit Logging**
- Every mutation event logged with:
  - actor
  - device
  - timestamp
  - before/after state
  - evidence references

---

## 10. Observability & SRE

**Metrics**
- Throughput
- Queue depth
- Latency
- Error rates
- Deployment success/failure
- Agent health state

**Logs**
- Structured JSON across services
- Correlated via trace_id

**Traces**
- OpenTelemetry end-to-end

**Dashboards**
- Device health
- Software rollout status
- Agent coverage
- Model performance
- SLA/MTTR analytics

---

## 11. Integration Architecture

**Outbound Connectors**
- ITSM (REST/GraphQL)
- EUC Tooling (Graph/WinRM/MECM APIs)
- Identity Providers (OIDC/SCIM)
- CMDB (ServiceNow CMDB APIs)

**Inbound**
- Webhooks (incident, approvals, device regs)
- Agent Telemetry Streams

**Protocols**
- RESTful APIs
- Webhooks
- MQTT (optional)
- gRPC (internal)

---

## 12. Scalability Considerations

**Scale Targets**
- 100,000 devices per tenant
- 15 devices per user
- 50,000 parallel deployment jobs
- <1 min telemetry freshness target

**Mechanisms**
- Horizontal autoscaling
- Distributed queue processing
- Partitioned Postgres (schema or table)
- MinIO erasure coding for durability

---

## 13. Failure & Recovery

**Resilience**
- Retry with exponential backoff
- Circuit breakers
- Idempotent deployment jobs

**Backup & Restore**
- PostgreSQL PITR
- MinIO replication
- Grafana dashboards backup
- Config export/import

---

## 14. Packaging & Distribution

**Packaging Targets**
- MSI
- PKG
- IntuneWin
- Shell/PowerShell bundles
- Custom manifests

**Distribution**
- Peer-to-peer optional
- CDN optional
- LAN-less fallback with throttling

---

## 15. Roadmap Hooks (Production)

Planned integration for production readiness:
- Code signing pipeline
- Approval governance UI
- Drift monitoring dashboard
- Model lineage registry
- Script marketplace
- Offline patch scheduling

---

## 16. Non-Functional Requirements

| Attribute | Requirement |
|---|---|
| Uptime | 99.5% |
| Security | Zero Trust, audit, RBAC, mTLS |
| Compliance | GDPR, DPDP, SOC2-compatible |
| Usability | Admin & end-user portals |
| Extensibility | Connector framework |
| Deployability | K8s-native + on-prem |
| Performance | Sub-second API responses |
| Observability | Full OTEL support |
| Mobility | No VPN required |
| Data Residency | Customer-local |

---

## 17. End State

A production-ready EUC application automation platform that satisfies:
- Enterprise security
- Regulatory residency
- Multi-device reality
- Human-in-loop governance
- Zero-trust operational posture
- AI-augmented automation with provable audit
