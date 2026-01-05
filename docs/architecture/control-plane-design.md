# Control Plane Design

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-04

---

## Overview

The Control Plane is the **thin orchestration layer** that acts as the system-of-record for **policy intents, approvals, and evidence**. It does NOT replace Intune/Jamf/SCCM/Landscape/Ansible — those remain as execution planes. The Control Plane enforces governance, orchestrates deployments, and maintains audit trails.

**Design Principle**: Thin control plane — policy and orchestration only; no duplication of MDM features.

---

## Architecture

### Logical Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Control Plane                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ API Gateway  │  │ Policy Engine│  │ Orchestrator │    │
│  │  + Auth      │  │              │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                  │             │
│  ┌──────▼─────────────────▼──────────────────▼───────┐    │
│  │           Workflow / CAB Module                    │    │
│  └──────┬─────────────────────────────────────────────┘    │
│         │                                                   │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Evidence     │  │ Event Store  │  │ Execution    │    │
│  │ Store        │  │ (Immutable)  │  │ Plane        │    │
│  │ (Immutable)  │  │              │  │ Connectors   │    │
│  └──────────────┘  └──────────────┘  └──────┬───────┘    │
└─────────────────────────────────────────────┼─────────────┘
                                              │
                    ┌─────────────────────────▼─────────────┐
                    │      Execution Planes                 │
                    │  Intune | Jamf | SCCM | Landscape     │
                    └────────────────────────────────────────┘
```

---

## Component Specifications

### 1. API Gateway + Auth

**Purpose**: Single entry point for all Control Plane operations with authentication and authorization.

**Requirements**:
- Entra ID authentication (OAuth 2.0 / OpenID Connect)
- Certificate-based authentication for service principals
- Scoped RBAC enforcement (see [RBAC Configuration](../infrastructure/rbac-configuration.md))
- Rate limiting and throttling
- API versioning (`/api/v1/...`)
- Request correlation id generation (UUIDv4)

**Technology Options**:
- Azure API Management (cloud-native, Entra ID integration)
- Kong / Tyk (self-hosted, flexible)
- Custom FastAPI/Go service with Entra ID middleware

**Authentication Flow**:
```
Client → API Gateway → Entra ID Token Validation → RBAC Check → Backend Service
```

**RBAC Scopes**:
- `control-plane.admin` - Platform Admin full access
- `control-plane.packaging` - Packaging Engineer (read-only for production, write for staging)
- `control-plane.publisher` - Publisher (scoped by BU/acquisition boundary)
- `control-plane.cab-approver` - CAB Approver (evidence pack read, approval write)
- `control-plane.security-reviewer` - Security Reviewer (SBOM/scan policy, exception approval)
- `control-plane.endpoint-ops` - Endpoint Operations (telemetry read, remediation write)
- `control-plane.auditor` - Auditor (read-only for events and evidence)

---

### 2. Policy Engine

**Purpose**: Evaluates entitlements, risk scoring, gates, and constraints before any deployment action.

**Responsibilities**:
- Identity & entitlement resolution (groups, acquisition boundaries, device conditions)
- Risk score computation from weighted factors (see [Risk Model](risk-model.md))
- Promotion gate evaluation (success rate, time-to-compliance, incident thresholds)
- Scope validation (`target_scope ⊆ publisher_scope` and `target_scope ⊆ app_scope`)
- CAB approval enforcement (block Ring 2+ for `Risk > 50` or privileged tooling)

**Policy Evaluation Flow**:
```
Deployment Intent → Risk Assessment → Scope Validation → CAB Check → Promotion Gates → Policy Decision (Allow/Deny/Require Approval)
```

**Policy Decision Outcomes**:
- `ALLOW` - Proceed with deployment
- `DENY` - Block deployment (policy violation)
- `REQUIRE_APPROVAL` - Block until CAB approval obtained
- `REQUIRE_EXCEPTION` - Block until exception approved (e.g., High/Critical CVE)

**Risk Score Computation**:
```python
def compute_risk_score(artifact, deployment_intent, risk_model_version="v1.0"):
    """
    Computes risk score from weighted factors using versioned rubric.

    Returns:
        {
            "risk_score": 0-100,
            "risk_model_version": "v1.0",
            "factors": [
                {"name": "privilege_impact", "normalized_value": 1.0, "weight": 20, "contribution": 20},
                {"name": "supply_chain_trust", "normalized_value": 0.1, "weight": 15, "contribution": 1.5},
                # ... other factors
            ],
            "threshold": "CAB_REQUIRED" | "AUTOMATED_ALLOWED"
        }
    """
    pass
