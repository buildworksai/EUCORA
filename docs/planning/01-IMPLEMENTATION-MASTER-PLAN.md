# EUCORA Implementation Master Plan

**SPDX-License-Identifier: Apache-2.0**  
**Copyright (c) 2026 BuildWorks.AI**

**Document Status**: AUTHORITATIVE — All implementation work derives from this plan  
**Created**: 2026-01-21  
**Authority**: Architecture Review Board + CAB

---

## Prerequisite Reading

Before reading this plan, you MUST have read:
1. [00-REQUIREMENTS-CRITICAL-REVIEW.md](00-REQUIREMENTS-CRITICAL-REVIEW.md) — The brutal truth about gaps
2. [CLAUDE.md](/CLAUDE.md) — Architecture governance (NON-NEGOTIABLE)
3. [AGENTS.md](/AGENTS.md) — Agent operating instructions

If you haven't read these, stop here. Reading this plan without context will lead to misaligned implementation.

---

## Implementation Philosophy

### Core Principle: Deliver Capabilities, Not Features

A feature is code that exists. A capability is code that works in production under load with audit trails and rollback plans.

**We deliver capabilities:**
- Every phase must result in production-deployable functionality
- Every phase must have ≥90% test coverage
- Every phase must include documentation and runbooks
- No phase is "complete" until CAB evidence standards are met

### The Three Questions for Every Change

Before any implementation work:
1. **Does this align with customer requirements?** (PRD, Architecture Spec)
2. **Does this comply with CLAUDE.md governance?** (Non-negotiable rules)
3. **Is this testable, observable, and auditable?** (Quality gates)

If any answer is "no" or "unclear" — STOP. Clarify before proceeding.

---

## Phase Overview (Revised)

| Phase | Name | Duration | Status | Dependency |
|-------|------|----------|--------|------------|
| **P0** | Security Emergency | DONE | ✅ Complete | None |
| **P1** | Database & Performance | DONE | ✅ Complete | P0 |
| **P2** | Resilience & Reliability | 1 week | ✅ Complete | P1 |
| **P3** | Observability & Operations | 1 week | ✅ Complete | P2 |
| **P4** | Testing & Quality | 2 weeks | 📋 Specified | P3 |
| **P5** | Evidence & CAB Workflow | 2 weeks | 📋 Specified | P4 |
| **P6** | Connector Implementation | 2 weeks | 📋 Specified | P5 |
| **P7** | Agent Foundation | 4 weeks | 📋 Specified | P6 |
| **P8** | Packaging Factory | 2 weeks | 📋 Specified | P7 |
| **P9** | AI Strategy Implementation | 3 weeks | 📋 Specified | P8 |
| **P10** | Scale Validation | 2 weeks | 📋 Specified | P9 |
| **P11** | Production Hardening | 1 week | 📋 Specified | P10 |
| **P12** | Final Validation & GO/NO-GO | 1 week | 📋 Specified | P11 |

**Total Timeline**: 22 weeks (5.5 months) — This is realistic, not aspirational.

---

## Phase Dependencies Graph

```
P0 (Security) ──────────────┐
                            ▼
P1 (Database) ─────────────►P2 (Resilience)
                            │
                            ▼
                     P3 (Observability)
                            │
                            ▼
                     P4 (Testing)
                            │
                            ▼
                     P5 (Evidence & CAB)
                            │
                            ▼
                     P6 (Connectors)
                            │
                            ▼
                     P7 (Agent Foundation)
                            │
                            ▼
                     P8 (Packaging Factory)
                            │
                            ▼
                     P9 (AI Strategy)
                            │
                            ▼
                     P10 (Scale Validation)
                            │
                            ▼
                     P11 (Production Hardening)
                            │
                            ▼
                     P12 (GO/NO-GO)
```

**CRITICAL**: No phase may begin until ALL previous phases are 100% complete with passing tests and documentation.

---

## Phase P2: Resilience & Reliability

