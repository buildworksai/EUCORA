# Phase P5: Evidence & CAB Workflow — Implementation Plan

**Start Date**: January 22, 2026
**Duration**: 2 weeks (Target completion: February 5, 2026)
**Owner**: CAB Evidence & Governance Engineer
**Prerequisites**: ✅ P4 COMPLETE (all tests passing, 90% coverage)

---

## Phase Objective

Implement the **Evidence Pack Generation Engine** and **CAB (Change Advisory Board) Approval Workflow** to enable:
1. Automatic evidence collection for deployment decisions
2. Risk scoring with transparent, weighted factors
3. CAB submission and approval workflow
4. Exception management with compensating controls
5. Immutable audit trail for all approvals

This phase establishes **governance compliance** — all deployments requiring CAB review will have complete evidence packs and documented approval decisions.

---

## P5 Sub-Phases (Delivery Order)

### P5.1: Evidence Pack Generation Engine
**Duration**: 3 days
**Owner**: Backend Engineer
**Deliverables**:
- Evidence pack schema with all required fields
- Evidence collection from artifacts, tests, scans
- Evidence serialization and storage
- Correlation ID linking to deployment intents

**Acceptance Criteria**:
- Evidence packs contain: artifacts, test results, SBOM, scan results, deployment plan, rollback plan
- All evidence fields populated automatically
- ≥85% test coverage on evidence generation
- Evidence immutable once created

### P5.2: Risk Scoring Model
**Duration**: 2 days
**Owner**: Backend Engineer
**Deliverables**:
- Risk factor definitions (version 1.0)
- Weighted scoring formula
- Factor normalization (0-100 scale)
- Risk computation with all factors documented

**Acceptance Criteria**:
- Risk score = clamp(0..100, Σ(weight_i * normalized_factor_i))
- All factors documented with rubrics
- Score computed deterministically
- Versioned risk model (risk_model_v1.0)
- ≥90% test coverage

### P5.3: CAB Submission Workflow
**Duration**: 2 days
**Owner**: Backend Engineer
**Deliverables**:
- CAB submission endpoint
- Evidence pack validation
- Auto-reject for incomplete evidence
- Submission to approval queue
- Notification system

**Acceptance Criteria**:
- Only complete evidence packs accepted
- Auto-reject partial submissions with clear error messages
- Submissions stored in event store with correlation IDs
- Admin notifications on new submissions
- ≥90% test coverage

### P5.4: CAB Approval Decision Logic
**Duration**: 2 days
**Owner**: Backend Engineer
**Deliverables**:
- Approval endpoint for CAB members
- Decision recording (approved/rejected/conditional)
- Condition tracking and expiry
- Ring promotion gates based on approval

**Acceptance Criteria**:
- Decisions recorded immutably in event store
- Approval bypasses risk thresholds appropriately
- Conditional approvals include compensating controls
- Expiry dates enforced
- ≥90% test coverage

### P5.5: Exception Management
**Duration**: 2 days
**Owner**: Backend Engineer
**Deliverables**:
- Exception creation workflow
- Exception expiry enforcement
- Compensating control tracking
- Security Reviewer approval requirement
- Exception audit trail

**Acceptance Criteria**:
- All exceptions have expiry dates
- Compensating controls documented
- Security Reviewer must approve
- Exceptions linked to deployment intents
- ≥90% test coverage

### P5.6: Integration & Testing
**Duration**: 2 days
**Owner**: QA + Backend
**Deliverables**:
- End-to-end workflow tests
- Integration tests with deployment intents
- Risk score calibration tests
- Exception workflow validation
- ≥90% test coverage on integration

**Acceptance Criteria**:
- Full workflow tested (evidence → submission → approval → ring promotion)
- Risk scores align with documented rubrics
- Exception gates enforced properly
- All edge cases handled
- ≥90% coverage on entire module

---

## P5 Deliverables Checklist

### Code Deliverables

