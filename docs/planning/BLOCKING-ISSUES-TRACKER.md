# EUCORA — Blocking Issues Tracker

**SPDX-License-Identifier: Apache-2.0**

**Version**: 1.0.0
**Status**: AUTHORITATIVE
**Created**: January 25, 2026
**Last Updated**: January 25, 2026
**Classification**: INTERNAL — Production Readiness

---

## Executive Summary

This document tracks **blocking issues** that prevent EUCORA from achieving production deployment per the signed Statement of Work. Issues are categorized by severity and mapped to SOW milestones.

**Critical Blockers**: 7
**High Priority Blockers**: 5
**Medium Priority Blockers**: 4
**Total Blocking Issues**: 16

---

## Severity Definitions

| Severity | Definition | SLA |
|----------|------------|-----|
| **CRITICAL** | Blocks SOW acceptance; contract risk | Must resolve before milestone |
| **HIGH** | Blocks deliverable completion | Must resolve within 5 days |
| **MEDIUM** | Degrades quality; workaround exists | Must resolve within 10 days |
| **LOW** | Minor issue; no immediate impact | Resolve before production |

---

## CRITICAL Blockers (7)

### BLOCK-001: Test Coverage Below SOW Requirement

**Status**: 🔴 OPEN
**SOW Deliverable**: All (D-01 through D-10)
**Milestone Impact**: All payments at risk
**Assigned**: TBD
**Due Date**: Week 4 (first milestone)

**Description**:
SOW requires ≥90% test coverage. Current coverage is **70.98%**.

**Evidence**:
```
Current: 70.98%
Required: 90.00%
Gap: 19.02 percentage points
```

**Impact**:
- SOW Section 4.2 requires "All tests ≥90% coverage"
- Pre-commit hook configured for 90% but being bypassed
- Customer can reject ALL deliverables on this basis alone

**Resolution Path**:
1. Run `pytest --cov=apps --cov-fail-under=70` to identify worst modules
2. Assign dedicated test writer (1 FTE for 12 weeks)
3. Weekly coverage targets: +2% per week minimum
4. Fix pre-commit enforcement immediately

**Acceptance Criteria**:
- [ ] Backend coverage ≥90%
- [ ] Pre-commit hook enforcing 90% threshold
- [ ] Coverage report in CI/CD artifacts

---

### BLOCK-002: License Management Module Does Not Exist

**Status**: 🔴 OPEN
**SOW Deliverable**: D-05 License Management
**Milestone Impact**: Week 7 payment ($X at risk)
**Assigned**: TBD
**Due Date**: Week 7

**Description**:
D-05 requires complete SAM-grade license management with:
- Vendor/SKU catalog
- Entitlement tracking
- Consumption discovery
- AI agents for reconciliation
- Sidebar showing "Consumed/Entitled/Remaining"

**Current State**: **0% implemented. No code exists.**

No `license_management` Django app. No models. No APIs. No frontend components.

**Impact**:
- This is the **differentiating feature** promised to customer
- 400+ engineering hours required
- Cannot be completed by Week 7 without immediate start

**Resolution Path**:
1. Day 1: `python manage.py startapp license_management`
2. Day 1-3: Data model (Vendor, SKU, Entitlement, Consumption)
3. Day 4-7: Core APIs
4. Week 2-3: AI agents and frontend
5. Week 4-5: Integration testing

**Acceptance Criteria**:
- [ ] Django app created and registered
- [ ] All models migrated
- [ ] API endpoints functional
- [ ] Frontend sidebar displaying real data
- [ ] AI agents operational with guardrails
- [ ] ≥90% test coverage

---

### BLOCK-003: Portfolio Management Module Does Not Exist

**Status**: 🔴 OPEN
**SOW Deliverable**: D-06 Application Portfolio
**Milestone Impact**: Week 7 payment
**Assigned**: TBD
**Due Date**: Week 7

**Description**:
D-06 requires:
- Application inventory with normalization
- Dependency mapping
- Portfolio risk scoring
- License-app association

**Current State**: **0% implemented. No code exists.**

**Impact**:
- 330+ engineering hours required
- Depends on D-05 (License Management) for full functionality
- Customer demo specifically highlighted this feature

**Resolution Path**:
1. Create `portfolio` Django app
2. Implement Application model with normalization
3. Build dependency mapping service
4. Integrate with License Management
5. Create dashboard components

**Acceptance Criteria**:
- [ ] Django app created
- [ ] Application catalog with deduplication
- [ ] Dependency mapping functional
- [ ] Integration with License Management
- [ ] ≥90% test coverage

---

### BLOCK-004: SCCM Connector is Vaporware

