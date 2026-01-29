# EUCORA — Master Implementation Plan (Production Readiness)

**SPDX-License-Identifier: Apache-2.0**

**Version**: 2.0.0
**Status**: AUTHORITATIVE
**Created**: January 25, 2026
**Owner**: Platform Engineering Agent
**Classification**: INTERNAL — Production Implementation Roadmap

---

## Executive Summary

This document is the **single source of truth** for EUCORA's production implementation roadmap. It supersedes all previous planning documents in `docs/planning/old/`.

**Current State**: MVP demonstrated, deal won. Core control plane operational (P1-P5.3 complete).

**Target State**: Production-grade enterprise deployment with:
- Full multi-platform execution (Windows, macOS, Linux, iOS, Android)
- License Management (SAM-grade, AI-assisted)
- Application Portfolio Compliance
- User/Admin Management with AD Integration
- AI Governance hardening

---

## 1. Customer Requirements Traceability Matrix

| Requirement Source | Key Deliverables | Target Phase |
|-------------------|------------------|--------------|
| **PRD Epic 1** — Packaging Automation | Package intake, SBOM, signing, evidence | P6 |
| **PRD Epic 2** — Deployment & Rollout | Ring-based rollout, rollback, offline-aware | P6 |
| **PRD Epic 3** — Device & Telemetry | Health metrics, UX scoring, inventory | P6 (enhance) |
| **PRD Epic 4** — AI Remediation | Incident classification, recommendations | P7 |
| **PRD Epic 5** — Change Control | CAB workflow, risk scoring, evidence | ✓ P5.3 DONE |
| **PRD Epic 6** — ITSM & EUC Integrations | ServiceNow, Jira, Intune, Jamf, SCCM | P6 |
| **PRD Epic 7** — Policy Engine | Compliance scoring, violations, alerts | P6 (enhance) |
| **License-management.md** | Vendor/SKU, entitlements, consumption, AI agents | P8-P9 |
| **Application-Portfolio-compliance.md** | App inventory, dependencies, portfolio risk | P9-P10 |
| **AI Governance Blueprint** | Human-in-loop, model lifecycle, drift detection | P7 |
| **Data & Telemetry Architecture** | OTEL, Prometheus, Loki, Tempo, residency | ✓ P3 DONE |
| **Platform Operating Model** | SRE, runbooks, AIOps, incident mgmt | P7, P11 |
| **Technical Architecture** | K8s deployment, zero-trust, mTLS | P11 |

---

## 2. Phase Completion Status

### Completed Phases

| Phase | Name | Status | Completion Date |
|-------|------|--------|-----------------|
| P0-P1 | Control Plane Baseline | ✅ COMPLETE | Jan 2026 |
| P2 | Resilience & Retry Patterns | ✅ COMPLETE | Jan 2026 |
| P3 | Observability Stack | ✅ COMPLETE | Jan 2026 |
| P4 | Testing & Quality Gates | ✅ COMPLETE | Jan 22, 2026 |
| P5.1 | Evidence Pack Generation | ✅ COMPLETE | Jan 21, 2026 |
| P5.2 | CAB Workflow + Risk Gates | ✅ COMPLETE | Jan 23, 2026 |
| P5.3 | CAB REST API | ✅ COMPLETE | Jan 24, 2026 |

### Active/Planned Phases

| Phase | Name | Status | Target |
|-------|------|--------|--------|
| P6 | Connectors & Multi-Platform | 🔄 IN PROGRESS | Week 1-3 |
| P7 | AI Agents & Governance | 🔄 IN PROGRESS | Week 2-4 |
| P8 | License Management Core | 📋 PLANNED | Week 3-5 |
| P9 | License AI Agents + Portfolio | 📋 PLANNED | Week 5-7 |
| P10 | User & Admin Management | 📋 PLANNED | Week 6-8 |
| P11 | Enterprise Hardening | 📋 PLANNED | Week 8-10 |
| P12 | Production Certification | 📋 PLANNED | Week 10-12 |

---

## 3. Critical Path Analysis

```
P6 (Connectors) ─────────────────────┐
                                     │
P7 (AI Governance) ──────────────────┼──► P11 (Enterprise Hardening)
                                     │
P8 (License Core) ──► P9 (License AI)┘
                          │
                          ▼
                    P10 (User Mgmt)
                          │
                          ▼
                    P12 (Production Cert)
```

**Critical Dependencies**:
1. P6 must complete Intune connector before P8 can pull consumption signals
2. P7 AI governance framework required before P9 license AI agents
3. P10 User Management requires P6 AD connector infrastructure
4. P11 requires all feature phases (P6-P10) to be code-complete

---

## 4. Phase Specifications

---

### Phase P6: Connectors & Multi-Platform Execution

**Duration**: 3 weeks
**Priority**: CRITICAL
**Dependencies**: P5.3 (CAB API)

