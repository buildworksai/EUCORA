# P4.2 Integration Testing Plan

**SPDX-License-Identifier: Apache-2.0**  
**Date**: 2026-01-22  
**Status**: ⏳ **READY TO COMMENCE**

---

## Overview

Phase P4.2 (Integration Testing) focuses on **end-to-end workflows** across multiple apps, testing the control plane and execution plane interactions.

**P4.1 API Tests** (143 tests, 7 apps) have been completed and verified.  
**P4.2 Integration Tests** will test 4 key scenarios combining multiple apps.

---

## P4.2 Scope

### 4 Key Integration Scenarios

#### Scenario 1: Deployment Flow
**Components**: deployment_intents + policy_engine + evidence_store + event_store

**Flow**:
1. Create deployment intent (POST /api/v1/deployments/)
2. Policy engine computes risk score
3. Evidence store queries artifact metadata
4. Event store logs DEPLOYMENT_CREATED event
5. CAB checks if approval needed (risk_score > 50)
6. Assertion: Deployment status is PENDING or AWAITING_CAB

**Tests** (4-5):
- ✅ Valid deployment flow succeeds
- ✅ High-risk deployment triggers CAB requirement
- ✅ Events logged in correct sequence
- ✅ Evidence pack linked to deployment
- ✅ Risk score computed deterministically

#### Scenario 2: CAB Approval Flow
**Components**: cab_workflow + deployment_intents + event_store

**Flow**:
1. Retrieve pending deployments (GET /api/v1/cab/pending/)
2. Approve deployment (POST /api/v1/cab/{id}/approve/)
3. Deployment status updated to APPROVED
4. Event store logs CAB_APPROVED event
5. Assertion: Deployment eligible for Ring 1 promotion

**Tests** (4-5):
- ✅ Approval updates deployment status
- ✅ Event store records approval decision
- ✅ Approver user field set correctly
- ✅ Conditional approvals with conditions stored
- ✅ Rejection updates status to REJECTED

#### Scenario 3: Evidence Pack Generation
**Components**: evidence_store + policy_engine + deployment_intents + cab_workflow

**Flow**:
1. Store evidence pack (POST /api/v1/evidence/store/)
2. Policy engine validates against policies
3. Risk score computed from evidence
4. Evidence pack linked to deployment
5. CAB submission prepared
6. Assertion: Complete evidence pack ready for approval

**Tests** (4-5):
- ✅ Evidence pack storage succeeds
- ✅ SBOM parsed and validated
- ✅ Scan results aggregated
- ✅ Risk factors extracted from evidence
- ✅ Evidence immutability enforced

#### Scenario 4: Connector Publishing Flow
**Components**: connectors + deployment_intents + event_store + policy_engine

**Flow**:
1. Create deployment intent (Ring 1 - Canary)
2. Evaluate promotion gates (success rate ≥98%)
3. Publish to Intune connector (POST /api/v1/connectors/publish/)
4. Connector returns deployment status
5. Event store logs DEPLOYMENT_PUBLISHED event
6. Assertion: Deployment tracking in execution plane

**Tests** (4-5):
- ✅ Publish to connector succeeds
- ✅ Correlation ID preserved through publication
- ✅ Connector returns status (success/failure/pending)
- ✅ Event store logs connector operation
- ✅ Remediation flow triggered on failure

---

## Test Implementation Structure

### Integration Test File Location

```
backend/apps/integration_tests/tests/test_integration_scenarios.py
```

### Test Class Structure

```python
class DeploymentFlowIntegrationTests(APITestCase):
    """Test end-to-end deployment flow."""
    def test_valid_deployment_flow_succeeds(self)
    def test_high_risk_deployment_requires_cab(self)
    def test_events_logged_in_sequence(self)
    def test_evidence_pack_linked_to_deployment(self)
    def test_risk_score_computed_deterministically(self)

class CABApprovalFlowIntegrationTests(APITestCase):
    """Test CAB approval workflow."""
    def test_approval_updates_deployment_status(self)
    def test_events_recorded_for_approval(self)
    def test_approver_field_set_correctly(self)
    def test_conditional_approval_stores_conditions(self)
    def test_rejection_updates_deployment_status(self)

class EvidencePackGenerationIntegrationTests(APITestCase):
    """Test evidence pack generation and validation."""
    def test_evidence_pack_storage_succeeds(self)
    def test_sbom_parsed_and_validated(self)
    def test_scan_results_aggregated(self)
    def test_risk_factors_extracted(self)
    def test_evidence_immutability_enforced(self)

class ConnectorPublishingFlowIntegrationTests(APITestCase):
    """Test connector publishing workflow."""
    def test_publish_to_connector_succeeds(self)
    def test_correlation_id_preserved(self)
    def test_connector_returns_status(self)
    def test_events_logged_for_publication(self)
    def test_remediation_triggered_on_failure(self)
```

**Total**: 18-22 integration tests (4-5 per scenario)

---

## Integration Test Requirements

### Cross-App State Verification

Each test must verify:

1. **Deployment Intent State**: Status transitions (PENDING → AWAITING_CAB → APPROVED → ACTIVE)
2. **CAB Approval State**: Decision tracking (PENDING → APPROVED/REJECTED/CONDITIONAL)
3. **Evidence Pack State**: Immutable storage and versioning
4. **Event Store State**: Chronological sequence and correlation IDs
5. **Policy Compliance**: Risk score computation and policy evaluation
6. **Connector State**: Publication status and sync with execution plane

### Database State Assertions