**Status**: 🔴 OPEN
**SOW Deliverable**: D-03 Connectors
**Milestone Impact**: Week 4 payment
**Assigned**: TBD
**Due Date**: Week 4

**Description**:
SCCM connector exists as a skeleton that references non-existent PowerShell scripts.

**Evidence**:
```python
# backend/apps/connectors/services.py
class SCCMConnectorService:
    def sync_inventory(self):
        # Calls: scripts/sccm/sync_inventory.ps1
        # File does not exist
```

**Current State**:
- Test connection: ❌ Stub only
- Sync inventory: ❌ References missing script
- Push intent: ❌ References missing script
- Compliance query: ❌ Not implemented
- Rollback: ❌ Not implemented

**Impact**:
- SOW explicitly lists SCCM as required connector
- Offline/constrained site deployments depend on SCCM
- 120+ engineering hours required

**Resolution Path**:
1. Create PowerShell scripts in `scripts/sccm/`
2. Implement WMI/REST provider integration
3. Add proper error handling and retry logic
4. Write integration tests against sandbox

**Acceptance Criteria**:
- [ ] All 5 connector operations functional
- [ ] Integration tests passing
- [ ] Idempotency verified
- [ ] Error classification implemented

---

### BLOCK-005: Landscape Connector is Vaporware

**Status**: 🔴 OPEN
**SOW Deliverable**: D-03 Connectors
**Milestone Impact**: Week 4 payment
**Assigned**: TBD
**Due Date**: Week 4

**Description**:
Landscape connector for Ubuntu/Linux management is a skeleton with no implementation.

**Current State**:
- Test connection: ❌ Returns mock True
- Sync inventory: ❌ Returns empty list
- Push intent: ❌ Logs and returns mock
- Compliance query: ❌ Not implemented
- Rollback: ❌ Not implemented

**Impact**:
- Linux device management non-functional
- SOW explicitly requires Linux support via Landscape or Ansible

**Resolution Path**:
1. Implement Landscape API client
2. Build repo sync functionality
3. Add package installation/removal
4. Write integration tests

**Acceptance Criteria**:
- [ ] All 5 connector operations functional
- [ ] Integration tests passing against Landscape sandbox

---

### BLOCK-006: Ansible Connector is Vaporware

**Status**: 🔴 OPEN
**SOW Deliverable**: D-03 Connectors
**Milestone Impact**: Week 4 payment
**Assigned**: TBD
**Due Date**: Week 4

**Description**:
Ansible/AWX connector exists as a skeleton with no real implementation.

**Current State**:
- Test connection: ❌ Returns mock True
- Sync inventory: ❌ Returns empty dict
- Push intent: ❌ Logs and returns mock
- Job templates: ❌ Not implemented
- Rollback: ❌ Not implemented

**Impact**:
- Alternative Linux management path non-functional
- Remediation playbook execution impossible

**Resolution Path**:
1. Implement AWX/Tower API client
2. Build job template management
3. Add inventory sync from AWX
4. Write integration tests

**Acceptance Criteria**:
- [ ] AWX API integration functional
- [ ] Job template CRUD operations
- [ ] Integration tests passing

---

### BLOCK-007: 92 Untracked Files in Git

**Status**: 🔴 OPEN
**SOW Deliverable**: All
**Milestone Impact**: All milestones
**Assigned**: TBD
**Due Date**: **IMMEDIATE** (Day 1)

**Description**:
92 files exist in the working directory but are not tracked in git. This includes:
- Complete implementations
- Migration files
- Test files
- Reports

**Evidence**:
```
?? backend/apps/agent_management/
?? backend/apps/ai_strategy/
?? backend/apps/evidence_store/models_p5_5.py
?? backend/apps/packaging_factory/
?? backend/coverage.json
... (87 more files)
```

**Impact**:
- **Governance violation**: Production code outside version control
- Cannot rollback if needed
- Cannot audit changes
- Team members cannot access code

**Resolution Path**:
1. Review each untracked file for secrets/credentials
2. Add appropriate entries to .gitignore for generated files
3. `git add` all legitimate source files
4. Create commit with descriptive message
5. Push to remote

**Acceptance Criteria**:
- [ ] All source files tracked in git
- [ ] Generated files in .gitignore
- [ ] No secrets committed
- [ ] Team can access all code

---

## HIGH Priority Blockers (5)

### BLOCK-008: User Management Incomplete

**Status**: 🟠 OPEN
**SOW Deliverable**: D-07 User & Admin Management
**Milestone Impact**: Week 10 payment
**Assigned**: TBD
**Due Date**: Week 10