> ⚠️ **CURRENT STATE WARNING**: As of Jan 25, 2026, only **Intune and Jamf** are production-ready. **SCCM, Landscape, and Ansible connectors are VAPORWARE** — they consist of 42-line PowerShell stubs that return hardcoded success without contacting any actual system. See [CONNECTOR-AUDIT-STATUS.md](./CONNECTOR-AUDIT-STATUS.md) for details.

#### 4.1 Objectives

Deliver production-ready connectors for all execution planes with idempotent operations, proper error handling, and reconciliation support.

#### 4.2 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D6.1** Intune Connector | Graph API integration for Win32/MSIX | Apps CRUD, assignment, compliance query |
| **D6.2** Jamf Connector | Jamf Pro API for PKG deployment | Package upload, policy creation, scope |
| **D6.3** SCCM Connector | WMI/REST for offline site distribution | Package, DP distribution, collection targeting |
| **D6.4** Landscape Connector | API for Ubuntu/Debian package mgmt | Repo sync, package install, compliance |
| **D6.5** Ansible Connector | AWX/Tower API for Linux remediation | Job template trigger, inventory sync |
| **D6.6** AD/Entra ID Connector | User/group sync, authentication | SCIM/Graph sync, group membership |
| **D6.7** Mobile Connectors | iOS (ABM), Android Enterprise | VPP assignment, managed app config |
| **D6.8** Reconciliation Engine | Desired vs actual drift detection | Drift events, remediation triggers |

#### 4.3 Data Model Additions

```python
# backend/apps/connectors/models.py (additions)
class ConnectorInstance(TimeStampedModel):
    """Configuration for a specific connector deployment."""
    connector_type = models.CharField(max_length=50, choices=CONNECTOR_TYPES)
    name = models.CharField(max_length=255)
    config_encrypted = models.BinaryField()  # Encrypted credentials
    status = models.CharField(max_length=20, choices=CONNECTOR_STATUS)
    last_sync_at = models.DateTimeField(null=True)
    health_status = models.CharField(max_length=20)

class SyncJob(TimeStampedModel):
    """Tracks sync operations between control plane and execution plane."""
    connector = models.ForeignKey(ConnectorInstance, on_delete=models.CASCADE)
    job_type = models.CharField(max_length=50)  # full_sync, delta_sync, push
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    records_processed = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    correlation_id = models.UUIDField()

class DriftEvent(TimeStampedModel):
    """Records drift between desired and actual state."""
    connector = models.ForeignKey(ConnectorInstance, on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=50)  # app, assignment, policy
    entity_id = models.CharField(max_length=255)
    desired_state = models.JSONField()
    actual_state = models.JSONField()
    drift_type = models.CharField(max_length=50)  # missing, modified, extra
    detected_at = models.DateTimeField(auto_now_add=True)
    remediation_status = models.CharField(max_length=20)
```

#### 4.4 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/connectors/` | GET, POST | List/create connector instances |
| `/api/connectors/{id}/` | GET, PUT, DELETE | Connector CRUD |
| `/api/connectors/{id}/test/` | POST | Test connectivity |
| `/api/connectors/{id}/sync/` | POST | Trigger sync job |
| `/api/connectors/{id}/sync/status/` | GET | Get sync status |
| `/api/connectors/{id}/drift/` | GET | Get drift events |
| `/api/connectors/{id}/reconcile/` | POST | Trigger reconciliation |
| `/api/sync-jobs/` | GET | List all sync jobs |
| `/api/drift-events/` | GET | List drift events (filterable) |

#### 4.5 Connector Interface Contract

```python
# backend/apps/connectors/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SyncResult:
    success: bool
    records_processed: int
    records_created: int
    records_updated: int
    records_deleted: int
    errors: List[Dict[str, Any]]
    correlation_id: str

class BaseConnector(ABC):
    """All connectors must implement this interface."""

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify connectivity to execution plane."""
        pass

    @abstractmethod
    async def sync_inventory(self) -> SyncResult:
        """Pull current state from execution plane."""
        pass

    @abstractmethod
    async def push_intent(self, intent: DeploymentIntent) -> SyncResult:
        """Push deployment intent to execution plane."""
        pass

    @abstractmethod
    async def get_compliance_status(self, scope: str) -> Dict[str, Any]:
        """Query compliance status from execution plane."""
        pass

    @abstractmethod
    async def rollback(self, deployment_id: str) -> SyncResult:
        """Execute rollback for a deployment."""
        pass

    @abstractmethod
    def get_idempotency_key(self, operation: str, params: Dict) -> str:
        """Generate idempotency key for operation."""
        pass
```

#### 4.6 Test Requirements

| Test Category | Minimum Coverage | Test Count |
|---------------|------------------|------------|
| Unit Tests (per connector) | 90% | ~50 per connector |
| Integration Tests | 80% | ~30 per connector |
| Idempotency Tests | 100% operations | ~20 per connector |
| Drift Detection Tests | 90% | ~15 |
| Rollback Tests | 100% | ~10 per connector |

