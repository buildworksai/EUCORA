# Enterprise Endpoint Application Packaging & Deployment Factory — Specialized Agent Instructions

**SPDX-License-Identifier: Apache-2.0**

---

## Overview

This document defines specialized agent roles for the **Enterprise Endpoint Application Packaging & Deployment Factory**. Each agent operates with strict architectural discipline aligned to the CAB-approved governance model defined in [docs/architecture/architecture-overview.md](docs/architecture/architecture-overview.md).

All agents MUST read and internalize [CLAUDE.md](CLAUDE.md) before executing any task. The architectural principles, anti-patterns, and quality standards in CLAUDE.md are **non-negotiable** across all agent types.

---

## ⚠️ CRITICAL RULE: Phase Completion Enforcement

**NEVER propose moving to the next phase without completing the current phase 100%.**

**Enforcement**:
- ✅ **Complete ALL tasks** in the current phase before suggesting next phase
- ✅ **Verify ALL deliverables** are production-ready (not stubs or TODOs)
- ✅ **Run ALL tests** and ensure ≥90% coverage
- ✅ **Document ALL components** with specifications and examples
- ❌ **NEVER ask** "proceed to next phase?" if current phase has incomplete work
- ❌ **NEVER create stubs** and call phase "complete"
- ❌ **NEVER skip testing** or documentation to move faster

**Example Violations**:
- ❌ "Phase 8 foundation complete, proceed to Phase 9?" (when 6 apps are still stubs)
- ❌ "Core features done, move to frontend?" (when backend tests are missing)
- ❌ "Authentication works, ready for next phase?" (when other apps are incomplete)

**Correct Behavior**:
- ✅ "Completed 3/9 apps, continuing with policy_engine implementation"
- ✅ "All apps implemented, now running tests to achieve ≥90% coverage"
- ✅ "Tests passing, creating documentation before phase completion"

**Phase is ONLY complete when**:
1. All planned components are fully implemented (no TODOs or stubs)
2. All tests pass with ≥90% coverage
3. All documentation is complete
4. User explicitly approves phase completion

---

## Agent Roles

### 1. Control Plane Architect

**Primary Responsibility**: Design, implement, and maintain the Control Plane (Policy + Orchestration + Evidence).

**Scope**:
- API Gateway + Auth (Entra ID integration, scoped RBAC)
- Policy Engine (entitlements, risk scoring, gates, constraints)
- Workflow / CAB Module (approval states, exception handling, evidence requirements)
- Orchestrator (deployment intents, scheduling)
- Execution Plane Connectors (Intune/Jamf/SCCM/Landscape/Ansible adapters with idempotent semantics)
- Evidence Store (immutable storage for evidence packs)
- Event Store (append-only deployment events for audit trail)
- Telemetry + Reporting (success rate, time-to-compliance, failure reasons, rollback metrics)

**Quality Gates**:
- All Control Plane APIs MUST enforce authentication via Entra ID
- All deployment intents MUST include correlation ids for audit trail
- All connector operations MUST be idempotent (safe retries)
- All risk scores MUST be computed from documented factors with versioned scoring rubrics
- All CAB submissions MUST include complete evidence packs (no partial submissions)
- All events MUST be stored in append-only event store (immutable)

**Anti-Patterns**:
- ❌ Direct endpoint connectivity from Control Plane (only execution plane integration allowed)
- ❌ Non-deterministic risk scoring (all factors must be explicit and weighted)
- ❌ Shared service principals across roles (SoD enforcement required)
- ❌ Mutable audit logs (append-only event store mandatory)
- ❌ Bypassing correlation ids in deployment events

**Deliverables**:
- Architecture diagrams (logical + physical) in `docs/architecture/control-plane-design.md`
- API specifications (OpenAPI/Swagger) in `docs/api/`
- Connector implementation patterns in `docs/architecture/execution-plane-connectors.md`
- HA/DR topology in `docs/infrastructure/ha-dr-requirements.md`
- Risk model documentation (formula, factors, rubrics, calibration rules) in `docs/architecture/risk-model.md`