**Description**:
D-07 requires admin user management. Current state:
- Basic authentication: ✅ Working
- User CRUD for admins: ❌ Not implemented
- Role management UI: ❌ Not implemented
- AD sync foundation: ❌ Not implemented

**Impact**:
- 220+ engineering hours required
- Customer explicitly requested AD integration path

**Acceptance Criteria**:
- [ ] Admin can create/edit/deactivate users
- [ ] Role management with permissions
- [ ] AD sync foundation testable
- [ ] ≥90% test coverage

---

### BLOCK-009: AI Agent Guardrails Incomplete

**Status**: 🟠 OPEN
**SOW Deliverable**: D-04 AI Framework
**Milestone Impact**: Week 7 payment
**Assigned**: TBD
**Due Date**: Week 7

**Description**:
AI agents exist but guardrail enforcement is incomplete:
- R1 actions (read-only): ✅ Working
- R2 actions (reversible): ⚠️ Partial
- R3 actions (irreversible): ❌ Not blocked without approval

**Impact**:
- SOW requires "Human-in-loop for R2/R3 actions"
- Risk of unauthorized automated changes

**Acceptance Criteria**:
- [ ] R2 actions require approval if Risk > 50
- [ ] R3 actions always require approval
- [ ] Audit trail for all agent actions
- [ ] Guardrail bypass impossible

---

### BLOCK-010: Pre-Commit Hook Not Enforcing Coverage

**Status**: 🟠 OPEN
**SOW Deliverable**: All
**Milestone Impact**: All milestones
**Assigned**: TBD
**Due Date**: **IMMEDIATE** (Day 1)

**Description**:
Pre-commit is configured to enforce 90% coverage but commits are going through at 70.98%.

**Evidence**:
```yaml
# .pre-commit-config.yaml claims 90%
# Actual coverage: 70.98%
# Commits still succeeding
```

**Possible Causes**:
1. Pre-commit not installed on developer machines
2. Commits bypassing with `--no-verify`
3. Coverage check not running in hook
4. Different source paths in hook vs actual

**Resolution Path**:
1. Audit pre-commit configuration
2. Verify hook is installed and running
3. Test coverage enforcement locally
4. Document installation requirements

**Acceptance Criteria**:
- [ ] Pre-commit blocks commits below 90%
- [ ] Cannot bypass without explicit override
- [ ] CI also enforces coverage

---

### BLOCK-011: Mobile Connectors Not Implemented

**Status**: 🟠 OPEN
**SOW Deliverable**: D-03 Connectors
**Milestone Impact**: Week 4 payment
**Assigned**: TBD
**Due Date**: Week 4

**Description**:
iOS ABM and Android Enterprise connectors are not implemented.

**Current State**:
- iOS ABM: ❌ No implementation
- Android Enterprise: ❌ No implementation
- VPP/licensing: ❌ No implementation

**Impact**:
- Mobile device management non-functional
- SOW requires iOS and Android support

**Acceptance Criteria**:
- [ ] iOS ABM connector functional
- [ ] Android Enterprise connector functional
- [ ] VPP licensing integration
- [ ] Integration tests passing

---

### BLOCK-012: ServiceNow Connector Incomplete

**Status**: 🟠 OPEN
**SOW Deliverable**: D-03 Connectors
**Milestone Impact**: Week 4 payment
**Assigned**: TBD
**Due Date**: Week 4

**Description**:
ServiceNow ITSM connector has basic structure but missing key operations.

**Current State**:
- Create incident: ⚠️ Basic implementation
- Update incident: ⚠️ Basic implementation
- Query CMDB: ❌ Not implemented
- Change request sync: ❌ Not implemented

**Impact**:
- ITSM integration incomplete
- CAB workflow cannot sync with ServiceNow

**Acceptance Criteria**:
- [ ] All ITSM operations functional
- [ ] CMDB query working
- [ ] Change request bidirectional sync
- [ ] Integration tests passing

---

## MEDIUM Priority Blockers (4)

### BLOCK-013: E2E Test Suite Incomplete

**Status**: 🟡 OPEN
**SOW Deliverable**: D-08 Enterprise Hardening
**Milestone Impact**: Week 12 payment
**Assigned**: TBD
**Due Date**: Week 10

**Description**:
End-to-end test suite exists but covers limited scenarios.

**Current State**:
- Deployment flow E2E: ⚠️ Partial
- CAB approval E2E: ✅ Working
- License management E2E: ❌ Blocked by BLOCK-002
- Portfolio E2E: ❌ Blocked by BLOCK-003

**Acceptance Criteria**:
- [ ] All critical paths covered
- [ ] E2E tests pass in staging
- [ ] No flaky tests

---

