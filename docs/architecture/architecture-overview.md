# EUCORA
### End-User Computing Orchestration & Reliability Architecture
**Architecture Overview, Control Plane Design, and Operating Model**

## Version
v1.2 (Board Review Draft — Robust)

## Status
Proposed – Pending Board Approval

## Audience
CAB, Security, Endpoint Operations, Platform Engineering

## Decision Summary (What the board is being asked to approve)
Approve Phase 0–1 to establish (1) a thin Control Plane, (2) a packaging supply-chain factory, and (3) a measurable ring rollout model with deterministic risk + CAB gating, while keeping Intune/Jamf/SCCM/Landscape/Ansible as execution systems.

---

## 1. Executive Summary

We manage a heterogeneous endpoint estate spanning:
- **50,000+ users** across acquisitions / mergers
- **Windows, macOS, Ubuntu/Linux**
- **iOS/iPadOS + Android** (BYOD + corporate-owned)
- Mixed security posture and mixed connectivity (**online + offline sites**)

Current practices (scripts + fragmented tooling) do not scale to **5,000+ applications** and create unacceptable risk in:
- security (privilege sprawl, unverified software, weak auditability)
- operations (drift, inconsistent deployment outcomes)
- governance (CAB evidence gaps)

This proposal defines:
- a **thin Control Plane**: policy + orchestration + evidence, acting as the system-of-record for **policy intents, approvals, and evidence**
- a **Packaging & Publishing Factory**: reproducible builds, signing/notarization, SBOM, scanning, testing
- a **Hybrid Content Distribution Plane**: site-aware routing, mirrors/caches for bandwidth and offline requirements
- a **ring-based rollout model**: measurable promotion gates and plane-specific rollback strategies

It explicitly **does not** replace Intune/Jamf/SCCM/Landscape/Ansible; it standardizes the enterprise lifecycle across them.
It is **not** the system-of-record for **device configuration** or **runtime compliance state** (those remain in the execution planes).

---

## 2. Principles (Non-Negotiable)

1. **Thin control plane**: Policy and orchestration only; no duplication of MDM features.
2. **Determinism**: No “AI-driven deployments”; all approvals and gates are explainable.
3. **Separation of duties**: Packaging ≠ Publishing ≠ Approval.
4. **Idempotency**: Every deployment action can be retried safely.
5. **Reconciliation over hope**: Continuous desired-vs-actual drift detection.
6. **Evidence-first governance**: CAB decisions include standardized evidence packs.
7. **Offline is a first-class constraint**: Explicit distribution strategy per site class.

---

## 3. Scope, Non-Goals, and Constraints

### 3.1 Goals
- System-of-record for **policy intents, approvals, and evidence** (not for device configuration or runtime compliance state).
- Standardized packaging supply-chain controls across platforms.
- Measurable ring rollouts with promotion gates, incident thresholds, and rollback plans.
- Hybrid/offline content distribution with clear site decision matrix.
- JIT privilege elevation with compliance gates and full auditability.

### 3.2 Non-Goals
- Replacing Intune/Jamf/SCCM/Landscape/Ansible as executors.
- Building a bespoke monolith that duplicates device management primitives.
- Autonomous production change without CAB/controls.

### 3.3 Execution Planes (Primary / Secondary)

| Platform | Primary | Secondary | Notes |
|---|---|---|---|
| Windows | Intune | SCCM | Legacy OS / constrained sites |
| macOS | Intune | Jamf | Jamf where deeper macOS controls are required |
| Ubuntu/Linux | Landscape / Ansible | Agent fallback | Signed repo as standard |
| iOS/iPadOS | Intune | — | ABM + ADE |
| Android | Intune | — | Android Enterprise |

---

## 4. Reference Architecture (Logical)