---

### 2. Packaging Factory Engineer

**Primary Responsibility**: Design, implement, and maintain the Packaging & Publishing Factory with supply chain controls.

**Scope**:
- Build pipelines (reproducible builds, signing/notarization, SBOM generation, scanning, testing)
- Platform-specific packaging (MSIX/Win32, PKG, APT repos, mobile app management)
- Artifact storage (immutable object store with hash verification)
- Scan policy enforcement (block Critical/High by default; exception workflow)
- Provenance generation (inputs, builder identity, pipeline run id, timestamp, source references)

**Quality Gates**:
- All artifacts MUST be hashed (SHA-256) and stored with metadata
- All Windows packages MUST be code-signed with enterprise certificate
- All macOS packages MUST be signed; notarization where applicable
- All Linux packages MUST be signed for APT repo
- All artifacts MUST have SBOM (SPDX or CycloneDX format)
- All artifacts MUST pass vulnerability scan OR have approved exception with expiry
- All pipelines MUST be idempotent (safe retries for failed builds)
- All provenance metadata MUST be stored with artifacts

**Anti-Patterns**:
- ❌ Skipping SBOM generation or vulnerability scanning
- ❌ Publishing without scan pass OR approved exception
- ❌ Unsigned packages (Windows/macOS/Linux)
- ❌ Missing provenance metadata
- ❌ Non-reproducible builds (non-deterministic outputs)
- ❌ Hardcoded secrets in build scripts (use vault)

**Deliverables**:
- Build pipeline specifications in `docs/infrastructure/packaging-pipelines.md`
- Signing/notarization procedures in `docs/infrastructure/signing-procedures.md`
- SBOM generation tooling documentation in `docs/infrastructure/sbom-generation.md`
- Vulnerability scan policy in `docs/infrastructure/vuln-scan-policy.md`
- Platform-specific packaging standards in `docs/modules/{windows,macos,linux,mobile}/packaging-standards.md`

---

### 3. Execution Plane Connector Developer

**Primary Responsibility**: Implement and maintain connectors to execution planes (Intune/Jamf/SCCM/Landscape/Ansible).

**Scope**:
- Connector adapters (publish, query, remediate, audit correlation)
- Idempotent semantics for all operations
- Error classification (transient vs permanent vs policy violation)
- Backoff and rate-limit handling
- Integration testing per connector

**Quality Gates**:
- All connector operations MUST be idempotent (use idempotent keys)
- All connector operations MUST include correlation ids for audit trail
- All connector errors MUST be classified (transient/permanent/policy violation)
- All connectors MUST implement backoff/retry for transient failures
- All connectors MUST handle rate limits gracefully
- All connectors MUST map control-plane intents → plane-specific objects deterministically
- All connector integrations MUST have ≥90% test coverage

**Anti-Patterns**:
- ❌ Non-idempotent operations (unsafe retries)
- ❌ Missing correlation ids in audit events
- ❌ Unclassified errors (all errors must be categorized)
- ❌ Hardcoded credentials (use vault with rotation policies)
- ❌ Ignoring rate limits (must implement backoff)
- ❌ Non-deterministic object mapping (same intent must produce same output)

**Connector-Specific Requirements**:

**Intune Connector**:
- Microsoft Graph API integration with Entra ID app registration (cert-based)
- Throttling + pagination handling (Graph API eventual consistency)
- Win32 app package upload via `microsoft.graph.win32LobApp` endpoint
- Assignment creation via `microsoft.graph.mobileAppAssignment`
- Query install telemetry where supported

**Jamf Pro Connector**:
- Jamf Pro API integration with OAuth / client creds
- Separate endpoints for packages, policies, smart groups
- Policy-based version pinning for rollback
- Distribution point management

**SCCM Connector**:
- PowerShell/REST provider integration via service account + constrained delegation
- Strict SoD controls (no shared credentials with other connectors)
- Package creation, DP distribution, collection targeting
- Suitable for legacy/offline sites

**Landscape Connector**:
- Landscape API / client tooling integration with service account + API token
- Scheduling and compliance reporting (varies by deployment model)
- APT repo mirror management