```python
# After deployment creation
self.assertEqual(deployment.status, DeploymentIntent.Status.PENDING)
self.assertIsNotNone(deployment.correlation_id)

# After policy check
self.assertGreaterEqual(deployment.risk_score, 0)
self.assertLessEqual(deployment.risk_score, 100)

# After CAB approval
self.assertEqual(cab_approval.decision, CABApproval.Decision.APPROVED)
self.assertEqual(cab_approval.approver, self.user)
self.assertIsNotNone(cab_approval.approval_timestamp)

# After evidence storage
self.assertEqual(evidence_pack.app_name, 'test-app')
self.assertIn('sbom', evidence_pack.evidence_data)

# After connector publish
self.assertIn('correlation_id', connector_status)
self.assertEqual(connector_status['status'], 'success')
```

### Event Store Sequence Validation

```python
# Events should be logged in chronological order
events = DeploymentEvent.objects.filter(
    correlation_id=deployment.correlation_id
).order_by('timestamp')

expected_sequence = [
    'DEPLOYMENT_CREATED',
    'POLICY_CHECK_COMPLETED',
    'CAB_SUBMISSION_PREPARED',
    'CAB_APPROVED',
    'DEPLOYMENT_PUBLISHED'
]

for i, expected_event in enumerate(expected_sequence):
    if i < len(events):
        self.assertEqual(events[i].event_type, expected_event)
```

---

## Success Criteria

### ✅ P4.2 Completion Criteria

- [ ] All 4 scenarios have integration tests (18-22 tests total)
- [ ] Each test verifies cross-app state changes
- [ ] Event store sequence correct (chronological, correlation IDs)
- [ ] No hardcoded test data (use factories or fixtures)
- [ ] ≥90% code coverage on all integration paths
- [ ] All integration tests pass on clean database
- [ ] Tests are deterministic (pass/fail same on repeat)
- [ ] Pre-commit hook validates integration tests

### Test Pass Rate Expectations

| Scenario | Tests | Expected Pass Rate |
|----------|-------|---|
| Deployment Flow | 5 | ≥95% |
| CAB Approval Flow | 5 | ≥95% |
| Evidence Generation | 5 | ≥95% |
| Connector Publishing | 7 | ≥90% |
| **TOTAL** | **22** | **≥92%** |

---

## Timeline

| Phase | Effort | Timeline | Status |
|-------|--------|----------|--------|
| **P4.1** (API Tests) | 12 hours | Jan 22 | ✅ **COMPLETE** |
| **P4.2** (Integration) | 8 hours | Jan 23-24 | ⏳ **NEXT** |
| **P4.3** (Load Testing) | 6 hours | Jan 25-26 | ⏳ Pending |
| **P4.4** (TODO Cleanup) | 4 hours | Jan 27 | ⏳ Pending |
| **P4.5** (Coverage Enforcement) | 6 hours | Jan 28 | ⏳ Pending |

---

## Dependencies & Blockers

### No Blockers 🟢

- ✅ All API tests complete (143 tests)
- ✅ Test database available (sqlite in development)
- ✅ All apps have models and views
- ✅ Event store implementation complete
- ✅ Evidence store implementation complete

---

## Risks & Mitigations

### Risk 1: Data Consistency Issues
**Risk**: Integration tests reveal that state changes aren't atomic across apps.  
**Mitigation**: Use database transactions in tests; verify with explicit assertions.

### Risk 2: Event Ordering Issues
**Risk**: Events logged out of chronological order.  
**Mitigation**: Add sequence number to events; verify ordering in tests.

### Risk 3: Idempotency Violations
**Risk**: Operations not idempotent, causing test failures on retry.  
**Mitigation**: Test all operations for idempotency in integration tests.

### Risk 4: Slow Test Execution
**Risk**: Integration tests take too long to run, slowing CI/CD.  
**Mitigation**: Parallelize tests where possible; use in-memory database for tests.

---

## Deliverables

### P4.2 Integration Test Suite

**File**: `backend/apps/integration_tests/tests/test_integration_scenarios.py`

**Contents**:
- DeploymentFlowIntegrationTests (5 tests)
- CABApprovalFlowIntegrationTests (5 tests)
- EvidencePackGenerationIntegrationTests (5 tests)
- ConnectorPublishingFlowIntegrationTests (7 tests)

**Total**: 22 integration tests

### P4.2 Completion Report

**File**: `reports/P4-INTEGRATION-TESTING-COMPLETE.md`

**Contents**:
- Summary of all 4 integration scenarios
- Test results and coverage metrics
- Architecture compliance verification
- Recommendations for P4.3+

---

## Next Actions

1. **Immediate** (Today):
   - Review P4.1 completion report
   - Plan P4.2 integration test cases

2. **This Week** (P4.2):
   - Implement 4 integration test scenarios (22 tests)
   - Verify cross-app state changes
   - Achieve ≥90% integration coverage

3. **Next Week** (P4.3-P4.5):
   - Load testing with Locust
   - TODO resolution
   - Coverage enforcement in CI/CD

---

## References

- **P4.1 API Tests**: [reports/P4-API-TESTING-COMPLETE.md](./P4-API-TESTING-COMPLETE.md)
- **Test Architecture**: [docs/architecture/testing-standards.md](../docs/architecture/testing-standards.md)
- **Quality Gates**: [docs/standards/quality-gates.md](../docs/standards/quality-gates.md)
- **Governance**: [CLAUDE.md](../CLAUDE.md)

---

**Status**: Ready to begin P4.2 Integration Testing  
**Estimated Completion**: Jan 24, 2026  
**Next Milestone**: P4.3 Load Testing (Jan 25-26)