| Component | File | Status |
|-----------|------|--------|
| Evidence Pack Model | `apps/evidence_store/models.py` | To implement |
| Evidence Generation Service | `apps/evidence_store/services.py` | To implement |
| Risk Scoring Engine | `apps/policy_engine/risk_scorer.py` | To implement |
| CAB Approval Model | `apps/cab_workflow/models.py` | Extend |
| CAB Submission View | `apps/cab_workflow/views.py` | New |
| CAB Approval View | `apps/cab_workflow/views.py` | New |
| Exception Model | `apps/cab_workflow/models.py` | New |
| Exception Management View | `apps/cab_workflow/views.py` | New |
| URLs | `apps/cab_workflow/urls.py` | Update |
| Serializers | `apps/cab_workflow/serializers.py` | New |

### Test Deliverables

| Test Suite | File | Tests | Coverage |
|-----------|------|-------|----------|
| Evidence Package Tests | `apps/evidence_store/tests/test_evidence_generation.py` | 20+ | 90%+ |
| Risk Scoring Tests | `apps/policy_engine/tests/test_risk_scorer.py` | 25+ | 90%+ |
| CAB Workflow Tests | `apps/cab_workflow/tests/test_approval_workflow.py` | 30+ | 90%+ |
| Exception Tests | `apps/cab_workflow/tests/test_exception_management.py` | 15+ | 90%+ |
| Integration Tests | `apps/cab_workflow/tests/test_integration.py` | 20+ | 90%+ |

**Total**: 110+ new tests

### Documentation Deliverables

| Document | File | Content |
|----------|------|---------|
| Architecture | `docs/architecture/evidence-pack-schema.md` | Evidence structure, fields |
| Risk Model | `docs/architecture/risk-model.md` | Scoring formula, factors, rubrics |
| CAB Workflow | `docs/architecture/cab-workflow.md` | Submission, approval, gates |
| API Spec | `docs/api/cab-workflow-endpoints.md` | Endpoint specifications |
| Exception Mgmt | `docs/architecture/exception-management.md` | Exception lifecycle |
| Runbook | `docs/runbooks/cab-submission.md` | Manual CAB submission guide |

---

## P5 Implementation Architecture

### Evidence Pack Generation Flow

```
Deployment Intent Created
    ↓
[Trigger Evidence Collection]
    ├→ Collect artifact hashes (SHA-256)
    ├→ Retrieve test results (from P4)
    ├→ Get SBOM (from packaging)
    ├→ Get vulnerability scan results
    ├→ Get code signing certificate info
    └→ Retrieve deployment/rollback plans
    ↓
[Compute Risk Score]
    ├→ Evaluate all risk factors
    ├→ Apply weights
    ├→ Normalize to 0-100
    └→ Version the model used
    ↓
[Generate Evidence Package]
    └→ Create immutable record in event store
         with correlation_id linking to deployment_intent
    ↓
[Ready for CAB Submission]
```

### CAB Approval Workflow Flow

```
Evidence Package Ready
    ↓
[CAB Submission]
    ├→ Validate evidence completeness
    ├→ Check risk thresholds
    └→ Submit to approval queue
    ↓
[CAB Review]
    ├→ Risk score ≤ 50: Auto-approve, notify deployment team
    ├→ Risk score 50-75: Manual review required
    └→ Risk score > 75: Risk assessment + exception required
    ↓
[Approval Decision]
    ├→ Approved: Proceed to Ring 2+
    ├→ Rejected: Return to development
    ├→ Conditional: Apply conditions + compensating controls
    └→ Exception: Grant exception with expiry date
    ↓
[Unlock Ring Promotion]
    └→ Deployment intent can proceed to Ring 2+
```

### Risk Scoring Formula

```
RiskScore = clamp(0..100, Σ(weight_i * normalized_factor_i))

Where factors include:
- Test coverage: 90%+ = 0 pts, <90% = 20 pts (weight: 25%)
- Security issues: None = 0, Medium = 15, High = 30, Critical = 50 pts (weight: 25%)
- Manual testing: Yes = 0, No = 10 pts (weight: 15%)
- Rollback validation: Complete = 0, Partial = 10 pts (weight: 15%)
- Change scope: Small = 0, Medium = 10, Large = 20 pts (weight: 20%)

Example:
  Test coverage (95%) = 0 pts × 0.25 = 0
  Security (0 issues) = 0 pts × 0.25 = 0
  Manual testing (Yes) = 0 pts × 0.15 = 0
  Rollback (Complete) = 0 pts × 0.15 = 0
  Change scope (Small) = 0 pts × 0.20 = 0
  ─────────────────────────────────────
  Total Risk Score = 0 (Green)

  Test coverage (85%) = 20 pts × 0.25 = 5
  Security (1 High) = 15 pts × 0.25 = 3.75
  Manual testing (No) = 10 pts × 0.15 = 1.5
  Rollback (Partial) = 10 pts × 0.15 = 1.5
  Change scope (Large) = 20 pts × 0.20 = 4
  ─────────────────────────────────────
  Total Risk Score = 15.75 (Yellow - CAB review)
```