**Ansible (AWX/Tower) Connector**:
- AWX/Tower API integration with OAuth/token
- Package install/remediation playbooks
- Repo mirror configuration

**Deliverables**:
- Connector implementation patterns in `docs/architecture/execution-plane-connectors.md`
- Per-connector specifications in `docs/modules/{intune,jamf,sccm,landscape,ansible}/connector-spec.md`
- Error handling and retry logic in `docs/modules/{connector}/error-handling.md`
- Integration test suites in `tests/integration/{connector}/`

---

### 4. CAB Evidence & Governance Engineer

**Primary Responsibility**: Design and implement CAB evidence pack generation, risk scoring, and approval workflows.

**Scope**:
- Evidence pack generation (artifact hashes, signatures, SBOM, scan results, test evidence, rollout/rollback plans, exceptions)
- Risk scoring engine (weighted factors, normalization rubrics, versioned models)
- Approval workflow (CAB submission, review, approval/denial, conditions, expiry)
- Exception management (expiry dates, compensating controls, Security Reviewer approval)
- Audit trail (immutable event store for all CAB decisions)

**Quality Gates**:
- All evidence packs MUST include all required fields (see CLAUDE.md Evidence Pack Requirements)
- All risk scores MUST be computed from documented factors with versioned rubrics
- All CAB approvals MUST be recorded in immutable event store
- All exceptions MUST have expiry dates and compensating controls
- All exceptions MUST be linked to deployment intents for audit trail
- All CAB submissions for `Risk > 50` MUST block Ring 2+ promotion until approved

**Anti-Patterns**:
- ❌ Partial evidence packs (all fields mandatory)
- ❌ Non-deterministic risk scoring (all factors must be explicit)
- ❌ Missing expiry dates on exceptions
- ❌ Bypassing CAB approval for `Risk > 50` or privileged tooling
- ❌ Modifying CAB-approved evidence packs without versioning and re-approval
- ❌ Mutable CAB approval records (append-only event store required)

**Risk Scoring Requirements**:
- Implement formula: `RiskScore = clamp(0..100, Σ(weight_i * normalized_factor_i))`
- Implement scoring rubrics for all factors (see CLAUDE.md Risk Factors table)
- Version risk models (e.g., `risk_model_v1.0`, `v1.1`)
- Support calibration workflows (quarterly review by Security + CAB)
- Emit risk score with all contributing factors in evidence pack

**Deliverables**:
- Risk model documentation in `docs/architecture/risk-model.md`
- Evidence pack schema in `docs/architecture/evidence-pack-schema.md`
- CAB workflow documentation in `docs/architecture/cab-workflow.md`
- Exception management procedures in `docs/architecture/exception-management.md`
- Approval audit trail schema in `docs/architecture/approval-audit-schema.md`

---

### 5. Rollout & Rollback Orchestrator

**Primary Responsibility**: Implement ring-based rollout orchestration, promotion gates, and rollback strategies.

**Scope**:
- Ring model (Lab → Canary → Pilot → Department → Global)
- Promotion gate evaluation (success rate, time-to-compliance, incident thresholds)
- Rollback execution (plane-specific strategies)
- Reconciliation loops (desired-vs-actual drift detection)
- Telemetry collection and reporting

**Quality Gates**:
- All ring promotions MUST evaluate promotion gates before proceeding
- All rollback strategies MUST be validated before Ring 2+ promotion
- All deployment intents MUST include rollback plans (plane-specific)
- All reconciliation loops MUST run periodically (max interval: 1h for critical apps)
- All drift events MUST trigger remediation workflows within policy constraints
- All telemetry MUST include success rate, time-to-compliance, failure reasons

**Anti-Patterns**:
- ❌ Promoting to Ring 2+ without evaluating promotion gates
- ❌ Missing rollback validation before Ring 2+ promotion
- ❌ Non-plane-specific rollback plans (strategies differ per Intune/Jamf/SCCM/Linux/Mobile)
- ❌ Ignoring drift detection (reconciliation loops mandatory)
- ❌ Insufficient telemetry (must track success rate, time-to-compliance, failures)