```

---

### 3. Orchestrator

**Purpose**: Creates deployment intents, schedules actions, manages ring progression — never executes directly on endpoints.

**Responsibilities**:
- Deployment Intent creation with correlation ids
- Ring-based rollout scheduling (Lab → Canary → Pilot → Department → Global)
- Promotion gate evaluation coordination
- Rollback orchestration (plane-specific strategies)
- Retry logic with exponential backoff for transient failures

**Deployment Intent Schema**:
```json
{
  "intent_id": "uuid-v4",
  "correlation_id": "uuid-v4",
  "application_id": "app-001",
  "version": "2.1.0",
  "artifact_hash": "sha256:...",
  "target_scope": {
    "acquisition_boundary": "acq-001",
    "business_unit": "bu-finance",
    "site_class": "online",
    "rings": ["ring-1-canary"]
  },
  "publisher_scope": {
    "acquisition_boundary": "acq-001",
    "business_unit": "bu-finance"
  },
  "schedule": {
    "ring-1-canary": {"start": "2026-01-05T00:00:00Z", "duration_hours": 24},
    "ring-2-pilot": {"start": "2026-01-06T00:00:00Z", "duration_hours": 48},
    "ring-3-department": {"start": "2026-01-08T00:00:00Z", "duration_hours": 72},
    "ring-4-global": {"start": "2026-01-11T00:00:00Z", "duration_hours": 168}
  },
  "promotion_gates": {
    "success_rate_threshold": 0.98,
    "time_to_compliance_hours": 24,
    "max_incidents": 0
  },
  "rollback_plan": {
    "strategy": "intune-supersedence",
    "rollback_version": "2.0.5",
    "validated": true,
    "validation_date": "2026-01-04T12:00:00Z"
  },
  "evidence_pack_id": "evidence-uuid",
  "cab_approval_id": "approval-uuid",
  "risk_score": 45,
  "created_at": "2026-01-04T10:00:00Z",
  "created_by": "publisher@example.com",
  "status": "in_progress"
}
```

**State Machine**:
```
pending → risk_assessed → scope_validated → cab_approved (if required) → ring_1_in_progress → ring_1_completed → ring_2_in_progress → ... → completed | failed | rolled_back
```

---

### 4. Workflow / CAB Module

**Purpose**: Manages approval states, exception handling, and evidence requirements.

**Responsibilities**:
- CAB submission workflow (evidence pack completeness check)
- Approval routing (assign to CAB approvers based on BU/acquisition boundary)
- Exception tracking (expiry dates, compensating controls, Security Reviewer approval)
- Approval audit trail (immutable event store)

**CAB Approval Record Schema**:
```json
{
  "approval_id": "uuid-v4",
  "deployment_intent_id": "intent-uuid",
  "evidence_pack_id": "evidence-uuid",
  "risk_score": 65,
  "submitted_at": "2026-01-04T10:00:00Z",
  "submitted_by": "packaging-eng@example.com",
  "assigned_to": ["cab-approver-1@example.com", "cab-approver-2@example.com"],
  "decision": "approved" | "denied" | "pending",
  "decided_at": "2026-01-04T14:00:00Z",
  "decided_by": "cab-approver-1@example.com",
  "conditions": [
    "Limit to Ring 2 (Pilot) for 7 days before Ring 3 promotion",
    "Additional monitoring via SIEM for privilege escalation events"
  ],
  "expiry": "2026-02-04T14:00:00Z",
  "justification": "High privilege impact due to admin elevation requirement. Compensating controls: SIEM monitoring, Ring 2 extended soak period.",
  "event_id": "event-uuid"
}
```

**Exception Record Schema**:
```json
{
  "exception_id": "uuid-v4",
  "artifact_id": "artifact-uuid",
  "exception_type": "vulnerability" | "unsigned_package" | "scope_violation",
  "severity": "high",
  "details": "CVE-2025-12345 (High) present in dependency libfoo 1.2.3",
  "compensating_controls": [
    "Network segmentation prevents exploit vector",
    "Additional EDR monitoring enabled",
    "Vendor patch expected within 14 days"
  ],
  "approved_by": "security-reviewer@example.com",
  "approved_at": "2026-01-04T12:00:00Z",
  "expiry": "2026-01-18T23:59:59Z",
  "owner": "packaging-eng@example.com",
  "event_id": "event-uuid"
}
```

---

### 5. Execution Plane Connectors

**Purpose**: Idempotent adapters to Intune/Jamf/SCCM/Landscape/Ansible with audit correlation.

**Connector Interface** (abstract):
```python
class ExecutionPlaneConnector(ABC):
    """Base interface for all execution plane connectors."""

    @abstractmethod
    async def publish(self, deployment_intent: DeploymentIntent) -> PublishResult:
        """
        Publish app/package and assignments to execution plane.
        MUST be idempotent (use correlation_id as idempotent key).
        """
        pass

    @abstractmethod
    async def query_status(self, deployment_intent_id: str) -> DeploymentStatus:
        """
        Query current deployment status from execution plane.
        """
        pass

    @abstractmethod
    async def remediate(self, deployment_intent_id: str, action: str) -> RemediationResult:
        """
        Execute remediation action (uninstall/rollback/redeploy/ring pinning).
        MUST be idempotent.
        """
        pass

    @abstractmethod
    async def verify_idempotency(self, correlation_id: str) -> bool:
        """
        Check if deployment with correlation_id already exists.
        """
        pass
