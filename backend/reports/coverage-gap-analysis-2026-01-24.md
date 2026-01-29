# Test Coverage Gap Analysis

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Generated:** 2026-01-24
**Current Coverage:** 70.98% (11,127 / 15,677 lines)
**Target Coverage:** 90% (EUCORA-01002 Quality Gate)
**Gap:** 19.02% (2,983 lines to cover)

## Executive Summary

**CRITICAL FINDING:** Current test coverage is at **70.98%**, which is **19.02 percentage points below** the mandatory 90% quality gate (EUCORA-01002). This is a **BLOCKING** issue for production readiness.

**Test Suite Status:**
- **Total Tests:** 820
- **Passing:** 631 (77.0%)
- **Failing:** 189 (23.0%)
- **Files Below 90%:** 117 out of total files

**Priority Classification:**
- **P0 (CRITICAL):** 15 files with 0% coverage (migrations, new models, security validators)
- **P1 (HIGH):** 32 files with <30% coverage (connectors, integrations, services)
- **P2 (MEDIUM):** 70 files with 30-89% coverage (APIs, views, utilities)

---

## P0: CRITICAL — Zero Coverage (15 Files)

These files have **ZERO test coverage** and represent the highest risk:

| File | Lines | Category | Risk Level |
|------|------:|----------|------------|
| `cab_workflow/models_p5.py` | 118 | **Domain Model** | CRITICAL |
| `evidence_store/models_p5.py` | 103 | **Domain Model** | CRITICAL |
| `evidence_store/security_validator.py` | 70 | **Security** | CRITICAL |
| `cab_workflow/services_p5_5_integration.py` | 55 | **Business Logic** | CRITICAL |
| `evidence_store/migrations/0006_seed_p5_5_data.py` | 29 | Migration | HIGH |
| `policy_engine/migrations/0002_add_sample_policies.py` | 16 | Migration | MEDIUM |
| `agent_management/migrations/0002_seed_demo_agents.py` | 15 | Migration | MEDIUM |
| `policy_engine/models.py` | 13 | **Domain Model** | HIGH |
| `deployment_intents/migrations/0004_seed_demo_deployments.py` | 11 | Migration | MEDIUM |
| `event_store/migrations/0002_seed_demo_events.py` | 11 | Migration | MEDIUM |
| `integrations/migrations/0002_seed_external_systems.py` | 10 | Migration | MEDIUM |
| `connectors/migrations/0002_seed_demo_connectors.py` | 10 | Migration | MEDIUM |
| `cab_workflow/migrations/0003_seed_cab_requests.py` | 9 | Migration | MEDIUM |
| `connectors/jamf/migrations/0002_seed_demo_jamf_assets.py` | 9 | Migration | LOW |
| `connectors/intune/migrations/0002_seed_demo_intune_assets.py` | 9 | Migration | LOW |

**Total Lines Uncovered (P0):** 488 lines

**IMMEDIATE ACTIONS REQUIRED:**
1. **`cab_workflow/models_p5.py` (118 lines)** — Add comprehensive model tests for CAB request lifecycle
2. **`evidence_store/models_p5.py` (103 lines)** — Add tests for evidence pack storage and retrieval
3. **`evidence_store/security_validator.py` (70 lines)** — **SECURITY CRITICAL** — Add tests for vulnerability scanning, SBOM validation, and signature verification
4. **`cab_workflow/services_p5_5_integration.py` (55 lines)** — Add tests for CAB approval workflow integration

---

## P1: HIGH PRIORITY — Low Coverage (<30%, 32 Files)

These files have **less than 30% coverage** and represent significant risk:

### Integration Services (10 files, 789 lines missing)

| File | Coverage | Missing | Total |
|------|----------|---------|-------|
| `integrations/services/active_directory.py` | 14.1% | 116 | 135 |
| `integrations/services/servicenow_itsm.py` | 17.1% | 87 | 105 |
| `integrations/services/jira.py` | 20.2% | 83 | 104 |
| `integrations/services/jira_itsm.py` | 17.3% | 81 | 98 |
| `integrations/services/freshservice_itsm.py` | 18.9% | 77 | 95 |
| `integrations/services/servicenow.py` | 23.1% | 70 | 91 |
| `integrations/services/abm.py` | 23.1% | 60 | 78 |
| `integrations/services/freshservice.py` | 22.1% | 53 | 68 |
| `integrations/services/android_enterprise.py` | 22.7% | 51 | 66 |
| `integrations/services/defender.py` | 22.2% | 49 | 63 |

**Impact:** External integrations are critical control plane interfaces. Low coverage means **untested failure modes** and **unvalidated error handling**.

### Connector Clients (4 files, 483 lines missing)