#### 4.7 Quality Gates

- [ ] All connector tests pass with ≥90% coverage
- [ ] Idempotency verified for all write operations
- [ ] Circuit breaker patterns implemented
- [ ] Retry with exponential backoff implemented
- [ ] Credentials encrypted at rest
- [ ] Audit logging for all operations
- [ ] TypeScript types for frontend connector management

---

### Phase P7: AI Agents & Governance

**Duration**: 3 weeks
**Priority**: HIGH
**Dependencies**: P6 (partial), P5.3 (CAB API)

#### 4.8 Objectives

Harden AI governance framework with human-in-loop approval, model lifecycle management, drift detection, and comprehensive audit trails.

#### 4.9 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D7.1** Agent Execution Framework | Unified agent runner with guardrails | All agents run through framework |
| **D7.2** Human-in-Loop Approval UI | Approval dialogs with evidence | All R2/R3 actions require approval |
| **D7.3** Model Registry | Model versioning and lineage | All models tracked with metadata |
| **D7.4** Drift Detection Pipeline | Input/output distribution monitoring | Alerts on drift thresholds |
| **D7.5** Agent Audit Trail | Complete logging of agent actions | Every action traceable |
| **D7.6** Incident Classification Agent | Enhanced with confidence calibration | ≥85% accuracy, calibrated confidence |
| **D7.7** Remediation Advisor Agent | Script recommendation with evidence | Recommendations include rollback plan |
| **D7.8** Risk Assessment Agent | Deterministic risk scoring | Explainable scores with factors |

#### 4.10 Data Model Additions

```python
# backend/apps/ai_agents/models.py (additions)
class AIModel(TimeStampedModel):
    """Registry of AI models with lineage tracking."""
    model_id = models.CharField(max_length=100, unique=True)
    model_type = models.CharField(max_length=50)  # classification, recommendation, etc.
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20)  # draft, validated, deployed, deprecated
    dataset_version = models.CharField(max_length=100)
    training_params = models.JSONField()
    validation_report = models.JSONField()
    risk_level = models.CharField(max_length=10)  # R1, R2, R3
    deployed_at = models.DateTimeField(null=True)
    deployed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class AgentExecution(TimeStampedModel):
    """Audit trail for agent executions."""
    agent_type = models.CharField(max_length=100)
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True)
    correlation_id = models.UUIDField()
    input_hash = models.CharField(max_length=64)
    input_summary = models.JSONField()
    output = models.JSONField()
    confidence = models.FloatField(null=True)
    risk_level = models.CharField(max_length=10)
    approval_required = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_at = models.DateTimeField(null=True)
    executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True)
    execution_result = models.JSONField(null=True)

class ModelDriftMetric(TimeStampedModel):
    """Tracks model performance drift over time."""
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE)
    metric_type = models.CharField(max_length=50)  # accuracy, confidence_mean, override_rate
    value = models.FloatField()
    threshold = models.FloatField()
    is_alert = models.BooleanField(default=False)
    recorded_at = models.DateTimeField(auto_now_add=True)
```

#### 4.11 Agent Guardrails (Non-Negotiable)

```python
# backend/apps/ai_agents/guardrails.py
from enum import Enum
from typing import Optional
from dataclasses import dataclass

class RiskLevel(Enum):
    R1_LOW = "R1"      # Auto-execute allowed
    R2_MEDIUM = "R2"   # Policy-dependent approval
    R3_HIGH = "R3"     # Mandatory human approval

@dataclass
class AgentGuardrail:
    """Defines execution boundaries for an agent."""
    agent_type: str
    risk_level: RiskLevel
    requires_approval: bool
    requires_evidence_pack: bool
    allowed_actions: list[str]
    forbidden_actions: list[str]
    max_scope_size: int  # Max devices/users affected
    timeout_seconds: int

AGENT_GUARDRAILS = {
    "incident_classifier": AgentGuardrail(
        agent_type="incident_classifier",
        risk_level=RiskLevel.R1_LOW,
        requires_approval=False,
        requires_evidence_pack=True,
        allowed_actions=["classify", "suggest_category"],
        forbidden_actions=["modify_incident", "close_incident"],
        max_scope_size=1,
        timeout_seconds=30,
    ),
    "remediation_advisor": AgentGuardrail(
        agent_type="remediation_advisor",
        risk_level=RiskLevel.R2_MEDIUM,
        requires_approval=True,
        requires_evidence_pack=True,
        allowed_actions=["recommend_script", "recommend_kb"],
        forbidden_actions=["execute_script", "modify_device"],
        max_scope_size=100,
        timeout_seconds=60,
    ),
    "auto_remediator": AgentGuardrail(
        agent_type="auto_remediator",
        risk_level=RiskLevel.R3_HIGH,
        requires_approval=True,
        requires_evidence_pack=True,
        allowed_actions=["execute_approved_script"],
        forbidden_actions=["execute_unapproved", "modify_system_config"],
        max_scope_size=10,
        timeout_seconds=300,
    ),
}
```