```

**Connector Implementations**:
- [Intune Connector](../modules/intune/connector-spec.md)
- [Jamf Pro Connector](../modules/jamf/connector-spec.md)
- [SCCM Connector](../modules/sccm/connector-spec.md)
- [Landscape Connector](../modules/landscape/connector-spec.md)
- [Ansible Connector](../modules/ansible/connector-spec.md)

**Error Classification**:
```python
class ConnectorError(Exception):
    ERROR_TYPES = {
        "TRANSIENT": ["rate_limit", "timeout", "service_unavailable"],
        "PERMANENT": ["invalid_credentials", "resource_not_found", "invalid_request"],
        "POLICY_VIOLATION": ["scope_violation", "unauthorized", "quota_exceeded"]
    }

    def __init__(self, error_type: str, message: str, details: dict):
        self.error_type = error_type  # TRANSIENT | PERMANENT | POLICY_VIOLATION
        self.message = message
        self.details = details
        self.retry_after = details.get("retry_after_seconds")
```

---

### 6. Evidence Store

**Purpose**: Immutable storage for evidence packs (object store/WORM capable).

**Requirements**:
- Immutable writes (WORM - Write Once Read Many)
- Versioning support (evidence pack v1.0, v1.1, etc.)
- Retention policy aligned to compliance requirements (e.g., 7 years)
- Hash verification on read (integrity check)
- Access control (read: CAB Approvers + Auditors; write: Control Plane only)

**Technology Options**:
- Azure Blob Storage with immutability policies
- AWS S3 with Object Lock
- MinIO with WORM mode

**Evidence Pack Schema**: See [Evidence Pack Schema](evidence-pack-schema.md)

---

### 7. Event Store

**Purpose**: Append-only deployment events for immutable audit trail.

**Requirements**:
- Append-only (no updates or deletes)
- Correlation id indexing for audit trail reconstruction
- SIEM integration for privileged actions and policy violations
- Retention policy aligned to compliance requirements
- Query performance for audit reports

**Technology Options**:
- Event sourcing database (EventStoreDB, Apache Kafka)
- Append-only table in PostgreSQL with immutability constraints
- Azure Event Hubs with capture to ADLS

**Deployment Event Schema**:
```json
{
  "event_id": "uuid-v4",
  "correlation_id": "uuid-v4",
  "event_type": "deployment_started" | "deployment_completed" | "deployment_failed" | "rollback_executed" | "cab_approved" | "exception_granted",
  "timestamp": "2026-01-04T10:00:00Z",
  "actor": "publisher@example.com",
  "actor_role": "Publisher",
  "deployment_intent_id": "intent-uuid",
  "execution_plane": "intune" | "jamf" | "sccm" | "landscape" | "ansible",
  "ring": "ring-1-canary",
  "outcome": "success" | "failure" | "pending",
  "details": {
    "artifact_id": "artifact-uuid",
    "target_devices": 250,
    "successful_installs": 245,
    "failed_installs": 5,
    "failure_reasons": {"timeout": 3, "dependency_missing": 2}
  },
  "metadata": {
    "ip_address": "10.0.1.100",
    "user_agent": "ControlPlane/1.0",
    "session_id": "session-uuid"
  }
}
```

---

### 8. Telemetry + Reporting

**Purpose**: Success rate, time-to-compliance, failure reasons, rollback execution metrics.

**Metrics** (minimum):
- **Success Rate**: `successful_installs / total_target_devices` per ring
- **Time-to-Compliance**: `time_to_first_successful_install` per ring per site class
- **Failure Rate**: `failed_installs / total_target_devices` per ring
- **Rollback Execution Count**: Number of rollbacks executed per app per time period
- **CAB Approval Time**: `decided_at - submitted_at` (average, p50, p95, p99)
- **Drift Detection Count**: Number of drift events per app per time period
- **Remediation Success Rate**: `successful_remediations / total_remediations`

**Dashboards**:
- Ring Rollout Health (per app, per ring)
- CAB Approval Pipeline (pending count, average approval time)
- Execution Plane Health (connector success rate, error types)
- Drift Detection & Remediation (drift events, remediation success rate)

**Technology Options**:
- Prometheus + Grafana (metrics + dashboards)
- Azure Monitor + Application Insights
- Datadog / New Relic

---

## Data Model (System-of-Record Objects)

### Core Entities

1. **Application**: Canonical identity, owner, category/class, support tier, licensing model
2. **Application Version**: Semantic version, release notes, supported OS matrix, dependencies
3. **Artifact**: Package binaries + hashes + signatures + provenance
4. **Entitlement Rule**: Target groups/conditions (user/device), exclusions, acquisition boundaries, posture constraints
5. **Deployment Intent**: Desired state for a scope (ring, schedule, constraints, required evidence)
6. **Approval Record**: Approver, decision, conditions, expiry, exception link
7. **Risk Assessment**: Inputs + computed score + threshold + justification
8. **Deployment Event**: Append-only events with correlation id, actor, time, plane, outcome

**Entity Relationship Diagram**:
```
Application (1) ─── (N) ApplicationVersion
ApplicationVersion (1) ─── (N) Artifact
ApplicationVersion (1) ─── (N) DeploymentIntent
DeploymentIntent (1) ─── (1) RiskAssessment
DeploymentIntent (1) ─── (0..1) ApprovalRecord
DeploymentIntent (1) ─── (1) EvidencePack
DeploymentIntent (1) ─── (N) DeploymentEvent
Artifact (1) ─── (N) Exception
```

---

## Tenant and Segmentation Model

**Single enterprise tenant** with segmentation by:
- Acquisition boundary (e.g., `acq-001`, `acq-002`)
- Business unit (e.g., `bu-finance`, `bu-hr`, `bu-it`)
- Geography/site (e.g., `geo-us-east`, `geo-emea-london`)

**Isolation Enforcement**:
- RBAC scopes (Publisher role scoped to `acq-001` + `bu-finance`)
- Policy constraints: `target_scope ⊆ publisher_scope` and `target_scope ⊆ app_scope`
- Mandatory scope declaration on every Deployment Intent
- Scope immutability: changes require CAB approval and versioning

**Segmentation Guardrails** (hard controls enforced by Policy Engine):
- **Default deny** for cross-boundary publishing and targeting
- **Mandatory scope declaration** on every Deployment Intent (acquisition boundary, BU, site scope)
- **Subset validation**: `target_scope ⊆ publisher_scope` and `target_scope ⊆ app_scope`
- **Scope immutability**: Changes to an app's allowed scope require CAB approval and are versioned
- **CAB evidence includes scope diff** (previous scope → requested scope) and explicit blast-radius summary

**Example Scope Validation**:
```python
def validate_scope(deployment_intent: DeploymentIntent, publisher: User):
    """Validate scope boundaries before deployment."""
    target_scope = deployment_intent.target_scope
    publisher_scope = publisher.allowed_scope
    app_scope = deployment_intent.application.allowed_scope

    # Check 1: target_scope ⊆ publisher_scope
    if not is_subset(target_scope, publisher_scope):
        raise PolicyViolation("Target scope exceeds publisher scope")

    # Check 2: target_scope ⊆ app_scope
    if not is_subset(target_scope, app_scope):
        raise PolicyViolation("Target scope exceeds app scope")

    # Check 3: CAB approval required for scope changes
    if app_scope != app_scope_previous and not cab_approved:
        raise PolicyViolation("Scope change requires CAB approval")