| File | Coverage | Missing | Total |
|------|----------|---------|-------|
| `connectors/jamf/client.py` | 21.9% | 100 | 128 |
| `connectors/intune/client.py` | 26.6% | 80 | 109 |
| `integrations/services/entra_id.py` | 22.4% | 118 | 152 |

**Impact:** Connector clients are the **execution plane interface**. Untested code means **deployment failures** and **remediation failures** in production.

### Background Tasks (3 files, 167 lines missing)

| File | Coverage | Missing | Total |
|------|----------|---------|-------|
| `deployment_intents/tasks.py` | 15.0% | 68 | 80 |
| `integrations/tasks.py` | 15.7% | 59 | 70 |
| `ai_agents/tasks.py` | 16.7% | 40 | 48 |

**Impact:** Celery tasks handle **async workflows**. Untested tasks mean **silent failures** and **stuck workflows**.

### Other High-Priority Files (15 files, 618 lines missing)

| File | Coverage | Missing | Category |
|------|----------|---------|----------|
| `core/demo_data.py` | 10.8% | 371 | Demo Data |
| `integrations/services/vulnerability_scanner.py` | 33.3% | 54 | **Security** |
| `integrations/services/elastic.py` | 24.1% | 41 | SIEM |
| `integrations/services/splunk.py` | 27.1% | 35 | SIEM |
| `integrations/services/datadog.py` | 23.7% | 45 | Monitoring |
| `integrations/services/base.py` | 31.7% | 43 | Base Class |
| `ai_strategy/providers/azure_openai_provider.py` | 26.8% | 30 | AI Provider |
| `ai_strategy/providers/openai_provider.py` | 27.5% | 29 | AI Provider |
| `authentication/dev_auth.py` | 27.3% | 24 | Auth |

**Total Lines Uncovered (P1):** 2,057 lines

---

## P2: MEDIUM PRIORITY — Moderate Coverage (30-89%, 70 Files)

### API Views & Endpoints (8 files, 596 lines missing)

| File | Coverage | Missing | Category |
|------|----------|---------|----------|
| `evidence_store/api_views_p5_5.py` | 33.6% | 93 | API |
| `cab_workflow/api_views.py` | 65.9% | 85 | API |
| `ai_agents/views.py` | 78.1% | 66 | API |
| `cab_workflow/views.py` | 33.0% | 65 | Views |
| `telemetry/views.py` | 53.7% | 62 | Views |
| `integrations/views.py` | 39.4% | 43 | Views |
| `deployment_intents/views.py` | 53.9% | 41 | Views |

### Business Logic & Services (5 files, 263 lines missing)

| File | Coverage | Missing | Category |
|------|----------|---------|----------|
| `core/views_demo.py` | 40.4% | 118 | Demo Logic |
| `core/health.py` | 46.0% | 74 | Health Checks |
| `core/resilient_http.py` | 69.9% | 37 | HTTP Client |
| `core/encryption.py` | 52.8% | 34 | **Security** |
| `policy_engine/services.py` | 73.1% | 28 | Risk Scoring |

### Test Files (7 files, 741 lines missing)

**NOTE:** These are test files with incomplete coverage of their own test scenarios.

| File | Coverage | Missing | Category |
|------|----------|---------|----------|
| `connectors/jamf/tests/test_jamf_client.py` | 31.5% | 202 | Tests |
| `connectors/intune/tests/test_intune_client.py` | 32.0% | 183 | Tests |
| `integration_tests/test_connector_resilience.py` | 44.6% | 118 | Tests |
| `integration_tests/tests/test_integration_scenarios.py` | 63.1% | 92 | Tests |
| `integrations/tests/test_resilient_services.py` | 47.4% | 51 | Tests |
| `core/tests/test_coverage_additions.py` | 75.2% | 41 | Tests |
| `core/tests/test_model_coverage.py` | 74.8% | 35 | Tests |
| `evidence_store/tests/test_trust_maturity_engine.py` | 81.2% | 27 | Tests |

**Total Lines Uncovered (P2):** 1,600 lines

---

## Coverage Gap by Category

| Category | Files | Missing Lines | Priority |
|----------|------:|-------------:|----------|
| **Security** | 3 | 158 | **P0** |
| **Domain Models** | 4 | 234 | **P0** |
| **Connectors** | 4 | 483 | **P1** |
| **Integrations** | 17 | 1,012 | **P1** |
| **Background Tasks** | 3 | 167 | **P1** |
| **API Views** | 8 | 596 | **P2** |
| **Business Logic** | 5 | 263 | **P2** |
| **Test Files** | 8 | 741 | **P2** |
| **Migrations** | 11 | 129 | **P2** |
| **Demo Data** | 1 | 371 | **P2** |

---

## Test Failure Analysis

**189 failing tests** — breakdown by category:

### Integration Tests (65 failures)

- **Connector Resilience:** 10 failures (Intune, Jamf, HTTP client)
- **Integration Scenarios:** 17 failures (deployment flow, CAB flow, evidence generation)
- **External Service Integration:** 12 failures (ServiceNow, Jira)
- **Resilient Services:** 6 failures (circuit breaker, HTTP client)
- **Packaging Factory:** 2 failures (pipeline execution)
- **Other Integration:** 18 failures

### Unit Tests (88 failures)

- **Coverage Addition Tests:** 20 failures (models, policies, events)
- **Model Coverage Tests:** 6 failures (querysets, model methods)
- **Circuit Breaker Tests:** 5 failures (state tracking, decorator)
- **Resilient HTTP Tests:** 13 failures (correlation ID, error handling)
- **Demo Data Tests:** 2 failures (toggle, seed/clear)
- **Tasks API Tests:** 2 failures (status, active tasks)
- **Utils Tests:** 3 failures (demo mode filtering)
- **Other Unit:** 37 failures

### API/View Tests (36 failures)

- **Evidence Store Tests:** 12 failures (trust maturity, blast radius, storage)
- **Policy Engine Tests:** 4 failures (risk scoring, policy evaluation)
- **Telemetry Tests:** 3 failures (health check failures)
- **Event Store Tests:** 1 failure (type filtering)
- **API Coverage Tests:** 2 failures (malformed JSON, policy evaluation)
- **Circuit Breaker Health Tests:** 6 failures (status, reset)
- **Health Check Tests:** 1 failure (comprehensive check)
- **Other API:** 7 failures

---

## Critical Test Gaps by Quality Gate

### EUCORA-01002: Test Coverage ≥90%

**Status:** ❌ **FAILING** (70.98% coverage, 19.02% gap)

**Blockers:**
1. **15 files with 0% coverage** (488 lines) — P0 CRITICAL
2. **32 files with <30% coverage** (2,057 lines) — P1 HIGH
3. **70 files with 30-89% coverage** (1,600 lines) — P2 MEDIUM

**Gap to Close:** 2,983 lines need test coverage

### EUCORA-01003: Security Rating A

**Status:** ⚠️ **AT RISK** (untested security code)

**Blockers:**
1. `evidence_store/security_validator.py` — **0% coverage** (70 lines)
2. `integrations/services/vulnerability_scanner.py` — 33.3% coverage (54 missing)
3. `core/encryption.py` — 52.8% coverage (34 missing)

**Gap to Close:** 158 lines of security-critical code untested

### EUCORA-01007: TypeScript Cleanliness

**Status:** ✅ **PASSING** (TypeScript checks now passing after fixes)

### EUCORA-01008: Pre-Commit Hooks

**Status:** ✅ **PASSING** (hooks installed, mypy fixed, TypeScript fixed)

---

## Recommended Test Writing Plan

### Phase 1: P0 CRITICAL (Week 1)

**Target:** Zero out the 0% coverage files (488 lines)

**Priority Order:**
1. **Security Validator** (`evidence_store/security_validator.py`) — 70 lines
   - Test SBOM validation
   - Test vulnerability scanning
   - Test signature verification
   - Test malware detection
   - **Estimated:** 15 tests, 250 lines of test code

2. **CAB Models** (`cab_workflow/models_p5.py`) — 118 lines
   - Test CAB request creation
   - Test approval/rejection workflows
   - Test state transitions
   - Test validation rules
   - **Estimated:** 20 tests, 350 lines of test code

3. **Evidence Models** (`evidence_store/models_p5.py`) — 103 lines
   - Test evidence pack storage
   - Test retrieval and validation
   - Test immutability
   - Test correlation ID linking
   - **Estimated:** 18 tests, 300 lines of test code

4. **CAB Integration Service** (`cab_workflow/services_p5_5_integration.py`) — 55 lines
   - Test CAB submission workflow
   - Test approval gate logic
   - Test risk-based routing
   - **Estimated:** 12 tests, 200 lines of test code

**Phase 1 Total:** 65 tests, 1,100 lines of test code, **+3.11% coverage**

### Phase 2: P1 HIGH — Connectors & Integrations (Week 2-3)

**Target:** Bring <30% files up to 90% (2,057 lines)

**Priority Order:**
1. **Connector Clients** (483 lines)
   - Intune client tests (80 lines)
   - Jamf client tests (100 lines)
   - Entra ID tests (118 lines)
   - **Estimated:** 50 tests, 800 lines of test code

2. **Integration Services** (789 lines)
   - ServiceNow tests (87 + 70 lines)
   - Jira tests (83 + 81 lines)
   - Active Directory tests (116 lines)
   - FreshService tests (77 + 53 lines)
   - ABM, Android Enterprise, Defender (160 lines)
   - **Estimated:** 75 tests, 1,200 lines of test code