```
                   ┌──────────────────────────────────────────────┐
                   │                  Control Plane               │
                   │ Policy + Orchestration + Evidence (Thin)     │
                   └───────────────┬──────────────────────────────┘
                                   │
                   ┌───────────────▼──────────────────────────────┐
                   │        Packaging & Publishing Factory         │
                   │ Build → Sign/Notarize → SBOM/Vuln → Test      │
                   └───────────────┬──────────────────────────────┘
                                   │
          ┌────────────────────────▼────────────────────────┐
          │                 Execution Planes                 │
          │ Intune | Jamf | SCCM | Landscape/Ansible         │
          └───────────────┬──────────────────────────────────┘
                          │
          ┌───────────────▼──────────────────────────────────┐
          │                  Endpoint Devices                 │
          │ Win | macOS | Ubuntu | iOS/iPadOS | Android        │
          └──────────────────────────────────────────────────┘

                 ┌───────────────────────────────────┐
                 │ Hybrid Content Distribution Plane  │
                 │ Artifact store + caches + mirrors  │
                 └───────────────────────────────────┘
```

Key principle:
> The platform decides **what** should happen. Existing tools execute **how** it happens.

---

## 5. Control Plane (Concrete)

### 5.1 Responsibilities
- Identity & entitlement resolution (groups, acquisition boundaries, device conditions)
- Application catalog and lifecycle state (requested → packaged → staged → approved → published → retired)
- Deterministic risk scoring and approval enforcement (CAB)
- Rollout orchestration and ring promotion gates
- Evidence pack generation and audit event logging
- Desired-state reconciliation and drift management

### 5.2 Minimum Components (Implementation-Agnostic)
- **API Gateway + Auth**: single entry point; Entra ID authentication; scoped RBAC.
- **Policy Engine**: evaluates entitlements, risk scoring, gates, and constraints.
- **Workflow / CAB Module**: approval states, exception handling, and evidence requirements.
- **Orchestrator**: creates “deployment intents” and schedules actions; never executes directly on endpoints.
- **Execution Plane Connectors**: adapters to Intune/Jamf/SCCM/Landscape/Ansible with idempotent semantics.
- **Evidence Store**: immutable storage for evidence packs (object store/WORM capable).
- **Event Store**: append-only deployment events (immutable audit trail).
- **Telemetry + Reporting**: success rate, time-to-compliance, failure reasons, rollback execution metrics.

### 5.3 Core Data Model (System-of-Record Objects)
- **Application**: canonical identity, owner, category/class, support tier, licensing model.
- **Application Version**: semantic version, release notes, supported OS matrix, dependencies.
- **Artifact**: package binaries + hashes + signatures + provenance.
- **Entitlement Rule**: target groups/conditions (user/device), exclusions, acquisition boundaries, posture constraints.
- **Deployment Intent**: desired state for a scope (ring, schedule, constraints, required evidence).
- **Approval Record**: approver, decision, conditions, expiry, exception link.
- **Risk Assessment**: inputs + computed score + threshold + justification.
- **Deployment Event**: append-only events with correlation id, actor, time, plane, outcome.

### 5.4 Tenant and Segmentation Model
- Single enterprise tenant with segmentation by:
  - acquisition boundary
  - business unit
  - geography/site
- Isolation is enforced via:
  - RBAC scopes
  - policy constraints (e.g., “apps for BU-A cannot publish into BU-B rings”)

### 5.4.1 Segmentation Guardrails (Hard Controls)
Guardrails are enforced by the Control Plane policy engine and connector implementations:
- **Default deny** for cross-boundary publishing and targeting.
- **Mandatory scope declaration** on every Deployment Intent (acquisition boundary, BU, and site scope).
- **Subset validation**: `target_scope ⊆ publisher_scope` and `target_scope ⊆ app_scope`.
- **Scope immutability**: changes to an app’s allowed scope require CAB approval and are versioned.
- **CAB evidence includes scope diff** (previous scope → requested scope) and explicit blast-radius summary.

### 5.5 RBAC Model (Minimum)
- **Platform Admin**: platform configuration, integration credentials, policy configuration.
- **Packaging Engineer**: build/test/sign artifacts; publish to staging only.
- **Publisher**: publishes approved artifacts to execution planes.
- **CAB Approver**: approve/deny; apply conditions; review evidence packs.
- **Security Reviewer**: approves exceptions; owns SBOM/vuln policy and PKI controls.
- **Endpoint Operations**: monitors telemetry, triggers remediation within scope.
- **Auditor**: read-only access to events and evidence.

