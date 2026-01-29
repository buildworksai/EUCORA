# EUCORA — License Management with AI Agents (Customer Requirement Spec)

## 1) Context & Drivers
EUCORA is a **thin control plane** that standardizes governance, evidence, and determinism across endpoint execution tools (Intune/Jamf/SCCM/etc.). The platform’s principles explicitly include **determinism**, **reconciliation loops**, and **evidence-first governance**. :contentReference[oaicite:0]{index=0}

This requirement adds **comprehensive license management** with AI Agents such that:
- License inventory is always accurate (as accurate as source systems allow)
- **Available / Consumed / Remaining** is visible continuously
- Consumption truth is driven by **reconciliation**, not assumptions
- Every automated agent action is **auditable** and **approval-governed** (where applicable)

---

## 2) Goals (Must-Have Outcomes)
### G1 — Comprehensive License Management
Implement a full license lifecycle system covering:
- Vendor/SKU catalog
- Entitlements (purchased/contracted licenses)
- Allocation pools and assignments
- Consumption discovery (installed/assigned/active usage)
- Reconciliation + snapshots + audit trail
- Alerts, thresholds, and compliance reporting

### G2 — AI Agent-Driven License Intelligence
Add agent workflows that can:
- Review and extract **available, consumed, remaining**
- Explain *why* the numbers changed
- Detect anomalies (sudden spikes, drift, duplicate counting)
- Recommend optimization actions (reclaim, reassign, purchase)

### G3 — “Always True” License Consumption in Sidebar
The **sidebar** must show continuously updated license consumption:
- Available / Consumed / Remaining (overall + optionally per key vendor/SKU)
- Timestamp: “last reconciled at”
- Health indicator: OK / Delayed / Source degraded / Reconciliation failed
- Clicking opens License Dashboard (details + drilldowns)

> “Always true” here means: the sidebar displays the **latest reconciled truth**, not random cached estimates. If reconciliation is delayed, sidebar must show the delay explicitly.

---

## 3) Non-Goals (Explicit Exclusions)
- Building a full procurement/ERP module (PO approvals, invoicing, etc.)
- Replacing vendor licensing portals (we ingest from them)
- “AI decides purchases automatically” (recommendations only unless explicitly approved workflow exists)

---

## 4) Definitions (Non-Negotiable Semantics)
### 4.1 Core Counters
For a given SKU (or pool):
- **Available** = Entitled - Reserved - Consumed (depending on license type rules)
- **Consumed** = Count of active consumption units after reconciliation
- **Remaining** = Entitled - Consumed - Reserved

### 4.2 Consumption Unit
Consumption unit depends on license model:
- Device-based (per device)
- User-based (per user)
- Concurrent (peak concurrent usage window)
- Subscription seats (assigned seats)
- Feature add-ons (per feature)

**Requirement:** The system must support **license model type** per SKU and compute counters accordingly.

### 4.3 “Truth Source” & Reconciliation
- **Truth = Reconciled Snapshot**
- Reconciliation is a deterministic job that:
  1) Pulls raw usage/assignment signals
  2) Normalizes into consumption units
  3) De-duplicates across sources
  4) Produces an immutable snapshot with evidence

---

## 5) Personas & Access Control (RBAC)
### Roles
- **License Admin**: configure vendors/SKUs, entitlements, integrations
- **License Auditor**: view all; export evidence packs; run audits
- **Ops Manager**: view dashboards, alerts, recommendations; approve actions
- **Agent Operator**: can trigger agent workflows within bounded permissions
- **Read-Only Viewer**: dashboard + sidebar view only

### RBAC Requirements
- All writes require explicit roles (no “everyone can edit” shortcuts)
- Agents operate under **delegated authority** of a role, not god-mode
- Every agent action must record:
  - actor = agent + delegated user context
  - inputs, outputs, decision trace
  - approvals (if required)

---

## 6) Data Sources & Integrations (Inputs)
### Required Integration Inputs
- **MDM/Endpoint systems**: Intune, Jamf, SCCM (as applicable)
- **Directory**: AD/Azure AD/IdP (users/devices)
- **Vendor licensing portals/APIs** (where available) OR import files
- Optional: EDR/CMDB for enrichment