#### 4.12 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/models/` | GET, POST | Model registry CRUD |
| `/api/ai/models/{id}/deploy/` | POST | Deploy model to production |
| `/api/ai/models/{id}/rollback/` | POST | Rollback to previous version |
| `/api/ai/executions/` | GET | List agent executions |
| `/api/ai/executions/{id}/approve/` | POST | Approve pending execution |
| `/api/ai/executions/{id}/reject/` | POST | Reject pending execution |
| `/api/ai/drift/` | GET | Get drift metrics |
| `/api/ai/drift/alerts/` | GET | Get active drift alerts |

#### 4.13 Quality Gates

- [ ] All agents execute through guardrail framework
- [ ] R2/R3 actions blocked without approval
- [ ] Complete audit trail for all agent actions
- [ ] Model lineage tracked for all deployed models
- [ ] Drift detection operational with alerting
- [ ] ≥90% test coverage for agent framework
- [ ] Evidence packs generated for all recommendations

---

### Phase P8: License Management Core

**Duration**: 2-3 weeks
**Priority**: CRITICAL (Customer Requirement)
**Dependencies**: P6 (connectors for consumption signals)

#### 4.14 Objectives

Implement enterprise-grade Software Asset Management (SAM) comparable to Flexera/ServiceNow SAMPro, with deterministic reconciliation and evidence-first governance.

#### 4.15 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D8.1** License Data Model | Vendor, SKU, Entitlement, Pool, Consumption | All entities with audit trail |
| **D8.2** Entitlement Management API | CRUD for license entitlements | Approval-governed writes |
| **D8.3** Consumption Signal Ingestion | Pull from MDM/telemetry sources | Normalized consumption units |
| **D8.4** Reconciliation Engine | Deterministic truth builder | Immutable snapshots with evidence |
| **D8.5** Sidebar Component | Real-time consumption display | Consumed/Entitled/Remaining + health |
| **D8.6** License Dashboard | Trends, alerts, drilldowns | Evidence export capability |
| **D8.7** Import/Export API | CSV/JSON import with validation | Schema validation, audit logging |

#### 4.16 Data Model