### 5.6 Idempotency, Concurrency, and Reconciliation
The Control Plane operates on a “desired state” model:
- **Intent is declarative**: what version should be present in ring X for scope Y.
- **Connectors are idempotent**: retries must not duplicate assignments or corrupt state.
- **Concurrency rules**: per-app/per-ring “one active change at a time” unless explicitly approved.
- **Reconciliation loop**:
  - periodically read execution plane state
  - compare to desired intent
  - emit drift events
  - trigger remediation workflows (within policy)

### 5.7 Failure Modes + HA/DR (Minimum)
- The Control Plane must not be a single point of endpoint execution:
  - If the Control Plane is degraded, already-deployed apps continue to function.
  - New deployments and promotions may pause safely; execution planes remain operational.
- Target availability: **99.9%** for the Control Plane (or enterprise standard, whichever is higher).
- HA:
  - stateless services behind load balancers
  - HA database (managed or clustered) for the system-of-record
  - redundant object storage for evidence packs/artifacts
- DR:
  - Minimum expectation: **RPO ≤ 24h** and **RTO ≤ 8h** (or enterprise standard, whichever is stricter)
  - audit logs and evidence replicated per compliance requirements

#### Failure Impact Matrix (Minimum)
| Failure | Impact | Control Plane Behavior | Mitigation |
|---|---|---|---|
| Control Plane unavailable | No new changes can be approved/published | Pause new deployments/promotions; emit incident | Restore HA; DR failover if required |
| Database unavailable | System-of-record read/write fails | Block publish and approvals; existing deployments unaffected | DB HA/failover; DR restore |
| Evidence store unavailable | Evidence packs cannot be written/read | **Publish blocked** (no evidence); promotions paused | Object store redundancy; retry/backoff |
| Intune Graph degraded/unavailable | Connector cannot publish/query reliably | Backoff/retry; promotions paused; reconcile later | Throttling/backoff; manual CAB pause if prolonged |
| Jamf API degraded/unavailable | Jamf publish/query impacted | Backoff/retry; Jamf promotions paused | Retry with idempotent keys |
| SCCM site server unavailable | SCCM publish/query impacted | SCCM promotions paused | Local DP content remains usable; restore site server |

---

## 6. Integration Mechanics (How We Actually Connect to Tools)

### 6.1 Integration Pattern
Each execution plane is integrated through an adapter that supports:
- publish (create/update app/package and assignments)
- query (read status, assignments, install telemetry where supported)
- remediate (uninstall/rollback, redeploy, ring pinning)
- audit correlation (correlation ids mapped to plane artifacts/assignments)

The Control Plane has **no direct connectivity to endpoints**; it only interfaces with authorized management planes (Intune/Jamf/SCCM/AWX/Landscape). There is **no Control Plane → endpoint agent channel** in Phase 0–2; any future agent capability is **read-only telemetry** unless explicitly approved.

### 6.2 Execution Plane Connectors (Concrete Expectations)

| Plane | Integration Surface | Auth | Notes |
|---|---|---|---|
| Intune | Microsoft Graph API | Entra ID app registration (cert-based) | Throttling + pagination; eventual consistency handling |
| Jamf Pro | Jamf Pro API | OAuth / client creds | Separate endpoints for packages, policies, smart groups |
| SCCM | PowerShell/REST provider (site server) | Service account + constrained delegation | Suitable for legacy/offline sites; requires strict SoD controls |
| Landscape | Landscape API / client tooling | Service account + API token | Scheduling and compliance reporting vary by deployment model |
| Ansible (AWX/Tower) | AWX/Tower API | OAuth/token | Use for package install/remediation playbooks and repo mirror config |

Connector quality bars:
- deterministic mapping from control-plane intent → plane-specific objects
- safe retries (idempotent keys)
- explicit error classification (transient vs permanent vs policy violation)
- backoff and rate-limit handling

---

## 7. Packaging & Publishing Factory (Concrete)