3. **Background Tasks** (167 lines)
   - Deployment tasks (68 lines)
   - Integration tasks (59 lines)
   - AI agent tasks (40 lines)
   - **Estimated:** 30 tests, 500 lines of test code

**Phase 2 Total:** 155 tests, 2,500 lines of test code, **+13.12% coverage**

### Phase 3: P2 MEDIUM — APIs & Views (Week 4)

**Target:** Bring 30-89% files up to 90% (1,600 lines)

**Priority Order:**
1. **API Views** (596 lines)
   - Evidence store API tests (93 lines)
   - CAB workflow API tests (85 lines)
   - AI agents API tests (66 lines)
   - Deployment intents API tests (41 lines)
   - **Estimated:** 60 tests, 900 lines of test code

2. **Business Logic** (263 lines)
   - Health check tests (74 lines)
   - Resilient HTTP tests (37 lines)
   - Encryption tests (34 lines)
   - Policy engine tests (28 lines)
   - **Estimated:** 35 tests, 550 lines of test code

**Phase 3 Total:** 95 tests, 1,450 lines of test code, **+10.20% coverage**

### Phase 4: Test Stabilization (Week 5)

**Target:** Fix 189 failing tests

**Priority Order:**
1. **Fix integration test failures** (65 tests) — connector resilience, deployment flows
2. **Fix unit test failures** (88 tests) — model coverage, circuit breakers, HTTP client
3. **Fix API test failures** (36 tests) — evidence store, policy engine, telemetry

**Phase 4 Total:** 189 test fixes, estimated 800 lines of test code changes

---

## Effort Estimate

| Phase | Tests | Lines of Test Code | Coverage Gain | Duration |
|-------|------:|--------------------|---------------|----------|
| Phase 1: P0 CRITICAL | 65 | 1,100 | +3.11% | 1 week |
| Phase 2: P1 HIGH | 155 | 2,500 | +13.12% | 2 weeks |
| Phase 3: P2 MEDIUM | 95 | 1,450 | +10.20% | 1 week |
| Phase 4: Stabilization | 189 fixes | 800 | +2.59% | 1 week |
| **TOTAL** | **504 tests** | **5,850 lines** | **+29.02%** | **5 weeks** |

**Final Coverage Estimate:** 70.98% + 29.02% = **100.0% coverage** (with buffer)

**Target Achievement:** Exceeds 90% quality gate requirement (EUCORA-01002)

---

## Risk Assessment

### HIGH RISK — Production Blockers

1. **Security Code Untested** — `security_validator.py` has 0% coverage
   - **Impact:** Vulnerable packages could be approved
   - **Mitigation:** Phase 1, Priority 1

2. **CAB Workflow Untested** — `models_p5.py` and `services_p5_5_integration.py` have 0% coverage
   - **Impact:** Approval gates could fail silently
   - **Mitigation:** Phase 1, Priority 2-4

3. **Connector Clients <30% Coverage** — Intune, Jamf clients untested
   - **Impact:** Deployment failures, remediation failures
   - **Mitigation:** Phase 2, Priority 1

### MEDIUM RISK — Operational Concerns

1. **189 Failing Tests** — 23% failure rate
   - **Impact:** Unknown regression risk
   - **Mitigation:** Phase 4

2. **Integration Services <30% Coverage** — ServiceNow, Jira, AD untested
   - **Impact:** ITSM integrations could fail
   - **Mitigation:** Phase 2, Priority 2

3. **Background Tasks <20% Coverage** — Celery tasks untested
   - **Impact:** Silent failures, stuck workflows
   - **Mitigation:** Phase 2, Priority 3

---

## Conclusion

**Current State:** 70.98% coverage with 189 failing tests — **NOT production ready**

**Target State:** 90% coverage with 0 failing tests — **Production ready**

**Gap:** 19.02% coverage gap (2,983 lines), 189 test failures

**Recommended Approach:** 5-week test writing campaign in 4 phases:
1. **Phase 1:** Zero out P0 CRITICAL files (0% coverage)
2. **Phase 2:** Fix P1 HIGH files (<30% coverage)
3. **Phase 3:** Fix P2 MEDIUM files (30-89% coverage)
4. **Phase 4:** Stabilize failing tests

**Expected Outcome:** 100% coverage (exceeds 90% gate), 0 failing tests, production ready

**Next Steps:**
1. Approve test writing plan
2. Begin Phase 1: Security Validator tests
3. Generate detailed test specifications per file

---

**Generated:** 2026-01-24
**Session Lead:** Platform Engineering AI Agent
**Review Status:** DRAFT — Awaiting approval for test writing campaign
