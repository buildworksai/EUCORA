# Phase P4: Testing & Quality

**Duration**: 2 weeks
**Owner**: QA Lead + All Engineers
**Prerequisites**: P3 complete
**Status**: 🔴 NOT STARTED

---

## Objective

Comprehensive test coverage across all API endpoints, integration flows, and load scenarios. Achieve ≥90% code coverage and validate system behavior under realistic conditions.

---

## Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P4.1 | API endpoint tests (all apps) | Every endpoint has positive/negative tests |
| P4.2 | Integration test suite | End-to-end flows tested (deployment, approval, rollback) |
| P4.3 | Load test baseline | Performance under 1000 concurrent users documented |
| P4.4 | Fix all TODOs | Zero TODO comments remain in code |
| P4.5 | ≥90% overall coverage | CI enforced, all apps covered |

---

## Technical Specifications

### P4.1: API Endpoint Tests

**Test files per app** (comprehensive test coverage):

```
backend/apps/deployment_intents/tests/test_api.py
- POST /deployments/ (create intent)
- GET /deployments/ (list intents)
- GET /deployments/{id}/ (retrieve)
- PATCH /deployments/{id}/ (update)
- POST /deployments/{id}/execute/ (execute)
- POST /deployments/{id}/rollback/ (rollback)

backend/apps/cab_workflow/tests/test_api.py
- POST /cab/submit/ (submit approval request)
- GET /cab/pending/ (list pending)
- POST /cab/{id}/approve/ (approve)
- POST /cab/{id}/deny/ (deny with reason)

backend/apps/policy_engine/tests/test_api.py
- GET /policy/evaluate/ (policy evaluation)
- POST /policy/constraints/validate/ (constraint validation)

backend/apps/evidence_store/tests/test_api.py
- POST /evidence/ (generate evidence pack)
- GET /evidence/{id}/ (retrieve)
- PATCH /evidence/{id}/ (versioning)

backend/apps/event_store/tests/test_api.py
- GET /events/ (list events)
- GET /events/{id}/ (retrieve event)

backend/apps/connectors/tests/test_api.py
- POST /connectors/{id}/sync/ (trigger sync)
- GET /connectors/{id}/status/ (check status)

backend/apps/ai_agents/tests/test_api.py
- POST /agents/tasks/ (create task)
- GET /agents/tasks/{id}/ (get task)
- POST /agents/conversation/ (send message)
```

**Test pattern per endpoint**:
```python
class TestDeploymentIntentsAPI(TestCase):
    def test_create_deployment_intent_success(self):
        # Valid input → 201 created

    def test_create_deployment_intent_invalid_scope(self):
        # Invalid scope → 400 bad request

    def test_create_deployment_intent_unauthorized(self):
        # No auth → 401 unauthorized

    def test_create_deployment_intent_forbidden_scope(self):
        # Wrong role → 403 forbidden

    def test_list_deployments_pagination(self):
        # Cursor pagination works

    def test_get_deployment_not_found(self):
        # Non-existent → 404 not found
```

**Coverage requirements**:
- Happy path (valid input → expected output)
- Validation errors (400)
- Authentication (401 without auth)
- Authorization (403 for wrong role)
- Not found (404)
- Edge cases (empty lists, boundaries, max items)
- Pagination (cursor pagination)
- Sorting/filtering (where applicable)

### P4.2: Integration Tests

End-to-end flow validation:

```
backend/tests/integration/test_deployment_flow.py
- Create deployment intent
- Execute to Ring 1 (Canary)
- Monitor health checks
- Promote to Ring 2 (Pilot)
- Detect drift
- Execute remediation
- Verify reconciliation

backend/tests/integration/test_cab_approval_flow.py
- Create deployment intent with Risk > 50
- Generate evidence pack
- Submit to CAB
- Approve with conditions
- Create event store record
- Verify audit trail

backend/tests/integration/test_evidence_pack_flow.py
- Build artifact (package)
- Generate SBOM
- Run vulnerability scan
- Generate evidence pack
- Submit for CAB review
- Track evidence versions

backend/tests/integration/test_connector_services.py
- (Already exists, extend)
- ServiceNow integration
- Jira integration
- Circuit breaker activation
- Fallback behavior
```