### Import Modes
- API-based scheduled pulls
- File import (CSV/JSON) with schema validation
- Manual entry (restricted; must be auditable)

---

## 7) Data Model (Minimum Entities)
### 7.1 Master Data
- `Vendor` (name, identifiers, support contacts)
- `LicenseSKU` (vendor, sku_code, license_model_type, unit_rules, normalization rules)

### 7.2 Entitlements & Contracts
- `Entitlement` (sku, contract_id, start/end, entitled_quantity, terms, documents, renewal)
- `LicensePool` (sku, scope: global/region/bu, entitled_quantity_override?, reserved_quantity)

### 7.3 Assignments & Consumption
- `Assignment` (pool, principal_type: user/device, principal_id, assigned_at, status)
- `ConsumptionSignal` (source_system, raw_id, timestamp, principal, sku, confidence, raw_payload_hash)
- `ConsumptionUnit` (normalized unit; de-duplicated; references signals)
- `ConsumptionSnapshot` (immutable; sku/pool counters; reconciled_at; evidence_pack_hash)

### 7.4 Jobs, Evidence, Audit
- `ImportJob` (source, status, counts, failures, hash of input)
- `ReconciliationRun` (status, ruleset_version, diffs, snapshot_ids)
- `EvidencePack` (artifacts: import logs, diffs, ruleset, hashes)
- `AuditLog` (actor, action, entity, before/after, correlation_id)

---

## 8) AI Agent Suite (Workflows + Boundaries)
EUCORA already positions “AI Agent Hub” but with deterministic governance principles. :contentReference[oaicite:1]{index=1}
So agents must be **assistive + auditable**, not magical.

### 8.1 Agent: License Inventory Extractor
**Purpose:** Gather “entitled/available” from vendor sources/contracts.
- Inputs: Entitlements, contract docs, portal exports, API data
- Steps:
  1) Validate schema / doc hash
  2) Extract SKU, quantities, dates, terms
  3) Produce draft entitlements + discrepancies
- Output: Proposed entitlement updates (requires approval)
- Guardrails: No auto-write to entitlements without approval

### 8.2 Agent: Consumption Discovery Agent
**Purpose:** Identify consumption signals from device/user telemetry.
- Inputs: MDM assignments, install state, active usage logs (if available)
- Steps:
  1) Pull signals
  2) Normalize to consumption units (per SKU model)
  3) Flag low-confidence signals for review
- Output: ConsumptionSignal + ConsumptionUnit candidates

### 8.3 Agent: Reconciliation & Truth Builder (Core)
**Purpose:** Produce the “always true” snapshot used by sidebar.
- Trigger: schedule (e.g., every 15 min / hourly) + manual “Run now”
- Steps:
  1) Fetch latest signals + entitlements
  2) Apply deterministic ruleset version (stored)
  3) Deduplicate + resolve conflicts
  4) Compute counters per SKU/pool
  5) Persist immutable snapshot + evidence pack
- Output: New `ConsumptionSnapshot` and sidebar updates
- Guardrails:
  - Must fail closed (no snapshot update) on integrity errors
  - Must store run report with diffs and reasons

### 8.4 Agent: Anomaly & Drift Detector
**Purpose:** Detect abnormal changes and drift over time.
- Inputs: snapshots over time
- Detects:
  - sudden spikes
  - negative remaining
  - oscillation (count flips)
  - source degradation (missing signals)
- Output: Alerts + recommended actions

### 8.5 Agent: Optimization Advisor (Recommend-only)
**Purpose:** Recommend reclaim/reassignment/purchase.
- Inputs: utilization, unused assignments, inactive devices/users, renewal dates
- Output: ranked recommendations + expected savings
- Guardrails: no auto-remediation without explicit approval workflow

---

## 9) UI/UX Requirements
### 9.1 Sidebar (Always Visible)
A “Licenses” section must show:
- **Consumed / Entitled / Remaining** (global)
- “Last reconciled: <timestamp>”
- Health: OK / Degraded / Failed / Stale (with stale duration)
- If stale or failed: show reason summary + link “View details”

**Update behavior**
- Sidebar values must come from the **latest successful ConsumptionSnapshot**
- If a reconciliation run fails, sidebar keeps last snapshot but flips health to Failed and shows last success time.