**Duration**: 1 week  
**Owner**: Backend Lead + SRE  
**Prerequisites**: P0 + P1 complete  
**Status**: 🔴 NOT STARTED

### Objective
Make the system survive failures gracefully — external service outages, transient errors, and resource exhaustion must not cascade into system-wide failures.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P2.1 | Celery async tasks for heavy operations | All operations >5s are async with task ID response |
| P2.2 | Circuit breakers for external services | Breaker opens after 5 failures, resets after 60s |
| P2.3 | Retry logic with exponential backoff | All HTTP calls retry with 1-10s backoff (max 3) |
| P2.4 | Request timeouts everywhere | No operation can hang indefinitely |
| P2.5 | ≥90% test coverage on resilience components | Failure scenarios tested |

### Technical Specifications

**P2.1: Celery Async Tasks**
- Location: `backend/apps/connectors/tasks.py`, `backend/apps/ai_agents/tasks.py`
- Operations to make async:
  - Connector deployment execution
  - Risk score calculation  
  - AI chat completion
  - Integration sync (already async — verify)
- Response pattern: `HTTP 202 Accepted` with task ID
- Task status API: `/api/v1/tasks/{task_id}/status`

**P2.2: Circuit Breakers**
- Add dependency: `pybreaker~=1.0.1` to `pyproject.toml`
- Create: `backend/apps/integrations/circuit_breakers.py`
- Per-service breakers: ServiceNow, Jira, Intune, Jamf, Landscape
- Config: `fail_max=5`, `reset_timeout=60`

**P2.3: Retry Logic**
- Add dependency: `tenacity~=8.2.3` to `pyproject.toml`
- Apply to all HTTP calls in `backend/apps/integrations/services/`
- Config: `stop_after_attempt(3)`, `wait_exponential(min=1, max=10)`
- Classify errors: transient (5xx, timeout) vs permanent (4xx)

**P2.4: Timeouts**
- All `requests.get/post` calls: `timeout=30`
- Database: `statement_timeout=30000` in connection OPTIONS
- Redis: `socket_timeout=5` in cache config

### Quality Gates
- [ ] All tests pass
- [ ] ≥90% coverage on new code
- [ ] No new type errors
- [ ] Documentation updated
- [ ] Runbook for circuit breaker monitoring

### Files to Create/Modify
```
backend/apps/connectors/tasks.py (CREATE)
backend/apps/ai_agents/tasks.py (MODIFY)
backend/apps/integrations/circuit_breakers.py (CREATE)
backend/apps/integrations/services/base.py (MODIFY)
backend/config/settings/base.py (MODIFY - timeouts)
pyproject.toml (MODIFY - dependencies)
docs/runbooks/circuit-breaker-operations.md (CREATE)
```

---

## Phase P3: Observability & Operations

**Duration**: 1 week  
**Owner**: SRE + Backend Lead  
**Prerequisites**: P2 complete  
**Status**: 🔴 NOT STARTED

### Objective
See what's happening in production — structured logging, correlation IDs everywhere, error sanitization, and comprehensive health checks.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P3.1 | Structured JSON logging | All logs in JSON with correlation_id |
| P3.2 | Remove console statements | Zero console.log in production builds |
| P3.3 | Error response sanitization | No internal details exposed |
| P3.4 | Enhanced health checks | Verify ALL dependencies |
| P3.5 | ≥90% test coverage | Logging/health tested |

### Technical Specifications

**P3.1: Structured Logging**
- Backend: `pythonjsonlogger` formatter
- Required fields: `correlation_id`, `timestamp`, `level`, `service_name`, `user_id`
- Create: `backend/apps/core/logging.py` with middleware

**P3.2: Console Statement Removal**
- Create: `frontend/src/lib/logger.ts`
- Replace all `console.log/error/warn` with logger calls
- Production: Send to Sentry/LogRocket
- Development: Pass through to console

**P3.3: Error Sanitization**
- Pattern: `{'error': 'Internal server error', 'correlation_id': '...'}`
- Never expose: stack traces, SQL queries, file paths, internal state
- Always log: Full error context server-side with correlation_id

