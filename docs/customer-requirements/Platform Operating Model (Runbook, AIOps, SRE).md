# EUCORA — Platform Operating Model (Runbook / AIOps / SRE)

## Version
1.0.0

## Status
Draft for Ops & SRE Enablement

## Owner
BuildWorks.AI — EUCORA Product Line

---

# 1. Purpose

Define how EUCORA operates in production environments including:

- Operational ownership & roles
- AIOps execution model
- SRE observability & reliability practices
- Incident management workflows
- Change control models (human-in-loop)
- Runbooks for failure scenarios
- Deployment & upgrade strategy
- Compliance & audit handling

---

# 2. Operating Principles

1. **Zero-Trust Operations**
   - No implicit trust for services, users, devices
2. **Human-in-Loop for Risk**
   - Automated suggestions → human approval
3. **Observability by Default**
   - Metrics / logs / traces present before go-live
4. **Residency & Sovereignty**
   - All data stays inside the tenant boundary
5. **Service Level Alignment**
   - SLOs drive SRE actions and backlog priorities
6. **Self-Healing Where Safe**
   - Automated remediation for low-risk classes
7. **Minimal Downtime**
   - Rolling upgrades with rollback guarantees

---

# 3. Operational Roles

| Role | Responsibilities |
|---|---|
| Platform Owner | Budget, SLA/SLO, vendor mgmt |
| SRE Lead | Reliability, performance, observability |
| SRE Engineer | Runbooks, automation, failure handling |
| ML Engineer | Model training, validation, drift mgmt |
| EUC Engineer | Packaging, deployment orchestration |
| ITSM Manager | Incident governance & SLA tracking |
| Security Engineer | Zero-trust & compliance enforcement |
| Change Approver | Human approval gates for automation |
| Compliance Officer | Audit evidence & regulatory adherence |

---

# 4. AIOps Layer Responsibilities

The AIOps layer automates detection, recommendation, and remediation:

| Stage | Description |
|---|---|
| Detection | Identify anomalies using telemetry data |
| Enrichment | Add evidence, context, previous outcomes |
| Classification | Categorize incidents + confidence |
| Recommendation | Suggest remediation or actions |
| Approval | Human-in-loop validation (mandatory for high risk) |
| Execution | Automated script/job deployment |
| Feedback | Result logged for model retraining |

**Risk Classes:**

| Class | Definition | Handling |
|---|---|---|
| R1 Low | Safe, reversible, isolated | Auto-execute |
| R2 Medium | User-affecting but reversible | Approval optional (policy) |
| R3 High | Platform-wide/user-impacting | Mandatory approval |

---

# 5. SRE Observability Model

## 5.1 Observability Stack

| Component | Purpose |
|---|---|
| Prometheus | Metrics |
| Loki | Logs |
| Tempo | Traces |
| Grafana | Dashboards & Alerting |
| Alertmanager | Routing & Escalation |
| PostgreSQL | Metadata & SLO tracking |
| MinIO | Evidence & artifacts |

## 5.2 Golden Signals

SRE must monitor Golden Signals:

| Signal | Source |
|---|---|
| Latency | API Gateway, Agent Comm |
| Traffic | Jobs/sec, telemetry/sec |
| Errors | HTTP 4xx/5xx, job failures |
| Saturation | CPU/memory/queue/DB load |

Additional domain-specific signals:

- Deployment success rate
- Agent heartbeat coverage
- Telemetry freshness (staleness)
- Model override/rejection rate
- Evidence bundle completeness

## 5.3 KPIs

| KPI | Target |
|---|---|
| Deployment Success Rate | ≥ 98% |
| Telemetry Freshness | ≤ 5 min |
| Incident False Classification | ≤ 15% |
| Model Override Rate | ≤ 40% after 3 months |
| Agent Coverage | ≥ 97% of devices |
| MTTR (Manual) | ≤ 4 hours |
| MTTR (AI-assisted) | ≤ 2 hours |

---

# 6. SLOs, SLIs, SLAs

## 6.1 SLIs (Measured Indicators)

| SLI | Metric |
|---|---|
| Availability | % uptime per rolling 30 days |
| Latency | p50/p95/p99 API latency |
| Error Rate | failed requests / total requests |
| Coverage | active agents / total agents |
| Drift | model performance deviation |

## 6.2 SLOs (Internal Objectives)