### 7.1 Supply Chain Gates (Mandatory)
For every artifact, the factory produces and stores:
- hashes (SHA-256) and signing metadata
- SBOM (SPDX or CycloneDX)
- vulnerability scan results and policy decision (pass/fail/exception)
- provenance: inputs, builder identity, pipeline run id, time, source references
- automated test evidence (where applicable)

Policy defaults (CAB-ready):
- **Block Critical/High** vulnerabilities by default.
- Exceptions require: expiry, compensating controls, and **Security Reviewer** approval; CAB record links the exception.
- Scans run in the **Packaging Factory pipeline** and gate promotion/publish actions (publish is blocked without a pass or approved exception).
- Publish APIs enforce `scan_pass OR approved_exception` as a hard precondition.
- Scanner implementations are enterprise-standard tools (e.g., Trivy/Grype/Snyk or equivalent) plus malware scanning as required.

### 7.2 Windows
- Preferred: **MSIX** where feasible.
- Standard: **Intune Win32 (.intunewin)** for MSI/EXE/unpackaged.
- Deterministic requirements:
  - install/uninstall commands (silent, no UI)
  - detection rules (file/registry/productcode) documented and tested
  - exit code mapping and reboot behavior documented
  - remediation scripts where needed (self-heal, dependency fixes)

### 7.3 macOS
- Signed PKG; notarization when applicable (per Apple requirements and distribution method).
- Intune primary; Jamf secondary when deeper macOS controls are required.
- Evidence includes: signing identity, notarization ticket (if applicable), pkgutil receipts/detections.

### 7.4 Ubuntu/Linux
- Standard: **signed APT repository** + versioned packages.
- Mirroring: site-local mirrors for offline/intermittent environments.
- Enforcement via Landscape schedules or Ansible playbooks.
- Explicit constraint: do not introduce Chef unless it is already the enterprise standard.

Linux drift policy (explicit):
- Phase 2: **detect-only** drift (report + ticket) using Landscape/Ansible inventory and package state checks.
- Phase 3: **enforce** drift (remediate) where approved, via Ansible playbooks or Landscape schedules, scoped by acquisition boundary and site class.

### 7.5 Mobile
- **Apple**: ABM + ADE; licensing/assignment via Intune (VPP workflow owned and governed).
- **Android**: Android Enterprise + Managed Google Play; Zero-touch for corporate-owned at scale.
Offline clarification:
- Offline behavior is **not guaranteed** for BYOD; device check-in windows are required for policy/app updates.
- Corporate-owned dedicated devices may cache apps, but still require periodic MDM check-in to remain compliant.
Publishing/rollback realities (explicit):
- Public store apps: rollback is typically managed by assignment/remove, not version “downgrade”.
- iOS/iPadOS LOB: managed distribution is supported; rollback is by reassigning a prior retained version where feasible, otherwise remove and remediate.
- Android private apps: use managed Google Play versioning/track strategy; rollback depends on what versions are retained/published to tracks.
LOB retention policy (to enable rollback where feasible):
- Retain prior LOB versions for **90 days** (or last **2** releases, whichever is greater), subject to storage/compliance constraints.

---

## 8. Hybrid + Offline Content Distribution (Explicit)

### 8.1 Site Classes
- **Online**: stable connectivity to cloud.
- **Intermittent**: limited bandwidth or frequent outages.
- **Air-gapped**: no cloud access; controlled transfer windows.

### 8.2 Distribution Primitives (By Platform)
- **Windows**:
  - online: Intune delivery with **Delivery Optimization** as the default client-side caching mechanism
  - enterprise caching (where feasible): **Microsoft Connected Cache** as the standard for bandwidth optimization at sites that support it
  - constrained/offline: SCCM distribution points (DPs) or equivalent local content distribution
- **macOS**:
  - online: Intune/Jamf standard distribution
  - constrained: Jamf distribution points / local caching where approved
- **Linux**:
  - online: central signed APT repo
  - offline: site mirrors (signed) with explicit sync procedures
- **Mobile**:
  - generally requires periodic internet access for MDM; offline support is limited to device-side cached apps

### 8.3 Decision Matrix (Minimum)