---

## P5 Dependencies & Blockers

### Must be complete before P5.1 starts:
- ✅ P4.4 state comparison logic (for reconciliation)
- ✅ Event store integration (for audit trail)
- ✅ Deployment intents model (for evidence linking)

### External dependencies:
- Packaging factory (for artifacts) — P8 implementation
- Vulnerability scanning (for scan results) — P4 output
- Test reports (for coverage) — P4.1 output

---

## P5 Quality Gates

### Code Quality
- ✅ All code must pass pre-commit hooks (type checking, linting, formatting)
- ✅ ≥90% test coverage on all new modules
- ✅ Zero hardcoded values in risk scoring
- ✅ All risk factors documented with rubrics
- ✅ All API endpoints have request/response validation

### Security
- ✅ CAB members must be authenticated (Entra ID)
- ✅ CAB approval decisions immutable (event store only)
- ✅ Exception creation requires Security Reviewer approval
- ✅ Audit trail includes actor and timestamp for all decisions
- ✅ Correlation IDs link all related events

### Compliance
- ✅ All risk scores computed deterministically
- ✅ Risk model versioned (v1.0)
- ✅ Evidence packs complete (no partial submissions)
- ✅ Approvals recorded with rationale
- ✅ Exceptions have expiry dates and compensating controls

### Documentation
- ✅ Risk model documented (formula, factors, rubrics, calibration)
- ✅ CAB workflow documented (submission, review, approval, gates)
- ✅ Exception management documented (creation, approval, expiry, enforcement)
- ✅ API endpoints documented (request/response, error codes, examples)
- ✅ Runbooks created (manual CAB submission, exception appeal)

---

## P5 Success Metrics

| Metric | Target | Acceptance |
|--------|--------|-----------|
| Test coverage | 90% | All new modules ≥90% |
| API endpoints | 8+ | Submit, approve, exception, list |
| Evidence fields | 10+ | All required by architecture |
| Risk factors | 5+ | Documented with rubrics |
| Integration tests | 20+ | End-to-end workflow covered |
| Documentation | 6+ | Architecture, API, runbooks |
| Compliance gate | 100% | Risk >50 requires CAB approval |
| Audit trail | 100% | All decisions logged with correlation IDs |

---

## P5 Schedule (2-Week Sprint)

**Week 1**:
- Day 1-2: Evidence pack schema + generation (P5.1)
- Day 3: Risk scoring engine (P5.2 start)
- Day 4-5: CAB submission workflow (P5.3)

**Week 2**:
- Day 1-2: CAB approval decision logic (P5.4)
- Day 3: Exception management (P5.5)
- Day 4-5: Integration, testing, documentation (P5.6)

**Deliverable date**: February 5, 2026

---

## Phase Gate Criteria

Phase P5 is complete when:

✅ Evidence pack generation fully implemented and tested
✅ Risk scoring engine complete with documented rubrics
✅ CAB submission workflow tested and integrated
✅ CAB approval decision logic enforced
✅ Exception management with expiry enforcement
✅ All 110+ tests passing with ≥90% coverage
✅ All documentation complete
✅ No production TODOs
✅ Master plan updated

Only after ALL criteria met can P6 begin.

---

## Handoff to P6

Once P5 is complete:
- Evidence packs are generated automatically
- CAB approvals control Ring 2+ promotion
- Exceptions are tracked and enforced
- All decisions immutable in event store

P6 (Connector Implementation) will implement the actual deployment execution to controlled sites using these governance decisions.

---

**Ready to start P5.1: Evidence Pack Generation Engine**
