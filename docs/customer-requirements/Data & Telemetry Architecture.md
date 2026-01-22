# EUCORA — Data & Telemetry Architecture

## Version
1.0.0

## Status
Draft for Architecture & SRE Review

## Owner
BuildWorks.AI — EUCORA Product Line

---

# 1. Purpose

Define the data models, telemetry flows, storage systems, protocols, retention policy, and observability layers for EUCORA’s production deployment, aligning to:

- Regulatory residency (self-hosted)
- Zero-trust security
- Remote-first endpoints
- AI-assisted reasoning
- Observability & SRE practices
- Compliance & audit requirements

---

# 2. Architectural Principles

- **Single Tenant Data Boundary:** no cross-customer data mixing
- **Residency Guaranteed:** PostgreSQL + MinIO deployed on customer infra
- **Telemetry as Signals, not Logs:** structured metrics → insights
- **Schema Governed:** strong typing for device and incident data
- **Push + Pull Telemetry:** agent-initiated + on-demand collection
- **Offline-Aware:** queued delivery with replay
- **Open Standards:** OpenTelemetry for metrics/logs/traces
- **Immutable Audit Trails:** Loki + PostgreSQL records

---

# 3. High-Level Data Architecture

**Core Data Domains**
1. Device Inventory
2. User–Device Correlation
3. Software Inventory
4. Packaging & Deployment Jobs
5. Telemetry & UX Metrics
6. Incidents & Evidence
7. AI Inference Metadata
8. Audit & Compliance

**Primary Stores**
| Store | Backend | Data Type |
|---|---|---|
| Metadata | PostgreSQL | normalized structured data |
| Artifacts | MinIO | binaries, bundles, evidence |
| Metrics | Prometheus | device + network + app metrics |
| Logs | Loki | structured application logs |
| Traces | Tempo | distributed traces |
| Cache/Queue | Redis | ephemeral |
| Config Store | PostgreSQL | manifests, policies |

---

# 4. Telemetry Model

## 4.1 Telemetry Categories

| Category | Description |
|---|---|
| Device Health | CPU, memory, disk, battery, thermal |
| App Performance | launch time, crash rate, hangs, errors |
| UX Scoring | latency, responsiveness, DPI events |
| Network | latency, bandwidth, proxy impact, loss |
| Software Inventory | installed packages, versions, signatures |
| Agent Health | heartbeats, queue depth, retries |
| Deployment Signals | success/failure, rollback, durations |

## 4.2 Device Telemetry Payload (Schema)

```json
{
  "device_id": "string",
  "user_id": "string",
  "timestamp": "RFC3339",
  "hardware": {
    "cpu": "percent",
    "memory": "percent",
    "disk": "percent",
    "thermal": "Celsius",
    "battery": "percent"
  },
  "software": {
    "packages": [
      { "name": "string", "version": "string", "signature": "sha256" }
    ]
  },
  "network": {
    "latency_ms": "number",
    "throughput_mbps": "number",
    "proxy": "bool"
  },
  "agent": {
    "version": "string",
    "queue_depth": "number",
    "status": "healthy|degraded|offline"
  }
}
````

---

# 5. Ingestion & Processing Pipeline

## 5.1 Transport Protocols

| Direction         | Protocol       |
| ----------------- | -------------- |
| Agent → Platform  | HTTPS/2 (JSON) |
| Service → Service | gRPC           |
| Telemetry Export  | OTLP           |
| Metrics Scrape    | Prometheus     |
| Logs              | Loki API       |
| Traces            | OTLP           |

MQTT optional for push events in low bandwidth sites.

## 5.2 Pipeline Stages

1. **Collection** (Agent → API Gateway)
2. **Validation** (Schema + Signature)
3. **Normalization** (Units, OS variants)
4. **Enrichment** (User, device, policy data)
5. **Routing** (Metrics/Logs/Traces/DB)
6. **Storage**
7. **Downstream Consumption**

   * dashboards
   * AI inference
   * compliance engine
   * incident creation

---

# 6. Data Flow Diagrams (Logical)

```
[Agent] 
   → (HTTPS/2) → [API Gateway]
       → [Telemetry Normalizer]
           ↘ Prometheus (metrics)
           ↘ Loki (logs)
           ↘ Tempo (traces)
           ↘ PostgreSQL (metadata)
           ↘ MinIO (evidence)