### 9.2 License Dashboard Page
Minimum widgets:
- Global counters (entitled/consumed/remaining) + trend line (last 30/90 days)
- Top SKUs by consumption
- Alerts panel (anomalies, expiring entitlements, negative remaining)
- Filters: vendor, SKU, pool, region, BU, license model type

### 9.3 SKU Detail Page
- Snapshot history timeline + diffs (what changed, why)
- Consumption breakdown:
  - by user/device
  - by source system
  - confidence levels
- Evidence pack download/export

### 9.4 Admin Pages
- Vendor + SKU management
- Entitlement management (create/edit requires approvals + attachments)
- Integration settings + import job monitor
- Ruleset versioning (see reconciliation logic version in use)

---

## 10) Backend/API Requirements (DRF)
### Read APIs (examples)
- `GET /api/licenses/summary` → global counters + last_reconciled + health
- `GET /api/licenses/skus` → list + current counters + trend
- `GET /api/licenses/skus/{id}` → details + snapshot diffs
- `GET /api/licenses/snapshots` → list by time range
- `GET /api/licenses/alerts` → active alerts
- `GET /api/licenses/evidence/{snapshot_id}` → evidence pack metadata/download link

### Write APIs (approval-governed)
- `POST /api/licenses/entitlements` → create draft entitlement change
- `POST /api/licenses/reconcile/run` → trigger reconciliation run (RBAC)
- `POST /api/licenses/import` → upload import file (validated, logged)
- `POST /api/licenses/rulesets` → create new ruleset version (restricted)

**Non-negotiable:** All write endpoints must produce AuditLog entries with correlation IDs.

---

## 11) Determinism, Evidence, and Auditability
Because EUCORA is built around deterministic governance and evidence-first behavior :contentReference[oaicite:2]{index=2}, license numbers must be defendable:
- Every snapshot must reference:
  - the ruleset version used
  - import job IDs and hashes
  - diff summary (what changed since previous snapshot)
- Evidence pack must be exportable for audit/CAB-style reviews:
  - logs, hashes, ruleset metadata, counts, exceptions

---

## 12) Reliability & Performance Requirements
- Reconciliation job must be idempotent and safe to retry :contentReference[oaicite:3]{index=3}
- Target freshness:
  - Default schedule: every 15–60 minutes (configurable)
  - Sidebar must show staleness if beyond threshold (e.g., >2x schedule)
- Degradation modes:
  - If one source system is down, snapshot must still compute with partial data but must label “Degraded” and explain coverage gaps.

---

## 13) Acceptance Criteria (Testable)
### AC1 — Sidebar Truth
- Given a successful reconciliation snapshot exists,
  - sidebar shows counters matching that snapshot exactly
  - sidebar shows correct “last reconciled” timestamp
- Given reconciliation fails,
  - sidebar retains last known snapshot values
  - health flips to Failed and shows failure reason + last success time

### AC2 — Correct Counters
- For each license model type (user/device/concurrent),
  - system computes Consumed/Remaining per defined rules
  - no negative remaining unless entitlement < consumed; in that case alert is generated

### AC3 — Auditability
- Every entitlement change, import job, reconciliation run:
  - creates an immutable audit entry
  - has evidence references (hashes, artifacts)
  - is attributable to a user (or agent with delegated user context)

### AC4 — Agent Guardrails
- Inventory Extractor and Optimization Advisor cannot auto-write final changes without approval
- Reconciliation agent cannot silently overwrite truth without an evidence pack
- All agent actions are logged with inputs/outputs and correlation_id

### AC5 — Drilldown & Evidence
- From dashboard → SKU detail → snapshot diff → evidence pack export works end-to-end
- Evidence pack is complete enough to explain “why consumed changed” for any SKU

---

## 14) Open Questions (Must be Answered Before Build)
1) Which license model types are in scope for the customer (user/device/concurrent/subscription/features)? = All
2) Which source systems are authoritative for “consumed” (Intune/Jamf/SCCM/vendor portal/usage telemetry)? = All
3) What is the freshness SLA expected by customer (15 min vs hourly vs daily)? = Daily
4) What is the approval policy: who approves entitlement updates and optimization actions? = Need to create approval workflow with human in loop.

---