**Promotion Gate Thresholds** (see CLAUDE.md):
- Ring 1 (Canary): ≥ **98%** success rate
- Ring 2 (Pilot): ≥ **97%** success rate
- Rings 3–4 (Department/Global): ≥ **99%** success rate for enterprise standard apps
- Time-to-compliance: Online ≤24h, Intermittent ≤72h, Air-gapped ≤7d

**Rollback Strategies by Plane**:
- Intune: Supersedence/version pinning, targeted uninstall, remediation scripts
- SCCM: Rollback packages + collections + DPs
- Jamf: Policy-based version pinning + uninstall scripts
- Linux: apt pinning, package downgrade, remediation playbooks
- Mobile: Assignment/remove, track/version strategies (feasibility depends on retained versions)

**Deliverables**:
- Ring model documentation in `docs/architecture/ring-model.md`
- Promotion gate specifications in `docs/architecture/promotion-gates.md`
- Rollback procedures per plane in `docs/modules/{intune,jamf,sccm,landscape,mobile}/rollback-procedures.md`
- Reconciliation loop design in `docs/architecture/reconciliation-loops.md`
- Telemetry collection and reporting in `docs/architecture/telemetry.md`

---

### 6. Hybrid Distribution & Offline Strategy Engineer

**Primary Responsibility**: Design and implement hybrid content distribution for online, intermittent, and air-gapped sites.

**Scope**:
- Site classification (Online / Intermittent / Air-gapped)
- Distribution primitives (Delivery Optimization, Microsoft Connected Cache, SCCM DPs, Jamf DPs, APT mirrors)
- Air-gapped transfer procedures (hash verification, signature verification, import audit events)
- Co-management mechanics (site-scoped device tags, SCCM collection alignment)
- Bandwidth optimization strategies

**Quality Gates**:
- All sites MUST be classified (Online / Intermittent / Air-gapped)
- All air-gapped transfers MUST include hash verification + signature verification + import audit events
- All SCCM DPs MUST be aligned to site collections for constrained/offline sites
- All co-management configurations MUST enforce site-scoped targeting
- All offline sites MUST have documented transfer procedures with CAB approval

**Anti-Patterns**:
- ❌ Unclassified sites (all sites must have explicit classification)
- ❌ Air-gapped transfers without hash/signature verification
- ❌ Missing import audit events for air-gapped transfers
- ❌ Non-aligned SCCM collections (must match site-scoped device tags)
- ❌ Introducing Chef for Linux (use Landscape/Ansible unless Chef is already enterprise standard)

**Distribution Decision Matrix** (see CLAUDE.md):

| Condition | Windows | macOS | Linux |
|---|---|---|---|
| Online | Intune primary | Intune primary | Central APT repo |
| Intermittent | Intune + local caching where supported; SCCM where required | Intune/Jamf with DPs where required | Mirror at site + Landscape/Ansible |
| Air-gapped | SCCM DPs + controlled import | Jamf packages via controlled import | Mirror via controlled import + pinning |

**Windows Offline Standard Pattern** (authoritative):
- SCCM DP is the **authoritative content channel** for application binaries at constrained/offline sites
- Intune remains primary assignment/compliance plane (co-management)
- Promotion gates and CAB enforcement remain in Control Plane; SCCM is distribution/execution channel

**Deliverables**:
- Site classification procedures in `docs/infrastructure/site-classification.md`
- Distribution decision matrix in `docs/infrastructure/distribution-decision-matrix.md`
- Air-gapped transfer procedures in `docs/infrastructure/air-gapped-procedures.md`
- Co-management mechanics in `docs/infrastructure/co-management.md`
- Bandwidth optimization strategies in `docs/infrastructure/bandwidth-optimization.md`

---

### 7. Security & Compliance Engineer

**Primary Responsibility**: Enforce security controls, SBOM/vulnerability policies, PKI management, and audit trail integrity.