**P3.4: Health Checks**
- Endpoint: `/api/v1/health/`
- Checks: database, redis, celery workers, minio, external services (circuit breaker status)
- Response: 200 if healthy, 503 if degraded

### Quality Gates
- [ ] All tests pass
- [ ] ≥90% coverage
- [ ] Zero console.log in frontend bundle (verified)
- [ ] Health endpoint works with all services down (returns 503)

### Files to Create/Modify
```
backend/apps/core/logging.py (CREATE)
backend/apps/core/middleware.py (MODIFY)
backend/config/settings/base.py (MODIFY - logging config)
backend/apps/telemetry/views.py (MODIFY - health check)
frontend/src/lib/logger.ts (CREATE)
frontend/src/lib/api/client.ts (MODIFY)
frontend/src/routes/Login.tsx (MODIFY)
frontend/src/context/AuthContext.tsx (MODIFY)
docs/runbooks/log-analysis.md (CREATE)
```

---

## Phase P4: Testing & Quality

**Duration**: 2 weeks  
**Owner**: QA Lead + All Engineers  
**Prerequisites**: P3 complete  
**Status**: 🔴 NOT STARTED

### Objective
Know that the system works correctly — comprehensive API tests, integration tests, and load tests.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P4.1 | API endpoint tests (all apps) | Every endpoint has positive/negative tests |
| P4.2 | Integration test suite | End-to-end flows tested |
| P4.3 | Load test baseline | Performance under 1000 concurrent users documented |
| P4.4 | Fix all TODOs | Zero TODO comments remain |
| P4.5 | ≥90% overall coverage | CI enforced |

### Technical Specifications

**P4.1: API Endpoint Tests**
Required test files per app:
```
backend/apps/deployment_intents/tests/test_api.py
backend/apps/cab_workflow/tests/test_api.py
backend/apps/integrations/tests/test_api.py
backend/apps/ai_agents/tests/test_api.py
backend/apps/evidence_store/tests/test_api.py
backend/apps/policy_engine/tests/test_api.py
backend/apps/connectors/tests/test_api.py
backend/apps/event_store/tests/test_api.py
```

Each file must test:
- Authentication required (401 without auth)
- Authorization enforced (403 for wrong role)
- Valid input → expected output
- Invalid input → 400 with helpful error
- Edge cases (empty data, pagination boundaries)

**P4.2: Integration Tests**
```
backend/tests/integration/test_deployment_flow.py
backend/tests/integration/test_cab_approval_flow.py
backend/tests/integration/test_evidence_pack_flow.py
backend/tests/integration/test_connector_services.py (exists, extend)
```

**P4.3: Load Tests**
- Tool: locust or k6
- Scenarios:
  - 100 users, 10 RPS: baseline
  - 500 users, 50 RPS: moderate
  - 1000 users, 100 RPS: stress
- Document: response times, error rates, resource utilization

**P4.4: TODO Resolution**
- Search: `grep -r "TODO" backend/`
- Each TODO must be: resolved OR converted to tracked issue

### Quality Gates
- [ ] ≥90% coverage enforced by CI
- [ ] All API tests pass
- [ ] All integration tests pass
- [ ] Load test results documented
- [ ] Zero TODO comments

---

## Phase P5: Evidence & CAB Workflow

**Duration**: 2 weeks  
**Owner**: CAB Evidence & Governance Engineer  
**Prerequisites**: P4 complete  
**Status**: 🔴 NOT STARTED

### Objective
Implement evidence-first governance — every CAB submission has a complete, immutable evidence pack.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P5.1 | Evidence pack schema & models | All required fields per CLAUDE.md |
| P5.2 | Evidence pack generation service | Auto-generate packs for deployment intents |
| P5.3 | Risk scoring engine | Deterministic scoring per CLAUDE.md formula |
| P5.4 | CAB workflow enhancement | Complete approval flow with evidence |
| P5.5 | Immutable event store | Append-only audit trail |
| P5.6 | ≥90% test coverage | Evidence generation tested |