```

---

## Idempotency, Concurrency, and Reconciliation

### Idempotency

**Intent is declarative**: What version should be present in ring X for scope Y.

**Connectors are idempotent**: Retries must not duplicate assignments or corrupt state.
- Use `correlation_id` as idempotent key
- Check for existing deployment with same `correlation_id` before creating new one
- Update existing deployment if found, create new if not found

**Deployment intents are retryable**: Same intent can be resubmitted without side effects.

### Concurrency Rules

**Per-app/per-ring "one active change at a time"** unless explicitly approved by CAB.
- Use database row-level locking on `DeploymentIntent` table
- Check for active deployments: `SELECT * FROM deployment_intents WHERE app_id = ? AND ring = ? AND status IN ('in_progress', 'pending') FOR UPDATE`
- If active deployment exists, block new deployment submission

### Reconciliation Loop

**Periodically read execution plane state, compare to desired intent, emit drift events, trigger remediation workflows.**

**Reconciliation Algorithm**:
```
LOOP every 1 hour (configurable):
  FOR EACH deployment_intent WHERE status = 'completed':
    actual_state = connector.query_status(deployment_intent.id)
    desired_state = deployment_intent.target_state

    IF actual_state != desired_state:
      EMIT drift_event(deployment_intent, actual_state, desired_state)

      IF remediation_policy = 'auto' AND within_policy:
        connector.remediate(deployment_intent.id, action='reconcile')
      ELSE:
        CREATE remediation_ticket(deployment_intent, drift_details)