```python
# backend/apps/license_management/models.py
from django.db import models
from apps.core.models import TimeStampedModel, CorrelationIdModel

class Vendor(TimeStampedModel):
    """Software vendor master data."""
    name = models.CharField(max_length=255, unique=True)
    identifier = models.CharField(max_length=100, unique=True)
    website = models.URLField(blank=True)
    support_contact = models.EmailField(blank=True)
    notes = models.TextField(blank=True)

class LicenseModelType(models.TextChoices):
    DEVICE = "device", "Per Device"
    USER = "user", "Per User"
    CONCURRENT = "concurrent", "Concurrent"
    SUBSCRIPTION = "subscription", "Subscription Seat"
    FEATURE = "feature", "Feature Add-on"

class LicenseSKU(TimeStampedModel):
    """License SKU with model type and computation rules."""
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    sku_code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    license_model_type = models.CharField(
        max_length=20,
        choices=LicenseModelType.choices
    )
    unit_rules = models.JSONField(default=dict)  # Computation rules
    normalization_rules = models.JSONField(default=dict)  # Signal normalization

    class Meta:
        unique_together = ['vendor', 'sku_code']

class Entitlement(TimeStampedModel, CorrelationIdModel):
    """Purchased/contracted license entitlement."""
    sku = models.ForeignKey(LicenseSKU, on_delete=models.CASCADE)
    contract_id = models.CharField(max_length=100)
    entitled_quantity = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True)
    terms = models.JSONField(default=dict)
    document_refs = models.JSONField(default=list)  # MinIO refs
    renewal_date = models.DateField(null=True)
    status = models.CharField(max_length=20)  # active, expired, pending
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_entitlements'
    )
    approved_at = models.DateTimeField(null=True)

class LicensePool(TimeStampedModel):
    """Allocation pool for a SKU with optional scope."""
    sku = models.ForeignKey(LicenseSKU, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    scope_type = models.CharField(max_length=20)  # global, region, bu
    scope_value = models.CharField(max_length=100, blank=True)
    entitled_quantity_override = models.IntegerField(null=True)
    reserved_quantity = models.IntegerField(default=0)

class Assignment(TimeStampedModel):
    """License assignment to user or device."""
    pool = models.ForeignKey(LicensePool, on_delete=models.CASCADE)
    principal_type = models.CharField(max_length=20)  # user, device
    principal_id = models.CharField(max_length=255)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20)  # active, revoked, expired

class ConsumptionSignal(TimeStampedModel):
    """Raw consumption signal from source system."""
    source_system = models.CharField(max_length=50)  # intune, jamf, etc.
    raw_id = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    principal_type = models.CharField(max_length=20)
    principal_id = models.CharField(max_length=255)
    sku = models.ForeignKey(LicenseSKU, on_delete=models.CASCADE)
    confidence = models.FloatField()  # 0.0 - 1.0
    raw_payload_hash = models.CharField(max_length=64)

    class Meta:
        indexes = [
            models.Index(fields=['source_system', 'raw_id']),
            models.Index(fields=['sku', 'timestamp']),
        ]

class ConsumptionUnit(TimeStampedModel):
    """Normalized, deduplicated consumption unit."""
    sku = models.ForeignKey(LicenseSKU, on_delete=models.CASCADE)
    pool = models.ForeignKey(LicensePool, on_delete=models.CASCADE, null=True)
    principal_type = models.CharField(max_length=20)
    principal_id = models.CharField(max_length=255)
    signals = models.ManyToManyField(ConsumptionSignal)
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True)
    status = models.CharField(max_length=20)  # active, inactive

class ConsumptionSnapshot(TimeStampedModel):
    """Immutable reconciled truth snapshot."""
    sku = models.ForeignKey(LicenseSKU, on_delete=models.CASCADE)
    pool = models.ForeignKey(LicensePool, on_delete=models.CASCADE, null=True)
    reconciled_at = models.DateTimeField()
    ruleset_version = models.CharField(max_length=50)
    entitled = models.IntegerField()
    consumed = models.IntegerField()
    reserved = models.IntegerField()
    remaining = models.IntegerField()
    evidence_pack_hash = models.CharField(max_length=64)
    evidence_pack_ref = models.CharField(max_length=500)  # MinIO path

    class Meta:
        indexes = [
            models.Index(fields=['sku', 'reconciled_at']),
            models.Index(fields=['reconciled_at']),
        ]

class ReconciliationRun(TimeStampedModel, CorrelationIdModel):
    """Tracks a reconciliation job execution."""
    status = models.CharField(max_length=20)  # running, completed, failed
    ruleset_version = models.CharField(max_length=50)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    skus_processed = models.IntegerField(default=0)
    snapshots_created = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    diff_summary = models.JSONField(default=dict)
    triggered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class LicenseAlert(TimeStampedModel):
    """Alert for license anomalies."""
    sku = models.ForeignKey(LicenseSKU, on_delete=models.CASCADE)
    pool = models.ForeignKey(LicensePool, on_delete=models.CASCADE, null=True)
    alert_type = models.CharField(max_length=50)  # overconsumption, expiring, spike, etc.
    severity = models.CharField(max_length=20)  # info, warning, critical
    message = models.TextField()
    detected_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

#### 4.17 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/licenses/summary/` | GET | Global counters + health |
| `/api/licenses/vendors/` | GET, POST | Vendor CRUD |
| `/api/licenses/skus/` | GET, POST | SKU CRUD |
| `/api/licenses/skus/{id}/` | GET, PUT | SKU detail |
| `/api/licenses/entitlements/` | GET, POST | Entitlement CRUD (approval required) |
| `/api/licenses/pools/` | GET, POST | Pool CRUD |
| `/api/licenses/assignments/` | GET, POST, DELETE | Assignment management |
| `/api/licenses/signals/` | GET | Raw consumption signals |
| `/api/licenses/snapshots/` | GET | Reconciled snapshots |
| `/api/licenses/snapshots/{id}/evidence/` | GET | Evidence pack download |
| `/api/licenses/reconcile/run/` | POST | Trigger reconciliation |
| `/api/licenses/reconcile/status/` | GET | Get reconciliation status |
| `/api/licenses/alerts/` | GET | Active alerts |
| `/api/licenses/import/` | POST | Import file upload |

#### 4.18 Frontend Components

```typescript
// frontend/src/routes/licenses/contracts.ts
export interface LicenseSummary {
  total_entitled: number;
  total_consumed: number;
  total_remaining: number;
  last_reconciled_at: string;
  health_status: 'ok' | 'degraded' | 'failed' | 'stale';
  health_message?: string;
  stale_duration_seconds?: number;
}

export interface LicenseSKU {
  id: string;
  vendor_name: string;
  sku_code: string;
  name: string;
  license_model_type: 'device' | 'user' | 'concurrent' | 'subscription' | 'feature';
  entitled: number;
  consumed: number;
  remaining: number;
  trend_30d: number[];
}

export interface ConsumptionSnapshot {
  id: string;
  sku_id: string;
  reconciled_at: string;
  entitled: number;
  consumed: number;
  remaining: number;
  diff_from_previous: {
    entitled_change: number;
    consumed_change: number;
  };
  evidence_pack_url: string;
}
```

#### 4.19 Sidebar Component Spec