### BLOCK-014: Load Testing Not Validated for 100k Devices

**Status**: 🟡 OPEN
**SOW Deliverable**: D-08 Enterprise Hardening
**Milestone Impact**: Week 10 payment
**Assigned**: TBD
**Due Date**: Week 10

**Description**:
SOW requires validation for 100,000 device scale. Load tests exist but haven't been validated at scale.

**Current State**:
- Locust tests exist
- Previous tests ran at smaller scale
- 100k device simulation not completed

**Acceptance Criteria**:
- [ ] Load test passes with 100k simulated devices
- [ ] Response times within SLA
- [ ] No memory leaks under load
- [ ] Results documented

---

### BLOCK-015: Break-Glass Procedures Not Tested

**Status**: 🟡 OPEN
**SOW Deliverable**: D-08 Enterprise Hardening
**Milestone Impact**: Week 10 payment
**Assigned**: TBD
**Due Date**: Week 10

**Description**:
Break-glass procedures documented but not tested.

**Current State**:
- Documentation exists in `docs/runbooks/`
- Procedures not validated in staging
- Recovery time not measured

**Acceptance Criteria**:
- [ ] Break-glass tested in staging
- [ ] Recovery time measured and documented
- [ ] Audit trail verified during break-glass

---

### BLOCK-016: Security Audit Not Scheduled

**Status**: 🟡 OPEN
**SOW Deliverable**: D-09 Production Deployment
**Milestone Impact**: Week 12 payment
**Assigned**: TBD
**Due Date**: Week 11

**Description**:
SOW requires security audit before production deployment. Audit not scheduled.

**Current State**:
- Internal scans running (0 critical CVEs)
- External audit not scheduled
- Penetration testing not scheduled

**Acceptance Criteria**:
- [ ] Security audit scheduled
- [ ] Penetration test scheduled
- [ ] Remediation time budgeted

---

## Blocked-By Dependencies

```
BLOCK-002 (License Management)
    └── BLOCK-003 (Portfolio - depends on License)
    └── BLOCK-013 (E2E Tests - can't test what doesn't exist)

BLOCK-004/005/006 (SCCM/Landscape/Ansible)
    └── BLOCK-011 (Mobile may share patterns)

BLOCK-001 (Test Coverage)
    └── ALL OTHER BLOCKS (coverage required for every deliverable)

BLOCK-007 (Untracked Files)
    └── ALL OTHER BLOCKS (must commit code before working on it)
```

---

## Resolution Priority Order

**Week 1 Priorities** (Must complete to unblock everything):

| Priority | Blocker | Action |
|----------|---------|--------|
| 1 | BLOCK-007 | Commit all untracked files |
| 2 | BLOCK-010 | Fix pre-commit enforcement |
| 3 | BLOCK-002 | Start License Management app |
| 4 | BLOCK-004 | Complete SCCM connector |
| 5 | BLOCK-001 | Begin test coverage campaign |

**Week 2-4 Priorities**:

| Priority | Blocker | Action |
|----------|---------|--------|
| 6 | BLOCK-005 | Complete Landscape connector |
| 7 | BLOCK-006 | Complete Ansible connector |
| 8 | BLOCK-011 | Complete Mobile connectors |
| 9 | BLOCK-003 | Start Portfolio app |
| 10 | BLOCK-009 | Complete AI guardrails |

**Week 5+ Priorities**:

| Priority | Blocker | Action |
|----------|---------|--------|
| 11 | BLOCK-008 | Complete User Management |
| 12 | BLOCK-012 | Complete ServiceNow |
| 13 | BLOCK-013 | Complete E2E tests |
| 14 | BLOCK-014 | Run 100k load test |
| 15 | BLOCK-015 | Test break-glass |
| 16 | BLOCK-016 | Schedule security audit |

---

## Daily Standup Questions

For each blocker, track:
1. What was done yesterday?
2. What will be done today?
3. What is blocking progress?
4. Is the due date at risk?

---

## Escalation Matrix

| Situation | Escalate To | Timeline |
|-----------|-------------|----------|
| CRITICAL blocker behind >2 days | Project Lead | Immediately |
| HIGH blocker behind >3 days | Project Lead | Within 24h |
| Multiple blockers competing for same resource | Project Lead | Within 24h |
| External dependency delay (audit, sandbox access) | Customer | Within 48h |
| SOW milestone at risk | Executive Sponsor | Immediately |

---

## Tracking Updates

| Date | Blocker | Update | Updated By |
|------|---------|--------|------------|
| 2026-01-25 | All | Initial tracker created | Platform Agent |

---

*This tracker must be updated daily. Any blocker that goes stale for >3 days without update is automatically escalated.*