### Technical Specifications

**P5.1: Evidence Pack Schema**
Required fields (from CLAUDE.md):
- artifact hashes + signatures
- SBOM + vulnerability scan results + policy decision
- install/uninstall/detection documentation
- rollout plan (rings, schedule, targeting, exclusions)
- rollback plan (plane-specific)
- test evidence (lab + Ring 0 results)
- exception record(s) with expiry and compensating controls

Location: `backend/apps/evidence_store/models.py`

**P5.2: Evidence Generation**
- Service: `backend/apps/evidence_store/services.py`
- Auto-generate on: deployment intent creation, status change
- Storage: MinIO with immutable bucket policy

**P5.3: Risk Scoring**
Formula (from CLAUDE.md):
```
RiskScore = clamp(0..100, Σ(weight_i * normalized_factor_i))
```

Factors:
- Privilege impact (20)
- Supply chain trust (15)
- Exploitability (10)
- Data access (10)
- SBOM/vulnerability (15)
- Blast radius (10)
- Operational complexity (10)
- History (10)

Location: `backend/apps/policy_engine/services.py`

**P5.4: CAB Workflow Enhancement**
- Approval requires evidence pack reference
- Risk > 50 blocks Ring 2+ without CAB approval
- All approvals recorded with actor, timestamp, evidence reference

**P5.5: Event Store**
- Create: `backend/apps/event_store/models.py` — append-only events
- All deployment events logged with correlation_id
- Events cannot be modified or deleted (enforce via database constraints)

### Quality Gates
- [ ] Evidence pack generation works end-to-end
- [ ] Risk scoring is deterministic (same inputs = same output)
- [ ] Event store is truly append-only
- [ ] CAB approval enforced for Risk > 50
- [ ] ≥90% coverage

---

## Phase P6: Connector Implementation

**Duration**: 2 weeks  
**Owner**: Execution Plane Connector Developer  
**Prerequisites**: P5 complete  
**Status**: 🔴 NOT STARTED

### Objective
Connect to execution planes — Intune, Jamf, SCCM, Landscape, Ansible connectors that actually work with idempotent operations.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P6.1 | Intune connector | Graph API integration with Win32 app upload |
| P6.2 | Jamf connector | Jamf Pro API with OAuth |
| P6.3 | SCCM connector | PowerShell/REST provider integration |
| P6.4 | Landscape connector | Landscape API integration |
| P6.5 | Ansible connector | AWX/Tower API integration |
| P6.6 | All connectors: idempotent operations | Safe retries verified |
| P6.7 | ≥90% test coverage | Integration tests per connector |

### Technical Specifications

**Connector Interface (All)**
```python
class BaseConnector(ABC):
    @abstractmethod
    def deploy(self, payload: dict, correlation_id: str) -> DeployResult:
        """Idempotent deployment operation."""
    
    @abstractmethod
    def query_status(self, deployment_id: str) -> StatusResult:
        """Query deployment status."""
    
    @abstractmethod
    def rollback(self, deployment_id: str, correlation_id: str) -> RollbackResult:
        """Idempotent rollback operation."""
```

**P6.1: Intune Connector**
- Auth: Entra ID app registration (cert-based)
- API: Microsoft Graph (`microsoft.graph.win32LobApp`)
- Operations: Create app, upload package, create assignment
- Idempotency: Use `@microsoft.graph.conflictBehavior` header

**P6.2: Jamf Connector**
- Auth: OAuth / client credentials
- API: Jamf Pro API
- Operations: Create package, create policy, manage smart groups

**P6.3: SCCM Connector**
- Auth: Service account + constrained delegation
- API: PowerShell/REST provider
- SoD: Separate credentials from other connectors

**P6.4: Landscape Connector**
- Auth: Service account + API token
- Operations: Schedule deployments, compliance reporting

**P6.5: Ansible Connector**
- Auth: OAuth/token
- API: AWX/Tower API
- Operations: Trigger job templates, query job status