| Condition | Windows | macOS | Linux |
|---|---|---|---|
| Online | Intune primary | Intune primary | Central APT repo |
| Intermittent | Intune + local caching where supported; SCCM where required | Intune/Jamf with local distribution points where required | Mirror at site + Landscape/Ansible |
| Air-gapped | SCCM packages via DPs + controlled import | Jamf packages via controlled import | Mirror via controlled import + pinning |

All air-gapped transfers require:
- hash verification
- signing verification
- import audit events and evidence pack linkage

### 8.4 Standard Pattern (Windows Offline/Constrained)
To avoid ambiguity, the default approach is:
- **Constrained/offline Windows sites**: **SCCM DP is the authoritative content channel** for application binaries.
- **Intune remains the primary assignment/compliance plane**; where co-management exists, Intune targeting triggers SCCM-managed distribution for those site/device cohorts.
- Exceptions (e.g., Connected Cache-only without SCCM DP, bespoke local mirrors) require CAB approval and are recorded as site-class exceptions with expiry.

Co-management mechanics (minimum, non-hand-wavy):
- Devices are **site-scoped** via tags and/or Entra ID group membership aligned to site classes.
- The Control Plane maintains or consumes approved **SCCM collections** aligned to those scopes, and SCCM deployments are bound to those collections.
- Promotion gates and CAB enforcement remain in the Control Plane; SCCM is the distribution/execution channel for constrained sites.

Preference order (Windows content delivery):
- Online: Intune + Delivery Optimization.
- Bandwidth-constrained (but online): Microsoft Connected Cache where feasible.
- Offline/air-gapped: SCCM DP (mandatory) with controlled imports and audit evidence.

---

## 9. Risk & Approval Model (Deterministic)

### 9.1 Risk Score Definition
Risk is computed from explicit factors. A simple model is used initially, then calibrated:

```
RiskScore = clamp(0..100, Σ(weight_i * normalized_factor_i))
```

`normalized_factor_i` is defined as `0.0` (no risk contribution) to `1.0` (maximum contribution) using documented scoring rules per factor (examples: “admin required” = 1.0; “user context only” = 0.2).

### 9.2 Risk Factors (Initial Weights)

| Factor | Examples | Weight |
|---|---|---:|
| Privilege impact | admin required, service install, system extensions | 20 |
| Supply chain trust | signature validity, notarization, publisher reputation | 15 |
| Exploitability | network listeners, exposed services, macros/scripting | 10 |
| Data access | credential store, wide filesystem access | 10 |
| SBOM/vulnerability | critical/high CVEs in dependencies | 15 |
| Blast radius | scope size, ring level, BU/site count | 10 |
| Operational complexity | offline import, reboots, special sequencing | 10 |
| History | prior incidents, failure rate, rollback difficulty | 10 |

### 9.2.1 Risk Factor Scoring Rubric (v1.0 Stub)
This rubric makes normalization defensible and is calibrated over time.

- Publisher trust (`0.0`–`1.0`):
  - `0.1`: signed + known vendor + consistent provenance
  - `0.4`: signed but unknown/unverified vendor
  - `0.9`: unsigned/uncertain provenance
- Privilege impact:
  - `0.2`: user-context install, no elevation
  - `1.0`: admin required / service install
  - `1.0`: driver/kernel extension/system extension
- Exploitability:
  - `0.2`: no listeners, no macro/scripting capability
  - `0.6`: user-space listener or embedded scripting
  - `1.0`: privileged listener or exposed service with elevated context
- SBOM/vulnerability:
  - `0.0`: no High/Critical findings
  - `0.7`: High present (no Critical) with compensating controls possible
  - `1.0`: Critical present (blocked unless exception)

Calibration rules:
- weights and thresholds are reviewed quarterly by Security + CAB
- model changes require versioning (risk model vX.Y) and evidence of calibration
Thresholds (including the **>50** CAB gate) are **provisional** for risk model v1.0 and may be adjusted based on incident and failure data.