### P4.3: Load Tests

Tool: **Locust** or **k6**

**Scenarios**:

```yaml
Scenario 1: Baseline (100 users, 10 RPS)
  - 100 concurrent users
  - 10 requests per second
  - Expected: <200ms p95 latency, 0% errors

Scenario 2: Moderate (500 users, 50 RPS)
  - 500 concurrent users
  - 50 requests per second
  - Expected: <500ms p95 latency, <1% errors

Scenario 3: Stress (1000 users, 100 RPS)
  - 1000 concurrent users
  - 100 requests per second
  - Expected: <1000ms p95 latency, <5% errors

Workload Mix:
  - 40% GET /deployments/
  - 20% POST /deployments/
  - 15% GET /health/
  - 10% POST /cab/approve/
  - 10% GET /events/
  - 5% GET /policy/evaluate/
```

**Metrics tracked**:
- Response times (p50, p90, p95, p99)
- Error rates (4xx, 5xx)
- Throughput (RPS)
- Resource utilization (CPU, memory, DB connections)
- Circuit breaker activation count

**Reporting**:
```
docs/reports/load-test-baseline.md
- Scenarios executed
- Results per scenario
- Bottleneck analysis
- Recommendations
```

### P4.4: TODO Resolution

All TODO comments must be either resolved or converted to tracked GitHub issues:

```bash
grep -r "TODO\|FIXME\|XXX" backend/apps/ --include="*.py" | grep -v ".pyc"
```

For each TODO:
- [ ] Resolve the issue (preferred)
- [ ] Convert to GitHub issue with label `tech-debt` if deferring
- [ ] Add issue number to code: `# ISSUE-123: Description`

### P4.5: Test Coverage

**Coverage target**: ≥90% (measured by pytest-cov)

**Per-app breakdown**:
```
apps/deployment_intents: ≥85% (high complexity, allowed lower)
apps/cab_workflow: ≥90%
apps/policy_engine: ≥90%
apps/evidence_store: ≥85%
apps/event_store: ≥95%
apps/connectors: ≥80% (integration complexity)
apps/ai_agents: ≥75% (AI complexity)
apps/core: ≥95% (critical utilities)
config/: ≥90% (settings, handlers)
```

**CI enforcement**:
```bash
pytest --cov=apps --cov=config --cov-fail-under=90
```

---

## Quality Gates

- [ ] ≥90% code coverage (CI enforced)
- [ ] All API tests pass (positive + negative cases)
- [ ] All integration tests pass
- [ ] Load test baseline completed
- [ ] Load test p95 latency < 500ms for 500 user scenario
- [ ] Zero TODOs remain in code
- [ ] No new linting errors
- [ ] Type checking passes (mypy)

---

## Files to Create/Modify

```
backend/
├── apps/deployment_intents/tests/
│   ├── test_api.py (CREATE) - Endpoint tests
│   └── test_models.py (EXISTS - extend)
├── apps/cab_workflow/tests/
│   └── test_api.py (CREATE)
├── apps/policy_engine/tests/
│   └── test_api.py (CREATE)
├── apps/evidence_store/tests/
│   └── test_api.py (CREATE)
├── apps/event_store/tests/
│   └── test_api.py (CREATE)
├── apps/connectors/tests/
│   └── test_api.py (CREATE)
├── apps/ai_agents/tests/
│   └── test_api.py (CREATE)
├── tests/integration/
│   ├── test_deployment_flow.py (CREATE)
│   ├── test_cab_approval_flow.py (CREATE)
│   ├── test_evidence_pack_flow.py (CREATE)
│   └── test_connector_services.py (EXISTS - extend)
└── tests/load/
    └── locustfile.py (CREATE)

docs/
└── reports/
    └── load-test-baseline.md (CREATE)
```

---

## Success Criteria

✅ **P4 is COMPLETE when**:
1. ≥90% code coverage across all apps
2. All endpoint tests pass (100+ tests)
3. All integration tests pass (10+ flows)
4. Load test baseline documented
5. Zero TODO comments in code
6. CI enforces coverage + linting
7. All quality gates green

**Target Completion**: 2 weeks (January 29-February 5, 2026)