```tsx
// frontend/src/components/licenses/LicenseSidebar.tsx
interface LicenseSidebarProps {
  summary: LicenseSummary;
  onClickDetails: () => void;
}

/**
 * Sidebar widget showing license consumption status.
 *
 * REQUIREMENTS:
 * - Shows Consumed / Entitled / Remaining
 * - Shows "Last reconciled: <timestamp>"
 * - Shows health indicator (OK/Degraded/Failed/Stale)
 * - If stale (>2x schedule interval), shows warning with duration
 * - Click opens License Dashboard
 * - Updates from latest ConsumptionSnapshot via React Query
 * - Polling interval: 60 seconds
 */
```

#### 4.20 Quality Gates

- [ ] Reconciliation produces deterministic, reproducible results
- [ ] Snapshots are immutable with evidence pack references
- [ ] All counters explainable down to device/user level
- [ ] Import jobs validate schema and log all operations
- [ ] Sidebar displays latest snapshot values accurately
- [ ] Health indicator reflects actual reconciliation status
- [ ] ≥90% test coverage for license management
- [ ] All write APIs require appropriate RBAC roles
- [ ] Audit trail for all entitlement changes

---

### Phase P9: License AI Agents + Application Portfolio

**Duration**: 2-3 weeks
**Priority**: HIGH
**Dependencies**: P7 (AI Framework), P8 (License Core)

#### 4.21 Objectives

Implement AI agents for license intelligence and begin Application Portfolio Management capabilities.

#### 4.22 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D9.1** License Inventory Extractor Agent | Extract entitlements from contracts/portals | Produces draft entitlements, requires approval |
| **D9.2** Consumption Discovery Agent | Identify consumption from telemetry | Normalized signals with confidence |
| **D9.3** Anomaly & Drift Detector Agent | Detect spikes, negative remaining, oscillation | Alerts with explanations |
| **D9.4** Optimization Advisor Agent | Recommend reclaim/reassign/purchase | Recommendations only, no auto-action |
| **D9.5** Application Catalog | Normalized app inventory | Deduplicated, version-tracked |
| **D9.6** App-License Association | Link apps to license SKUs | Many-to-many with evidence |
| **D9.7** Dependency Mapping | Runtime and shared dependencies | Inferred + manual + evidence |
| **D9.8** Portfolio Dashboard (Basic) | App inventory with compliance status | Filters, search, export |

#### 4.23 AI Agent Specifications

```python
# backend/apps/license_management/agents/inventory_extractor.py
class LicenseInventoryExtractorAgent(BaseAgent):
    """
    Extracts entitlements from contracts, portals, and imports.

    GUARDRAILS:
    - Risk Level: R2 (requires approval for entitlement creation)
    - Cannot auto-write entitlements
    - Must produce draft for human review
    - Must log all extraction attempts
    """

    async def execute(self, input_data: ExtractorInput) -> ExtractorOutput:
        # 1. Validate input (contract doc, portal export, API data)
        # 2. Extract SKU, quantities, dates, terms
        # 3. Produce draft entitlements with discrepancies
        # 4. Generate evidence pack
        # 5. Submit for approval
        pass

# backend/apps/license_management/agents/optimization_advisor.py
class OptimizationAdvisorAgent(BaseAgent):
    """
    Recommends license optimization actions.

    GUARDRAILS:
    - Risk Level: R2 (recommend only)
    - Cannot execute reclaim/reassign/purchase
    - Must provide savings estimate with evidence
    - Requires approval for any action
    """

    async def execute(self, input_data: AdvisorInput) -> AdvisorOutput:
        # 1. Analyze utilization patterns
        # 2. Identify unused assignments
        # 3. Detect inactive devices/users
        # 4. Check renewal dates
        # 5. Produce ranked recommendations
        # 6. Include expected savings and evidence
        pass
```

#### 4.24 Application Portfolio Data Model

```python
# backend/apps/portfolio/models.py
class Application(TimeStampedModel):
    """Normalized application entity."""
    canonical_name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    criticality = models.CharField(max_length=20)  # critical, high, medium, low
    lifecycle_status = models.CharField(max_length=20)  # active, deprecated, eol
    business_owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    technical_owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='technical_owned_apps'
    )

class ApplicationVersion(TimeStampedModel):
    """Tracked version of an application."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    version = models.CharField(max_length=100)
    release_date = models.DateField(null=True)
    end_of_support = models.DateField(null=True)
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True)
    vulnerabilities = models.JSONField(default=list)

class ApplicationLicenseAssociation(TimeStampedModel):
    """Links applications to license SKUs."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    license_sku = models.ForeignKey('license_management.LicenseSKU', on_delete=models.CASCADE)
    association_type = models.CharField(max_length=20)  # required, optional, bundled
    evidence = models.JSONField(default=dict)

class ApplicationDependency(TimeStampedModel):
    """Dependency between applications."""
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='dependencies'
    )
    depends_on = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='dependents'
    )
    dependency_type = models.CharField(max_length=20)  # runtime, build, optional
    inferred = models.BooleanField(default=False)
    confidence = models.FloatField(null=True)
    evidence = models.JSONField(default=dict)

class PortfolioRiskScore(TimeStampedModel):
    """Risk score for an application in portfolio."""
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    score = models.FloatField()  # 0-100
    factors = models.JSONField()  # Individual factor contributions
    computed_at = models.DateTimeField(auto_now_add=True)
```