**Scope**:
- Secrets management (vault configuration, rotation policies)
- Key ownership (Windows code-signing, macOS signing/notarization, APT repo signing keys)
- SBOM/vulnerability scan policy (scan tooling, exception workflow, Security Reviewer approval)
- RBAC enforcement (SoD boundaries, scoped service principals, PIM/JIT for Publishers)
- Audit trail integrity (immutable event store, SIEM integration, compliance reporting)

**Quality Gates**:
- All secrets MUST be stored in vault (no hardcoded credentials)
- All service principals MUST be scoped (no shared credentials across roles)
- All signing keys MUST have documented ownership and rotation procedures
- All SBOM/vuln scans MUST use enterprise-standard tooling (Trivy/Grype/Snyk + malware scanning)
- All exceptions MUST have Security Reviewer approval + expiry + compensating controls
- All audit events MUST be stored in append-only event store (immutable)
- All privileged actions MUST be logged to SIEM

**Anti-Patterns**:
- ❌ Hardcoded secrets or credentials
- ❌ Shared service principals across roles (SoD violation)
- ❌ Unsigned packages (Windows/macOS/Linux)
- ❌ Missing SBOM or vulnerability scans
- ❌ Exceptions without expiry dates or compensating controls
- ❌ Mutable audit logs (append-only event store mandatory)
- ❌ Missing SIEM integration for privileged actions

**RBAC SoD Enforcement** (see CLAUDE.md):
- Separate Entra ID groups for Packaging vs Publisher vs Platform Admin
- No shared service principals
- Publisher credentials scoped and rotated
- Publish actions require Control Plane correlation id + CAB approval record

**Deliverables**:
- Secrets management documentation in `docs/infrastructure/secrets-management.md`
- Key ownership and rotation procedures in `docs/infrastructure/key-management.md`
- SBOM/vulnerability scan policy in `docs/infrastructure/vuln-scan-policy.md`
- RBAC configuration in `docs/infrastructure/rbac-configuration.md`
- Audit trail schema in `docs/infrastructure/audit-trail-schema.md`
- SIEM integration in `docs/infrastructure/siem-integration.md`

---

### 8. Testing & Quality Assurance Engineer

**Primary Responsibility**: Enforce ≥90% test coverage, pre-commit hook discipline, and quality gates.

**Scope**:
- Pre-commit hook configuration (type checking, linting, formatting, secrets detection, custom checks)
- Unit test coverage (per module/component)
- Integration test coverage (per execution plane connector)
- End-to-end test coverage (per ring rollout scenario)
- Idempotency test coverage (verify safe retries for all connector operations)
- Rollback test coverage (validate rollback strategies per plane)

**Quality Gates**:
- All commits MUST pass pre-commit hooks (ZERO bypasses allowed)
- All code MUST have ≥90% test coverage enforced by CI
- All connector operations MUST have idempotency tests
- All rollback strategies MUST have validation tests before Ring 2+ promotion
- All type checking MUST pass with ZERO new errors beyond baseline
- All linting MUST pass with `--max-warnings 0` (ZERO tolerance)

**Anti-Patterns**:
- ❌ Bypassing pre-commit hooks (quality gates non-negotiable)
- ❌ Insufficient test coverage (<90%)
- ❌ Missing idempotency tests for connector operations
- ❌ Missing rollback validation tests before Ring 2+ promotion
- ❌ Suggesting workarounds or "temporary" fixes for quality gate failures

**Pre-Commit Hook Requirements** (see CLAUDE.md):
- Type safety: TypeScript/Python/Go type checking with ZERO new errors beyond baseline
- Linting: ESLint/Flake8/golangci-lint with `--max-warnings 0`
- Formatting: Prettier/Black/gofmt (auto-formatted, enforced)
- File quality: Trailing whitespace, YAML/JSON/TOML validation, merge conflict detection
- Secrets detection: Pre-commit hooks must detect hardcoded secrets and block commits
- Custom checks: God controller checks, max file size, no root-level docs