### 9.3 Thresholds and Gates
- **Risk ≤ 50**: automated ring progression allowed (with promotion gates).
- **Risk > 50**: CAB approval required before publishing beyond Ring 1.
- **Privileged tooling**: always requires CAB approval, regardless of score.
- Publishing into Ring 1 (Canary) still requires **evidence pack completeness** and all non-CAB gates; only the CAB approval itself is bypassed at Ring 1 for `Risk > 50`.

### 9.4 Evidence Pack Requirements
At minimum, every CAB submission includes:
- artifact hashes + signatures
- SBOM + scan report + policy decision
- install/uninstall/detection documentation
- rollout plan (rings, schedule, targeting, exclusions)
- rollback plan (plane-specific)
- test evidence (lab + ring 0 results)
- exception record(s), if any

### 9.5 Exceptions (Controlled)
Exceptions are permitted only with:
- explicit expiry date
- compensating controls (e.g., tighter ring limits, additional monitoring)
- named accountable owner
- audit linkage to the deployment intent

---

## 10. Rollout + Rollback (Per-Plane Reality)

### 10.1 Ring Model
1. Ring 0 – Lab / Automation
2. Ring 1 – Canary
3. Ring 2 – Pilot
4. Ring 3 – Department
5. Ring 4 – Global

### 10.2 Promotion Gates (Measurable)
- install success rate meets threshold (initial targets; calibrated per app class):
  - Ring 1 (Canary) ≥ **98%**
  - Ring 2 (Pilot) ≥ **97%**
  - Rings 3–4 (Department/Global) ≥ **99%** for enterprise standard apps
- time-to-compliance meets threshold (initial targets):
  - Online sites: **≤ 24h**
  - Intermittent sites: **≤ 72h**
  - Air-gapped sites: **≤ 7d** (or next approved transfer window)
- no security incidents attributable to package
- rollback validated for the plane(s)
- CAB approval where required

### 10.3 Rollback Strategies
Rollback is not transactional across all planes:
- **Intune**: supersedence/version pinning, targeted uninstall, remediation scripts.
- **SCCM**: rollback packages + collections + DPs.
- **Jamf**: policy-based version pinning + uninstall scripts.
- **Linux**: apt pinning, package downgrade, remediation playbooks.
- **Mobile**: assignment/remove, track/version strategies, and remediation; version rollback feasibility depends on distribution method and retained versions.

---

## 11. Privilege & JIT (Concrete)

### 11.1 Goals
- eliminate standing local admin where possible
- time-bound elevation with device posture checks
- auditable approvals and session logging where feasible

### 11.2 Standard Approach (Default + Exceptions)
Default choices are explicit to avoid “options paralysis”:
- **Windows default**: **Intune Endpoint Privilege Management (EPM)** where supported; enterprise PAM tooling is used only for legacy/edge cohorts by exception.
- **macOS default**: enterprise PAM tooling (where present) or Jamf-governed elevation patterns; avoid unmanaged local admin.
- **Linux default**: centrally managed sudo policy; JIT via enterprise PAM tooling where available; full audit to SIEM.

### 11.3 Elevation Request Workflow (Governed)
- Elevation requests are policy-evaluated (device posture + user role + app classification).
- If elevation is required to deploy a **high-risk (>50)** or **privileged** tool, the Control Plane enforces a **CAB gate** before issuing an approval token/workflow outcome.
- Elevation approvals are time-bound, scope-bound (app + device cohort), and produce audit events suitable for SIEM correlation.

Break-glass:
- limited, audited accounts
- periodic access reviews
- explicit post-incident rotation and evidence

---

## 12. Security, Audit, and Compliance

- **Secrets management**: credentials stored in a vault; rotation policy defined.
- **Key ownership**:
  - Windows code-signing
  - macOS signing + notarization
  - APT repo signing keys
- **Logging**:
  - immutable deployment events
  - evidence pack retention policy (per enterprise retention policy; duration set by regulation and audit requirements)
  - SIEM integration for privileged actions and policy violations
- **Separation of duties**:
  - Packaging cannot directly publish to production without CAB-approved promotion.

---

## 13. Prerequisites (Expanded)

- Entra ID + required identity governance (access reviews, RBAC hygiene)
- Microsoft Intune enabled for Windows/macOS/iOS/Android + compliance policy baseline
- Conditional Access integrated with Intune compliance