#### 4.25 Quality Gates

- [ ] All license AI agents execute through guardrail framework
- [ ] Optimization recommendations are evidence-backed
- [ ] Application catalog deduplicates across sources
- [ ] License-app associations are auditable
- [ ] Dependency graph queryable
- [ ] ≥90% test coverage
- [ ] No auto-actions without approval

---

### Phase P10: User & Admin Management

**Duration**: 2 weeks
**Priority**: HIGH
**Dependencies**: P6 (AD Connector)

#### 4.26 Objectives

Implement comprehensive user management with admin capabilities and future AD integration support.

#### 4.27 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D10.1** User Management UI | Create, edit, deactivate users | Admin-only access |
| **D10.2** Role Management | RBAC role assignment | Predefined + custom roles |
| **D10.3** Group Management | User grouping for permissions | Hierarchical groups |
| **D10.4** AD Sync Foundation | Sync users/groups from AD | Scheduled + on-demand |
| **D10.5** Session Management | Active session tracking | Force logout capability |
| **D10.6** Audit Dashboard | User action audit trail | Filterable, exportable |
| **D10.7** Password Policies | Complexity, expiry, history | Configurable policies |

#### 4.28 Data Model Enhancements

```python
# backend/apps/authentication/models.py (enhancements)
class UserProfile(TimeStampedModel):
    """Extended user profile."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='direct_reports'
    )
    ad_object_id = models.CharField(max_length=100, blank=True)
    ad_synced_at = models.DateTimeField(null=True)

class Role(TimeStampedModel):
    """RBAC role definition."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField()  # List of permission strings
    is_system = models.BooleanField(default=False)  # System roles cannot be deleted

    class Meta:
        ordering = ['name']

class Group(TimeStampedModel):
    """User group with hierarchical structure."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        related_name='children'
    )
    roles = models.ManyToManyField(Role, blank=True)
    ad_group_id = models.CharField(max_length=100, blank=True)

class UserSession(TimeStampedModel):
    """Active user session tracking."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

#### 4.29 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/` | GET, POST | User CRUD (admin only) |
| `/api/users/{id}/` | GET, PUT, DELETE | User detail |
| `/api/users/{id}/deactivate/` | POST | Deactivate user |
| `/api/users/{id}/sessions/` | GET | User sessions |
| `/api/users/{id}/sessions/revoke/` | POST | Revoke all sessions |
| `/api/roles/` | GET, POST | Role CRUD |
| `/api/groups/` | GET, POST | Group CRUD |
| `/api/groups/{id}/members/` | GET, POST, DELETE | Group membership |
| `/api/ad-sync/` | POST | Trigger AD sync |
| `/api/ad-sync/status/` | GET | AD sync status |

#### 4.30 Quality Gates

- [ ] Admin-only access for user management
- [ ] Session management with force logout
- [ ] Audit trail for all user changes
- [ ] AD sync foundation testable
- [ ] Password policies enforceable
- [ ] ≥90% test coverage

---

### Phase P11: Enterprise Hardening

**Duration**: 2 weeks
**Priority**: HIGH
**Dependencies**: P6-P10 code-complete

#### 4.31 Objectives

Harden the platform for enterprise production deployment with HA/DR, security, and operational readiness.

#### 4.32 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D11.1** HA/DR Documentation | Topology, RPO/RTO, failover procedures | RPO ≤24h, RTO ≤8h |
| **D11.2** Secrets Management | Vault integration or K8s secrets | No hardcoded secrets |
| **D11.3** mTLS Service Mesh | Service-to-service encryption | All internal traffic encrypted |
| **D11.4** SBOM Generation Pipeline | Automated SBOM for all releases | SPDX format, CI integration |
| **D11.5** Vulnerability Scanning | Trivy/Grype in CI pipeline | Zero critical/high CVEs |
| **D11.6** Backup/Restore Procedures | PostgreSQL PITR, MinIO replication | Tested restore procedures |
| **D11.7** Break-Glass Procedures | Emergency access documentation | Audited, time-limited |
| **D11.8** Performance Benchmarks | Load testing results | 100k devices validated |

#### 4.33 Quality Gates

- [ ] Zero critical/high CVEs in production image
- [ ] SBOM generated for all components
- [ ] Backup/restore tested and documented
- [ ] mTLS enabled for all internal services
- [ ] Secrets rotatable without downtime
- [ ] Load test validates 100k device scale

