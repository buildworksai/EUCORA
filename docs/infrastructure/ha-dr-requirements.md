# HA/DR Requirements
**Version**: 1.0
**Status**: Draft
**Last Updated**: 2026-01-05

---

## Overview
This document defines the availability and disaster recovery expectations for the Control Plane and its supporting services. The Control Plane is the **system-of-record for policy intents, approvals, and evidence** and must remain thin, stateless where practical, and resilient to infrastructure failures.

**Design Principle**: "Thin control plane" from the architecture overview — the Control Plane only orchestrates policy and evidence, it does not execute directly on endpoints.

---

## 1. HA Topology
1. **Stateless front-end services** (API gateway, policy engine, workflow orchestrator) run in at least three Availability Zones per region and sit behind a global load balancer (Azure Front Door or equivalent) with active-active routing. Health probes enforce rolling restart strategies.
2. **Control Plane database** (PostgreSQL/MySQL managed instance or equivalent) is deployed as a geo-redundant cluster with automatic failover. Synchronous replication ensures RPO ≤ 5 minutes, with asynchronous replicas for analytics.
3. **Event store + evidence store** (immutable append-only logs + object storage) are built on redundant storage accounts (Azure Blob w/ RA-GRS or similar) or enterprise object store with versioning. Evidence packs use WORM/immutable containers to satisfy audit needs.
4. **Connector service endpoints** (Intune/Jamf/SCCM/Landscape/Ansible worker pools) run stateless connectors with auto-scaling groups, pulling intents from durable queues to maintain idempotency. Connectors log correlation IDs for every operation.
5. **Telemetry/monitoring stack** streams to SIEM (Azure Sentinel/Splunk); alerts trigger CAB on-call playbooks.

### Availability Targets (Measurable)
- **Control Plane API + workflow services**: 99.9% availability target (enterprise standard) measured at 5-minute granularity per region.
- **Control Plane database**: RPO ≤ 24h (targeting ≤ 1h for tier-1 apps); RTO ≤ 8h for full recovery.
- **Evidence store**: 99.99% durability and 99.9% availability; unavailability blocks new publishes.
- **Event store**: append-only; availability aligned with database SLAs.
- **Connector worker pools**: scaling ensures no queue backlog beyond 10 minutes for critical rings.

## 2. Failure Modes Matrix
| Component | Failure | Impact | Control Plane Behavior | Mitigations/Validation |
|---|---|---|---|---|
| Control Plane API/Policy services | Stateless service outage | New Deployment Intents and approves blocked | Pause promotions; existing endpoints unaffected | LB health probes; auto-redeploy; CAB incident review; validation rule: `ServiceHealth = Healthy` required before new publish |
| Database | Primary unavailable | No reads/writes for policy/evidence | Publish/approval APIs block | Failover to secondary; runbook verifying data consistency; validation: `TransactionLag <= 5s` before failback |
| Evidence store | Object storage outage | Evidence packs cannot be written/read, publish blocked | Blocking gate with explicit error; emit Impact = publish blocked | Retry policy with exponential backoff; alternate storage region w/ `ValidatedCopyExists` check |
| Intune Graph degraded | publish/assignment fails | deployments paused for rings relying on Intune | Backoff/retry; CAB manual pause if >15 min | `ConnectorBackoff` logic ensures 2x base interval, `PromotionsPaused` flag; validation: `GraphThrottleCount <= 5` before resuming |
| Jamf API outage | macOS distribution fails | macOS ring progression halted | Backoff + CAB notification | Use SAP runbook to confirm requeue; metric `JamfQueueDepth` monitored |
| SCCM site server down | offline site distribution interrupted | Air-gapped ring cannot progress | Control Plane records site outage; promotion gate fails until site healthy | Validate `SCCM.SiteHealth = Healthy`; fallback to manual import if >24h |
| Event store write blocked | Audit events not persisted | Non-compliance risk | Reject publishes until store healthy | `EventStoreWriteSuccess >= 99.9%` per hour; failover to redundant cluster |

## 3. Backup & Restore Procedures
- **Database backups**: automated snapshots every hour with 7-day retention; separate cross-region export every 24h stored for >=90 days per compliance.
- **Evidence/event store snapshots**: versioned objects + daily inventory; retention ≥ 7 years (or compliance-specific). Restoration procedure includes hash verification and rehydration.
- **Connector state**: durable queue checkpoints stored in Azure Service Bus/AWS SQS (or equivalent) with dead-letter handling; restore by replaying `Deployment Intents` (idempotent) into connectors.
- **Key material**: signing + vault secrets recoverable via soft-delete and purge protection in Azure Key Vault or equivalent.
- **Validation rule**: `LastBackupAge <= 24h` for database + evidence store to be considered healthy.

## 4. Failover Testing Requirements
- Quarterly failover drills for each HA domain (API tier, database, evidence store, connectors) that include:
  - Controlled failover (simulate outage, validate auto-promotion, ensure RTO ≤ 8h)
  - Smoke verification (submit test Deployment Intent, validate evidence pack ingestion, ensure correlation id captured)
  - Rollback validation (Ring 0 test ensures rollback pipeline works even if connectors were in failover)
- After each test, update CAB log with results + any deviations (failures require a new risk score if thresholds missed).
- Automated validation script runs post-failover verifying: `ServicesReady = True`, `MetadataTablesInSync = True`, `EventCountGrowth >= Threshold`.

## 5. Validation Rules
1. **Evidence completeness gate**: publish APIs enforce that evidence pack writes succeeded (`EvidencePackState = Committed`) before approval.
2. **Correlation IDs**: every failover and recovery event must log correlation ids to the event store and SIEM (per `control-plane-design` documentation).
3. **Backup freshness**: gating rule `BackupAgeHours <= 24` before enabling new deployments.
4. **Connector idempotency**: connectors reapply intents after failover, verifying `Test-IdempotencyKey` to avoid duplication.
5. **CAB approval persistence**: approvals recorded in append-only event store; DR failover must validate `ApprovalEventCount` matches primary count.

---

## Related Documentation
- [docs/architecture/architecture-overview.md](../architecture/architecture-overview.md)
- [docs/architecture/control-plane-design.md](../architecture/control-plane-design.md)
- [docs/infrastructure/rbac-configuration.md](rbac-configuration.md)

---

**HA/DR Requirements v1.0 — Draft**