Apple:
- ABM + ADE tokens governed (renewal owners, lifecycle)
- APNs certificate governance
- VPP app licensing workflow (ownership defined)

Android:
- Android Enterprise configured
- Zero-touch enrollment configured where supported
- BYOD vs corporate-owned modes defined

SCCM (legacy):
- co-management boundaries defined
- distribution points aligned to offline strategy

Linux:
- signed APT repo + mirrors
- Landscape/Ansible ownership defined

Supply chain:
- SBOM + vulnerability scanning toolchain
- malware scanning/allowlisting as required
- exception workflow agreed with CAB/Security

---

## 14. Operating Model (RACI — Minimum)

### 14.1 Access Boundaries & SoD Enforcement
Separation of duties is enforced with explicit access boundaries and monitored privileged roles:
- **Packaging Engineers** have **no Intune production write access** (no create/update app objects, assignments, or production groups).
- **Publishers** are a separate, limited role:
  - production publish rights only (scoped by BU/acquisition boundary)
  - monitored and access-reviewed
  - preferably JIT via PIM/privileged access workflow where available
- **CAB approvals are enforced by the Control Plane** before any publish action is permitted.

Ownership clarity (minimum):
- **Intune production app objects & assignments**: Publisher (accountable), Endpoint Ops (responsible for operational health/runbooks), Security (consulted for policy exceptions).
- **Entra ID dynamic groups lifecycle**: Endpoint Ops/Identity team (responsible) with change control; Publishers consume approved groups, do not create ad-hoc production groups.
- **ABM/ADE tokens + VPP licensing operations**: Endpoint Ops (Apple platform owner) with documented renewal owners and operational runbooks.

How we prevent role escalation:
- separate Entra ID groups for Packaging vs Publisher vs Platform Admin
- no shared service principals; publisher credentials are scoped and rotated
- publish actions require Control Plane correlation id + CAB approval record (for gated changes)

| Activity | Packaging | Security | CAB | Endpoint Ops | App Owner |
|---|---|---|---|---|---|
| Onboard new app | R | C | A | C | C |
| Approve high-risk/privileged | C | R | A | C | C |
| Publish to production | C | C | A | R | C |
| Support incidents | C | C | C | R | C |
| Define entitlement rules | C | C | A | R | C |
| Maintain signing keys | C | R | C | C | C |

Legend: R=Responsible, A=Accountable, C=Consulted

---

## 15. Delivery Roadmap (Phased, With Exit Criteria)

### Phase 0 — Foundations (2–4 weeks)
- Define app taxonomy, minimum metadata, and “definition of done” for packages.
- Establish signing key governance and secrets management.
- Confirm CAB evidence pack template and thresholds.

Exit criteria:
- CAB accepts evidence pack template and risk model v1.0.

### Phase 1 — Windows Factory MVP (6–10 weeks)
- Build packaging pipeline for Win32/MSIX (signing + SBOM + scanning + test installs).
- Implement ring model and publish workflow into Intune (with correlation ids + evidence).
- Implement basic reconciliation (desired intent vs published assignments).

Exit criteria:
- 10–20 representative apps onboarded end-to-end with measurable success rates.

### Phase 2 — macOS + Linux Expansion (8–12 weeks)
- Add macOS packaging/notarization workflows and publishing via Intune/Jamf.
- Stand up signed APT repo + mirror pattern and enforcement via Landscape/Ansible.

Exit criteria:
- Offline site pilot validated with at least one constrained site per OS.

### Phase 3 — Scale + Optimization (ongoing)
- Advanced reconciliation/drift remediation, richer telemetry, automated exception expiry.
- Standardized remediation playbooks and support runbooks.

---

## 16. Strategic Outcome

This architecture is implementable and reduces risk by:
- enforcing supply-chain controls (SBOM, scanning, signing)
- making CAB decisions evidence-based and auditable
- standardizing rollout/rollback reality across execution planes
- supporting offline sites with an explicit distribution strategy
- preventing privilege sprawl via concrete JIT mechanisms