### Quality Gates
- [ ] Each connector has integration tests
- [ ] Idempotency verified (same operation twice = same result)
- [ ] Error classification: transient vs permanent
- [ ] Correlation ID in all audit events
- [ ] ≥90% coverage

---

## Phase P7: Agent Foundation

**Duration**: 4 weeks  
**Owner**: Agent Development Team  
**Prerequisites**: P6 complete  
**Status**: 🔴 NOT STARTED

### Objective
Build endpoint agents — the critical missing component for telemetry, deployment, and remediation.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P7.1 | Agent architecture design | Documented in ADR |
| P7.2 | Windows agent MVP | Telemetry collection, package deployment |
| P7.3 | macOS agent MVP | Telemetry collection, package deployment |
| P7.4 | Linux agent MVP | Telemetry collection, package deployment |
| P7.5 | Agent communication protocol | HTTPS/2 + mTLS |
| P7.6 | Offline queue with replay | Handles disconnected scenarios |
| P7.7 | ≥90% test coverage | Agent functionality tested |

### Technical Specifications

**Agent Requirements (All Platforms)**
- Language: Go (cross-platform, single binary)
- Communication: HTTPS/2 with mTLS
- Features:
  - Telemetry collection (device health, software inventory)
  - Package deployment execution
  - Remediation script execution
  - Offline queue with replay
  - Delta updates

**P7.2: Windows Agent**
- Telemetry: WMI queries for CPU, memory, disk, installed software
- Deployment: Execute MSI/MSIX/Win32 packages
- Remediation: Execute PowerShell scripts
- Service: Run as Windows Service

**P7.3: macOS Agent**
- Telemetry: sysctl, system_profiler
- Deployment: Execute PKG packages
- Remediation: Execute shell scripts
- Service: Run as LaunchDaemon

**P7.4: Linux Agent**
- Telemetry: procfs, apt/dpkg queries
- Deployment: apt install, dpkg
- Remediation: Execute shell scripts
- Service: Run as systemd service

### Quality Gates
- [ ] ADR documenting agent architecture
- [ ] Each agent collects telemetry correctly
- [ ] Each agent can execute deployments
- [ ] Offline mode works (queue, replay)
- [ ] ≥90% coverage

---

## Phase P8: Packaging Factory

**Duration**: 2 weeks  
**Owner**: Packaging Factory Engineer  
**Prerequisites**: P7 complete  
**Status**: 🔴 NOT STARTED

### Objective
Automated packaging pipeline — build, sign, scan, and store packages with supply chain controls.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P8.1 | Windows packaging pipeline | MSIX/Win32 with signing |
| P8.2 | macOS packaging pipeline | PKG with signing/notarization |
| P8.3 | Linux packaging pipeline | Signed APT packages |
| P8.4 | SBOM generation | SPDX/CycloneDX for all packages |
| P8.5 | Vulnerability scanning | Trivy/Grype integration |
| P8.6 | Artifact storage | MinIO with hash verification |
| P8.7 | ≥90% test coverage | Pipeline tested |

### Technical Specifications

**Packaging Pipeline (All)**
```
Intake → Build → Sign → SBOM → Scan → Policy Decision → Store
```

**Gates**:
- Block Critical/High vulnerabilities (default)
- Exceptions require: expiry date, compensating controls, Security Reviewer approval
- All artifacts stored with SHA-256 hash and metadata

**P8.1: Windows Pipeline**
- Input: MSI, EXE, MSIX
- Output: Signed Intune Win32 package
- Signing: Enterprise code-signing certificate

**P8.2: macOS Pipeline**
- Input: PKG, DMG
- Output: Signed + notarized PKG
- Signing: Apple Developer certificate

**P8.3: Linux Pipeline**
- Input: DEB, source
- Output: Signed APT package
- Signing: GPG key for APT repo

### Quality Gates
- [ ] All packages signed before publish
- [ ] SBOM generated for every package
- [ ] Vulnerability scan runs on every build
- [ ] Critical/High blocked without exception
- [ ] ≥90% coverage