```

**Drift Event Schema**:
```json
{
  "event_id": "uuid-v4",
  "event_type": "drift_detected",
  "deployment_intent_id": "intent-uuid",
  "timestamp": "2026-01-04T15:00:00Z",
  "drift_type": "assignment_missing" | "version_mismatch" | "scope_mismatch",
  "desired_state": {"version": "2.1.0", "assigned_devices": 250},
  "actual_state": {"version": "2.0.5", "assigned_devices": 200},
  "remediation_action": "auto" | "manual_ticket",
  "remediation_result": "pending" | "success" | "failed"
}
```

---

## Failure Modes + HA/DR

### Failure Impact Matrix

| Failure | Impact | Control Plane Behavior | Mitigation |
|---|---|---|---|
| Control Plane unavailable | No new changes can be approved/published | Pause new deployments/promotions; emit incident | Restore HA; DR failover if required |
| Database unavailable | System-of-record read/write fails | Block publish and approvals; existing deployments unaffected | DB HA/failover; DR restore |
| Evidence store unavailable | Evidence packs cannot be written/read | **Publish blocked** (no evidence); promotions paused | Object store redundancy; retry/backoff |
| Intune Graph degraded/unavailable | Connector cannot publish/query reliably | Backoff/retry; promotions paused; reconcile later | Throttling/backoff; manual CAB pause if prolonged |
| Jamf API degraded/unavailable | Jamf publish/query impacted | Backoff/retry; Jamf promotions paused | Retry with idempotent keys |
| SCCM site server unavailable | SCCM publish/query impacted | SCCM promotions paused | Local DP content remains usable; restore site server |

### HA Requirements

**Target availability**: **99.9%** for the Control Plane (or enterprise standard, whichever is higher).

**HA Design**:
- Stateless services behind load balancers (API Gateway, Orchestrator)
- HA database (managed or clustered) for the system-of-record (PostgreSQL with replication, Azure SQL with failover groups)
- Redundant object storage for evidence packs/artifacts (geo-redundant replication)
- Redis cluster for session state and caching

### DR Requirements

**Minimum expectation**: **RPO ≤ 24h** and **RTO ≤ 8h** (or enterprise standard, whichever is stricter).

**DR Strategy**:
- Continuous replication of database to secondary region
- Evidence pack storage with geo-redundant replication
- Audit logs and events replicated per compliance requirements
- DR runbook with failover procedures (see [Runbooks](../runbooks/))

---

## Technology Stack Recommendations

### Option 1: Cloud-Native (Azure)

| Component | Technology |
|---|---|
| API Gateway + Auth | Azure API Management + Entra ID |
| Policy Engine | Custom service (Python/FastAPI or Go) |
| Orchestrator | Azure Durable Functions or custom service |
| Workflow / CAB Module | Power Automate + custom service |
| Evidence Store | Azure Blob Storage with immutability policies |
| Event Store | Azure Event Hubs with capture to ADLS |
| Database | Azure SQL with failover groups |
| Telemetry | Azure Monitor + Application Insights |

### Option 2: Hybrid (Self-Hosted + Cloud)

| Component | Technology |
|---|---|
| API Gateway + Auth | Kong + Entra ID integration |
| Policy Engine | Custom service (Python/FastAPI or Go) |
| Orchestrator | Temporal.io or custom service |
| Workflow / CAB Module | Custom service with workflow engine |
| Evidence Store | MinIO with WORM mode |
| Event Store | EventStoreDB or PostgreSQL append-only |
| Database | PostgreSQL with replication |
| Telemetry | Prometheus + Grafana |

---

## Next Steps

1. Finalize technology stack selection (cloud-native vs hybrid)
2. Design API specifications (OpenAPI/Swagger) in `docs/api/`
3. Implement connector interface and first connector (Intune) in Phase 1
4. Set up HA/DR infrastructure (see [HA/DR Requirements](../infrastructure/ha-dr-requirements.md))
5. Configure RBAC in Entra ID (see [RBAC Configuration](../infrastructure/rbac-configuration.md))

---

## Related Documentation

- [Architecture Overview](architecture-overview.md)
- [Risk Model](risk-model.md)
- [Evidence Pack Schema](evidence-pack-schema.md)
- [Execution Plane Connectors](execution-plane-connectors.md)
- [HA/DR Requirements](../infrastructure/ha-dr-requirements.md)
- [RBAC Configuration](../infrastructure/rbac-configuration.md)