---

### Phase P12: Production Certification

**Duration**: 2 weeks
**Priority**: CRITICAL
**Dependencies**: P11 complete

#### 4.34 Objectives

Final production certification with comprehensive testing, documentation, and operational readiness.

#### 4.35 Deliverables

| Deliverable | Description | Acceptance Criteria |
|-------------|-------------|---------------------|
| **D12.1** E2E Test Suite | Full workflow coverage | All critical paths tested |
| **D12.2** Security Audit | Penetration testing results | No critical findings |
| **D12.3** Compliance Evidence | GDPR, SOC2, DPDP alignment | Audit-ready evidence |
| **D12.4** Operational Runbooks | Complete runbook set | All failure scenarios covered |
| **D12.5** Training Materials | Admin and user guides | Role-based documentation |
| **D12.6** Production Checklist | Go-live verification | All items checked |
| **D12.7** Monitoring Dashboards | Production-ready Grafana | SLO tracking enabled |
| **D12.8** Incident Response Plan | Escalation procedures | Tested procedures |

#### 4.36 Quality Gates

- [ ] All E2E tests pass
- [ ] Security audit completed with remediation
- [ ] Compliance evidence package complete
- [ ] Runbooks reviewed and tested
- [ ] Training materials approved
- [ ] Production checklist 100% complete

---

## 5. Test Coverage Requirements

### Overall Coverage Targets

| Component | Current | Target | Gap |
|-----------|---------|--------|-----|
| Backend | 70.98% | 90% | 19.02% |
| Frontend | ~60% | 80% | ~20% |

### Per-Phase Coverage Requirements

| Phase | Unit Tests | Integration Tests | E2E Tests |
|-------|------------|-------------------|-----------|
| P6 | ≥90% | ≥80% | ≥70% |
| P7 | ≥90% | ≥80% | ≥70% |
| P8 | ≥90% | ≥85% | ≥75% |
| P9 | ≥90% | ≥80% | ≥70% |
| P10 | ≥90% | ≥80% | ≥70% |
| P11 | ≥90% | ≥85% | ≥80% |
| P12 | ≥90% | ≥90% | ≥90% |

---

## 6. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **92 untracked files in git** | CONFIRMED | CRITICAL | Commit immediately before any work |
| **SCCM/Landscape/Ansible vaporware** | CONFIRMED | CRITICAL | Build from scratch; 300+ hours |
| Test coverage gap delays phase completion | HIGH | MEDIUM | Dedicated test writing sprints |
| Connector API changes break integration | MEDIUM | HIGH | Version pinning, integration tests |
| License data model complexity | MEDIUM | MEDIUM | Incremental delivery, early validation |
| AI agent guardrail gaps | LOW | CRITICAL | Security review before deployment |
| AD integration complexity | MEDIUM | MEDIUM | Phased approach, fallback to local auth |
| Performance at 100k scale | LOW | HIGH | Load testing in P11 |

> **IMMEDIATE ACTION REQUIRED**: Before any feature work begins, commit the 92 untracked files to git. See [BLOCKING-ISSUES-TRACKER.md](./BLOCKING-ISSUES-TRACKER.md) BLOCK-007.

---

## 7. Definition of Done (Global)

For any phase to be marked COMPLETE:

1. **Code Quality**
   - [ ] All tests pass
   - [ ] Coverage ≥90% for new code
   - [ ] Zero TypeScript errors
   - [ ] Zero ESLint warnings
   - [ ] Pre-commit hooks pass

2. **Documentation**
   - [ ] API documentation updated
   - [ ] Architecture decisions documented
   - [ ] Runbooks updated (if operational changes)

3. **Security**
   - [ ] No hardcoded secrets
   - [ ] RBAC verified
   - [ ] Audit logging verified

4. **Review**
   - [ ] Code review completed
   - [ ] Architecture review (if significant changes)

---

## 8. Appendices

### Appendix A: Customer Requirement Cross-Reference

See [docs/customer-requirements/](../customer-requirements/) for full requirement documents:
- Product Requirements Document (PRD).md
- TECHNICAL ARCHITECTURE SPECIFICATION.md
- License-management.md
- Application-Portfolio-compliance.md
- AI Governance & Compliance Blueprint.md
- Data & Telemetry Architecture.md
- Platform Operating Model (Runbook, AIOps, SRE).md

### Appendix B: Previous Phase Reports

See [reports/](../../reports/) for detailed completion reports of P1-P5.3.

### Appendix C: Architecture Documentation

See [docs/architecture/](../architecture/) for system architecture documentation.

---

**Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Jan 25, 2026 | Platform Engineering Agent | Initial creation |
| 2.0.0 | Jan 25, 2026 | Platform Engineering Agent | Full phase specifications |

---

*This document is the authoritative source for EUCORA production implementation planning. All previous planning documents in docs/planning/old/ are superseded.*