```

Downstream:

```
[Prometheus] → Grafana dashboards
[Loki] → LogQL queries + audit review
[Tempo] → Tracing UI + SRE workflows
[PostgreSQL] → CMDB/Inventory/Policies
[MinIO] → Evidence bundles, artifacts, packages
```

---

# 7. Storage Design

## 7.1 PostgreSQL (Relational Metadata)

**Tables include:**

* `devices`
* `users`
* `device_user_map`
* `software_inventory`
* `jobs`
* `incidents`
* `inference_events`
* `approvals`
* `policies`
* `audit_events`

## 7.2 MinIO (Artifacts & Evidence)

Stores:

* Packaging artifacts
* Installer binaries
* Deployment logs
* Evidence bundles
* Crash dumps
* AI model dumps & lineage
* SBOMs (future)

Benefits:

* On-prem
* S3-compatible
* WORM + replication support

## 7.3 Prometheus (Metrics)

Stores:

* numerical time-series
* ingest from devices & services

Used for:

* SRE dashboards
* anomaly alerts
* UX scoring

## 7.4 Loki (Logs)

Stores structured logs:

* agent logs
* remediation logs
* deployment logs
* audit logs

## 7.5 Tempo (Traces)

Stores:

* service traces
* device job execution traces (optional)

---

# 8. Retention & Purging Policies

Defaults (tenant controlled):

| Data Type            | Retention | Store             |
| -------------------- | --------- | ----------------- |
| Telemetry Metrics    | 90 days   | Prometheus        |
| Logs                 | 180 days  | Loki              |
| Traces               | 30 days   | Tempo             |
| Inventory & Metadata | 365 days  | PostgreSQL        |
| Incidents            | 365 days  | PostgreSQL        |
| Evidence Bundles     | 365 days  | MinIO             |
| Audit Logs           | 730 days  | PostgreSQL + Loki |
| AI Metrics           | 730 days  | PostgreSQL        |

Supports:

* GDPR right-to-erasure
* DPDP consent management
* Sohar/FINRA-like audit extensions

---

# 9. Identity & Device Correlation Model

**Multi-device rule:** up to **15 devices per user**

Tables:

| Table             | Purpose                  |
| ----------------- | ------------------------ |
| `users`           | identity record          |
| `devices`         | device record            |
| `device_user_map` | N:1 mapping              |
| `sessions`        | user <-> device sessions |

**Session Mapping Example:**

```json
{
  "session_id": "uuid",
  "user_id": "uuid",
  "device_id": "uuid",
  "start": "timestamp",
  "end": "timestamp",
  "context": {
    "network": "corp|home|public",
    "vpn": true,
    "geo": "ISO-3166"
  }
}
```

This enables **causal correlation** for incidents.

---

# 10. Regulatory & Compliance Modes

Supports:

* GDPR
* India DPDP
* SOC2
* ISO 27001
* NIST 800-53 audit mappings

**Residency Enforcement**

* MinIO + PostgreSQL deployed local
* No external training loops unless opted-in
* Masked PII for AI pipelines

---

# 11. Observability & SRE

## 11.1 Metrics (Prometheus)

Examples:

* `agent_heartbeat_failures`
* `deployment_success_total`
* `deployment_failure_total`
* `latency_p50,p95,p99`
* `queue_depth`
* `model_confidence_avg`
* `model_override_rate`

## 11.2 Logs (Loki)

Logs are structured JSON for:

* audit trails
* evidence generation
* remediation actions
* system events

## 11.3 Traces (Tempo)

Traces for:

* deployment workflows
* remediation workflows
* inference pipeline timing

---

# 12. AI Consumption of Telemetry

Telemetry feeds:

1. **Classification Models**

   * device health categories
   * failure patterns

2. **Recommendation Models**

   * remediation scripts
   * configuration changes

3. **Anomaly Detection**

   * outlier metrics
   * drift detection

4. **Evidence Bundles**

   * telemetry snapshots
   * job context
   * model confidence

---

# 13. Failure Handling & Offline Scenarios

Agents must support:

* local queueing
* exponential backoff
* deduplication
* replay on reconnect
* delta compression
* conflict resolution

Severity classification:

| Severity    | Symptom             | Action                 |
| ----------- | ------------------- | ---------------------- |
| S1 Critical | telemetry lost      | buffer + retry         |
| S2 Partial  | degraded throughput | compress + batch       |
| S3 Minor    | reorder events      | logical timestamp sort |

---

# 14. End State

The Data & Telemetry Architecture provides:

* Residency & compliance guarantees
* Complete observability stack (metrics/logs/traces)
* AI-ready signal streams
* Strong schema governance
* SRE-grade reliability
* Zero-trust data plane behavior
* Multi-device aware correlation

It is production-safe for regulated enterprises with remote-first user bases.

---