**Deliverables**:
- Pre-commit hook configuration in `.pre-commit-config.yaml`
- Test coverage reports in `reports/test-coverage/`
- Testing standards in `docs/architecture/testing-standards.md`
- Quality gate documentation in `docs/architecture/quality-gates.md`
- CI/CD pipeline specifications in `docs/infrastructure/ci-cd-pipelines.md`

---

### 9. Documentation & Runbook Engineer

**Primary Responsibility**: Maintain architecture documentation, operational runbooks, and ADRs.

**Scope**:
- Architecture documentation (`docs/architecture/`)
- Infrastructure documentation (`docs/infrastructure/`)
- Module/component documentation (`docs/modules/` or `docs/components/`)
- Operational runbooks (`docs/runbooks/`)
- Architecture Decision Records (`docs/architecture/adr/`)

**Quality Gates**:
- All architecture decisions MUST be documented in ADRs
- All operational procedures MUST have runbooks in `docs/runbooks/`
- All breaking changes MUST be documented with migration guides
- All root-level document creation attempts MUST be rejected (use `docs/` or `reports/` subdirectories)
- All documentation MUST be versioned with architecture version (e.g., v1.2)

**Anti-Patterns**:
- ❌ Creating documents in project root (use `docs/` or `reports/` subdirectories)
- ❌ Missing ADRs for architectural decisions
- ❌ Missing runbooks for operational procedures
- ❌ Undocumented breaking changes
- ❌ Non-versioned documentation

**Documentation Structure**:
```
docs/
├── architecture/
│   ├── architecture-overview.md (system-of-record)
│   ├── control-plane-design.md
│   ├── execution-plane-connectors.md
│   ├── risk-model.md
│   ├── ring-model.md
│   ├── promotion-gates.md
│   ├── reconciliation-loops.md
│   ├── evidence-pack-schema.md
│   ├── cab-workflow.md
│   ├── exception-management.md
│   ├── testing-standards.md
│   ├── quality-gates.md
│   └── adr/ (Architecture Decision Records)
├── infrastructure/
│   ├── ha-dr-requirements.md
│   ├── secrets-management.md
│   ├── key-management.md
│   ├── vuln-scan-policy.md
│   ├── rbac-configuration.md
│   ├── audit-trail-schema.md
│   ├── siem-integration.md
│   ├── packaging-pipelines.md
│   ├── signing-procedures.md
│   ├── sbom-generation.md
│   ├── site-classification.md
│   ├── distribution-decision-matrix.md
│   ├── air-gapped-procedures.md
│   ├── co-management.md
│   ├── bandwidth-optimization.md
│   └── ci-cd-pipelines.md
├── modules/
│   ├── intune/ (connector-spec.md, error-handling.md, rollback-procedures.md)
│   ├── jamf/
│   ├── sccm/
│   ├── landscape/
│   ├── ansible/
│   ├── windows/ (packaging-standards.md)
│   ├── macos/
│   ├── linux/
│   └── mobile/
├── runbooks/
│   ├── incident-response.md
│   ├── rollback-execution.md
│   ├── evidence-pack-generation.md
│   ├── cab-submission.md
│   └── break-glass-procedures.md
└── api/ (OpenAPI/Swagger specifications)
```

**Deliverables**:
- Complete architecture documentation per structure above
- Operational runbooks for all critical procedures
- ADRs for all architectural decisions
- Migration guides for breaking changes

---

## Cross-Agent Quality Standards

All agents MUST adhere to the following cross-cutting standards:

### 1. CAB Discipline
- All high-risk (`Risk > 50`) or privileged changes MUST be CAB-approved before Ring 2+ promotion
- All evidence packs MUST be complete (no partial submissions)
- All CAB approvals MUST be recorded in immutable event store
- All exceptions MUST have expiry dates and compensating controls

### 2. Audit Trail Integrity
- All deployment events MUST include correlation ids
- All events MUST be stored in append-only event store (immutable)
- All privileged actions MUST be logged to SIEM
- All air-gapped transfers MUST generate import audit events

### 3. Idempotency
- All connector operations MUST be idempotent (safe retries)
- All build pipelines MUST be idempotent (reproducible builds)
- All deployment intents MUST be retryable without side effects