---

## Phase P9: AI Strategy Implementation

**Duration**: 3 weeks  
**Owner**: AI/ML Engineer  
**Prerequisites**: P8 complete  
**Status**: 🔴 NOT STARTED

### Objective
Implement AI capabilities — either ML models or LLM-based, with governance controls.

### Strategic Decision Required
**Before this phase begins, leadership must decide:**
- **Option A**: Build ML infrastructure (model training, registry, drift detection)
- **Option B**: LLM-wrapper with prompt engineering and guardrails

This plan documents Option B (faster to market, lower capability ceiling).

### Deliverables (Option B: LLM Strategy)

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P9.1 | LLM provider abstraction | Switch providers without code changes |
| P9.2 | Prompt engineering framework | Documented prompts for each use case |
| P9.3 | Guardrails & safety | PII filtering, output validation |
| P9.4 | Evidence bundle generation | AI suggestions include evidence |
| P9.5 | Confidence scoring | All suggestions have confidence |
| P9.6 | Human-in-loop integration | High-risk requires approval |
| P9.7 | ≥90% test coverage | AI components tested |

### Technical Specifications

**P9.1: Provider Abstraction**
```python
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, context: dict) -> Completion:
        pass

class OpenAIProvider(LLMProvider): ...
class AzureOpenAIProvider(LLMProvider): ...
class LocalLlamaProvider(LLMProvider): ...  # For air-gapped
```

**P9.2: Prompt Framework**
- Use cases: incident classification, remediation suggestion, KB search
- Prompts documented in `backend/apps/ai_agents/prompts/`
- Prompt versioning for A/B testing

**P9.3: Guardrails**
- Input: PII detection and masking
- Output: Validation against expected schema
- Safety: Block harmful suggestions

**P9.4: Evidence Generation**
AI suggestions must include:
- Input context (what the AI saw)
- Model used (version, provider)
- Confidence score
- Reasoning chain (if available)

### Quality Gates
- [ ] Provider can be changed via config
- [ ] Prompts are documented and versioned
- [ ] PII is never sent to external LLMs
- [ ] All suggestions have evidence
- [ ] ≥90% coverage

---

## Phase P10: Scale Validation

**Duration**: 2 weeks  
**Owner**: SRE + Performance Engineer  
**Prerequisites**: P9 complete  
**Status**: 🔴 NOT STARTED

### Objective
Prove the system works at scale — 10k devices, 50k devices, then 100k devices.

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P10.1 | 10k device simulation | System stable under 10k device load |
| P10.2 | 50k device simulation | System stable under 50k device load |
| P10.3 | 100k device simulation | System stable under 100k device load |
| P10.4 | Horizontal scaling config | Auto-scaling rules documented |
| P10.5 | Performance baseline | Latency/throughput documented |

### Technical Specifications

**Simulation Tool**
- Create agent simulator that mimics telemetry patterns
- Configure: 10k, 50k, 100k simulated agents
- Measure: API latency, database load, queue depth

**Performance Targets**
- API latency p95: <500ms
- Telemetry ingestion: <1 minute freshness
- Deployment intent creation: <2s
- CAB approval: <1s

**Scaling Rules**
- API pods: scale on CPU >70%
- Celery workers: scale on queue depth >1000
- Database: read replicas for list queries

### Quality Gates
- [ ] 10k simulation passes all targets
- [ ] 50k simulation passes all targets
- [ ] 100k simulation passes all targets
- [ ] Scaling rules documented
- [ ] Performance baseline documented

---

## Phase P11: Production Hardening

**Duration**: 1 week  
**Owner**: Security + SRE  
**Prerequisites**: P10 complete  
**Status**: 🔴 NOT STARTED

### Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P11.1 | Penetration test | No critical/high findings |
| P11.2 | DR/backup validation | RPO ≤24h, RTO ≤8h verified |
| P11.3 | Secret rotation test | Secrets can be rotated without downtime |
| P11.4 | SIEM integration | All security events forwarded |
| P11.5 | Break-glass procedures | Documented and tested |