| SLO | Target |
|---|---|
| Platform Availability | 99.5% |
| Agent Comm Latency | < 1s p95 |
| Evidence Bundle Completion | 100% |
| Classification Confidence | ≥ 85% accuracy |
| Rollout Rollback Time | ≤ 10 min |
| DB Recovery | ≤ 15 min (PITR) |

## 6.3 SLAs (Customer-Facing)

Defined by customer environment, baseline defaults:

| SLA | Default |
|---|---|
| Incident Severity 1 Response | ≤ 30 min |
| Severity 2 Response | ≤ 2 hours |
| Change Request Window | 24–72 hours |
| Data Retention Compliance | 100% guaranteed |

---

# 7. Incident Management Workflow

## 7.1 Incident Lifecycle Stages

1. Detection (AIOps / Agent / User)
2. Ticket Creation (ITSM integration)
3. Enrichment (Telemetry + Evidence)
4. Classification (ML + rules)
5. Assignment (routing)
6. Recommendation (scripts/actions)
7. Approval (human-in-loop)
8. Execution (deployment/patch/script)
9. Verification (health checks)
10. Closure (audit + feedback loop)

## 7.2 Evidence Requirements

Every incident must include:

- Device metadata
- User-session correlation
- Telemetry snapshot
- Job history
- Model inference (if applicable)
- Confidence score
- Action logs & outcomes

## 7.3 ITSM Integration

Supported via REST/Webhooks for:

- Incident ↔ EUCORA sync
- Approval workflow sync
- CMDB sync (device/software)
- SLA tracking

---

# 8. Change Management Model

Since customer clarified **Human-in-Loop**, model is:

| Change Type | Approval |
|---|---|
| R1 Low Risk | Auto |
| R2 Medium Risk | Policy-dependent |
| R3 High Risk | Human mandatory |

**Approver Evidence Bundle Includes:**

- Reasoning
- Confidence
- Risk level
- Impact radius
- Rollback strategy
- Similar past outcomes

---

# 9. Runbooks (Critical)

## 9.1 Agent Connectivity Failure

**Symptoms**
- No heartbeat
- Telemetry stale
- Jobs queued

**Actions**
- Validate TLS cert lifetime
- Validate gateway reachability
- Check proxy config
- Check DNS resolution
- Inspect agent logs via local tool

**Recovery**
- Retry with exponential backoff
- Re-register device if identity mismatch

---

## 9.2 Deployment Rollback

**Triggers**
- High failure rate
- User impact detected
- Security violation

**Steps**
1. Halt rollout
2. Notify change approvers
3. Trigger rollback job
4. Collect failure evidence
5. Update CMDB & ITSM
6. Create model feedback event

---

## 9.3 Model Drift Event

**Detection Signals**
- Confidence drop
- Override spike
- Error rate spike
- Seasonal input drift

**Remediation**
1. Freeze new inferences (optional)
2. Retrain on recent data
3. Validate & approve model
4. Deploy new model
5. Re-enable inference
6. Log lineage event

---

# 10. Deployment & Upgrade Strategy

## 10.1 Supported Modes

| Mode | Description |
|---|---|
| All-in-One | Demo / pilot |
| Multi-Node | Standard production |
| Kubernetes | Preferred production |

## 10.2 Upgrade Rules

- Rolling deployments
- Backward compatibility for agents
- Schema migrations versioned
- MinIO objects versioned
- PostgreSQL PITR enabled
- Rollback supported via container tags + DB snapshot

## 10.3 Agent Upgrade

- Delta patching
- Signed binaries
- Throttled waves
- Rollback supported

---

# 11. Security & Compliance Operations

**Operational Controls**
- RBAC for all UI/API actions
- mTLS for all services
- SBOM collection
- Sigstore or Cosign signing (future)
- MinIO object policies (WORM optional)
- PostgreSQL encryption (TLS at rest optional)

**Audit Outputs**
- Access logs
- Incident logs
- Approval logs
- Remediation logs
- Model lineage logs
- Deployment history

All logs stored for **730 days** by default.

---

# 12. End State

This Operating Model ensures EUCORA can run in regulated, global, remote-first enterprise environments with:

- Predictable reliability
- Safe automation
- Defensible audit trails
- Zero-trust posture
- SRE-grade observability
- AI models with governance & human oversight
- Clear runbooks for failure & incident handling

---