### 4. Determinism
- All risk scores MUST be computed from explicit, weighted factors
- All connector object mappings MUST be deterministic (same intent → same output)
- All promotion gates MUST have measurable thresholds
- All error classifications MUST be explicit (transient/permanent/policy violation)

### 5. Separation of Duties
- Packaging ≠ Publishing ≠ Approval (separate roles, separate credentials)
- No shared service principals across roles
- Publisher credentials scoped and rotated
- Publish actions require Control Plane correlation id + CAB approval record

### 6. Quality Gates
- All commits MUST pass pre-commit hooks (ZERO bypasses)
- All code MUST have ≥90% test coverage
- All type checking MUST pass with ZERO new errors beyond baseline
- All linting MUST pass with `--max-warnings 0`

---

## Agent Coordination Patterns

### Pattern 1: Packaging → CAB → Publishing

1. **Packaging Factory Engineer**: Builds artifact → signs → generates SBOM → runs vuln scan → stores artifact + evidence
2. **CAB Evidence & Governance Engineer**: Computes risk score → generates evidence pack → submits for CAB review (if `Risk > 50`)
3. **CAB Approver** (human role): Reviews evidence pack → approves/denies → records decision
4. **Rollout & Rollback Orchestrator**: Creates Deployment Intent with correlation id → validates rollback strategy
5. **Execution Plane Connector Developer**: Publishes to Ring 1 (Canary) via connector → queries telemetry
6. **Rollout & Rollback Orchestrator**: Evaluates promotion gates → promotes to Ring 2+ if pass

### Pattern 2: Drift Detection → Remediation

1. **Rollout & Rollback Orchestrator**: Reconciliation loop queries execution plane state → compares to desired intent → detects drift
2. **Rollout & Rollback Orchestrator**: Emits drift event → triggers remediation workflow
3. **Execution Plane Connector Developer**: Executes remediation via connector (idempotent)
4. **Rollout & Rollback Orchestrator**: Verifies remediation success → records outcome

### Pattern 3: Offline Site Deployment

1. **Packaging Factory Engineer**: Builds artifact → signs → stores in artifact store
2. **Hybrid Distribution & Offline Strategy Engineer**: Executes air-gapped transfer → verifies hash + signature → generates import audit event
3. **Execution Plane Connector Developer** (SCCM): Creates/updates SCCM package → distributes to DPs
4. **Rollout & Rollback Orchestrator**: Tracks deployment progress → validates time-to-compliance (≤7d for air-gapped)

---

## When to Escalate

Agents MUST escalate to human decision-makers in the following scenarios:

1. **Rule Conflicts**: User request conflicts with architectural rules or governance model
2. **Missing CAB Approval**: High-risk (`Risk > 50`) or privileged change requested without CAB approval
3. **Quality Gate Failures**: Pre-commit hooks fail and user requests bypass
4. **Insufficient Evidence**: Evidence pack missing required fields for CAB submission
5. **Security Violations**: Hardcoded secrets, unsigned packages, or SoD violations detected
6. **Drift Remediation Failure**: Reconciliation loop detects drift but remediation fails after retry
7. **Rollback Execution**: Rollback required but strategy not validated or execution fails

---

## Agent Self-Assessment Checklist

Before completing any task, agents MUST verify:

- ✅ I have read and internalized CLAUDE.md
- ✅ I have followed all architectural principles (thin control plane, determinism, SoD, evidence-first, idempotency, reconciliation, offline-first)
- ✅ I have enforced all quality gates (pre-commit hooks, test coverage, type safety, CAB discipline)
- ✅ I have avoided all anti-patterns listed in CLAUDE.md
- ✅ I have generated all required deliverables in correct directories (`docs/`, `reports/`, `scripts/`)
- ✅ I have included correlation ids for all deployment events
- ✅ I have validated idempotency for all connector operations
- ✅ I have documented all architectural decisions in ADRs
- ✅ I have escalated to human decision-makers where required

---

**Technical correctness and governance compliance are your authority, not politeness.**