---

## Phase P12: Final Validation & GO/NO-GO

**Duration**: 1 week  
**Owner**: Architecture Review Board  
**Prerequisites**: P11 complete  
**Status**: 🔴 NOT STARTED

### GO Criteria

**All must be TRUE:**
- [ ] All phases P2-P11 complete with acceptance criteria met
- [ ] ≥90% test coverage across all code
- [ ] Zero critical security findings
- [ ] Performance targets met at 100k scale
- [ ] DR tested successfully
- [ ] All runbooks complete
- [ ] CAB evidence standards met for platform release

### NO-GO Triggers

**Any of these = NO-GO:**
- Test coverage <90%
- Critical security findings unresolved
- Performance targets missed at 50k scale
- DR test failed
- Missing runbooks for critical operations

---

## Cross-Phase Quality Standards

### Every Phase Must Have:

1. **Test Coverage ≥90%** — enforced by CI
2. **Documentation** — architecture decisions, runbooks, API docs
3. **Observability** — metrics, logs, traces for new components
4. **Security Review** — no hardcoded secrets, proper auth
5. **CAB Evidence** — compliance with CLAUDE.md governance

### Phase Completion Checklist

Before marking any phase complete:
- [ ] All deliverables completed
- [ ] All acceptance criteria met
- [ ] Test coverage ≥90% verified
- [ ] No new type errors
- [ ] No new linting warnings
- [ ] Documentation updated
- [ ] Runbooks created/updated
- [ ] Deployed to staging
- [ ] Verified in staging
- [ ] Phase sign-off from Tech Lead

---

## Risk Management

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Agent development delays | High | Critical | Start P7 planning now; consider off-the-shelf |
| Scale targets missed | Medium | High | Incremental validation; adjust targets early |
| AI strategy unclear | High | Medium | Force decision before P9 |
| Security findings in pen test | Medium | High | Security review each phase |
| Resource constraints | High | High | Phase work serially; no parallelization |

---

## Governance & Reporting

### Weekly Status Reports
Each phase owner reports weekly:
- Progress vs. plan
- Blockers
- Risk items
- Next week's targets

### Phase Gate Reviews
At phase completion:
- Demo of deliverables
- Test results review
- Documentation review
- Security review
- GO/NO-GO decision for next phase

### Escalation Path
If blocked:
1. Phase owner escalates to Tech Lead
2. Tech Lead escalates to Engineering Manager
3. Engineering Manager escalates to CTO

---

## Appendix: Phase Document Index

| Phase | Specification Document |
|-------|------------------------|
| P2 | [02-PHASE-P2-RESILIENCE.md](02-PHASE-P2-RESILIENCE.md) |
| P3 | [03-PHASE-P3-OBSERVABILITY.md](03-PHASE-P3-OBSERVABILITY.md) |
| P4 | [04-PHASE-P4-TESTING.md](04-PHASE-P4-TESTING.md) |
| P5 | [05-PHASE-P5-EVIDENCE-CAB.md](05-PHASE-P5-EVIDENCE-CAB.md) |
| P6 | [06-PHASE-P6-CONNECTORS.md](06-PHASE-P6-CONNECTORS.md) |
| P7 | [07-PHASE-P7-AGENTS.md](07-PHASE-P7-AGENTS.md) |
| P8 | [08-PHASE-P8-PACKAGING.md](08-PHASE-P8-PACKAGING.md) |
| P9 | [09-PHASE-P9-AI.md](09-PHASE-P9-AI.md) |
| P10 | [10-PHASE-P10-SCALE.md](10-PHASE-P10-SCALE.md) |
| P11 | [11-PHASE-P11-HARDENING.md](11-PHASE-P11-HARDENING.md) |
| P12 | [12-PHASE-P12-FINAL.md](12-PHASE-P12-FINAL.md) |

---

**This plan is authoritative. Deviations require Architecture Review Board approval.**
