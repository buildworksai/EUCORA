# EUCORA Quality Gates

**SPDX-License-Identifier: Apache-2.0**  
**Version**: 1.0.0  
**Last Updated**: January 8, 2026  
**Authority**: MANDATORY — No Exceptions

---

## Purpose

This document defines quality gates for all code, commits, builds, and deployments in EUCORA. Quality gates are **non-negotiable** checks that **block** commits, builds, or deployments if standards are not met.

**Related Documentation:**
- [Coding Standards](./coding-standards.md)
- [Testing Standards](../architecture/testing-standards.md)
- [AGENTS.md](../../AGENTS.md)
- [CLAUDE.md](../../CLAUDE.md)

---

## Quality Gate Configuration

**SECURITY WARNING**: Never hardcode credentials in rules files.

```yaml
quality_gates:
  code_coverage: 90            # EUCORA-01002
  duplicated_lines: 3
  maintainability_rating: A
  reliability_rating: A
  security_rating: A           # EUCORA-01003
  security_hotspots: 0
  vulnerabilities: 0           # EUCORA-01004
  code_smells: 0
  bugs: 0
  technical_debt: 5            # minutes per file (EUCORA-01005)
  cognitive_complexity: 15     # EUCORA-01006
  cyclomatic_complexity: 10
```

---

## Pre-Commit Quality Gates

**MANDATORY: All commits MUST pass pre-commit hooks before being pushed.**

### EUCORA-01002 Coverage ≥ 90%

New/changed code must maintain ≥ 90% coverage. CI blocks merges below threshold.

**Enforcement:**
- Pre-commit hook: Run tests with coverage check
- CI/CD: Block merge if coverage < 90%

### EUCORA-01003 Security Rating A

Zero tolerance for security degradations. Fix BLOCKER/CRITICAL before merge.

**Enforcement:**
- Pre-commit hook: Security scan (detect-secrets)
- CI/CD: Security audit (SAST, dependency scan)

### EUCORA-01004 Zero Vulnerabilities

Code + dependencies must report 0 vulnerabilities prior to merge/release.

**Enforcement:**
- Pre-commit hook: Dependency vulnerability scan
- CI/CD: Comprehensive security scan

### EUCORA-01005 Technical Debt ≤ 5 min/file

Maintainability guardrail for safety-critical software.

**Enforcement:**
- CI/CD: SonarQube analysis
- Block merge if technical debt exceeds threshold

### EUCORA-01006 Cognitive Complexity ≤ 15/function

Reduce human error in reviews and maintenance.

**Enforcement:**
- Pre-commit hook: Complexity analysis
- CI/CD: SonarQube complexity check

### EUCORA-01007 Domain Ownership & TypeScript Cleanliness (CRITICAL)

Every top-level frontend domain (e.g., `frontend/src/routes/deployments`, `frontend/src/routes/policy`) MUST have an explicit **CODEOWNER** responsible for:
- Keeping that domain at **zero TypeScript errors** and **zero ESLint errors**.
- Rejecting any PR that introduces new TS/ESLint errors in that domain.

**CI MUST**:
- Track TypeScript errors **per domain directory**.
- Fail a PR if `errors_after > errors_before` for any touched domain directory.
- New files MAY NOT be added to a domain that already has TypeScript errors unless the same PR also drives that domain's error count closer to zero.

### EUCORA-01008 Transitional Freeze for "Dirty" Frontend Domains

A frontend domain directory is considered **dirty** when any `tsc --noEmit` error originates from files under that directory.

**While a domain is dirty**:
- Only **refactor / remediation** work is allowed in that directory.
- **New features** targeting that domain are forbidden until `tsc --noEmit` reports **zero errors** for that directory.
- CI MUST enforce that net-new lines in dirty domains are exclusively associated with TS/ESLint fixes or test hardening.
- Once a domain reaches **zero TypeScript errors and zero ESLint errors**, normal feature work may resume, but EUCORA-04002 and EUCORA-04010 (global TypeScript/ESLint gates) keep it clean.

---

## Pre-Commit Hook Requirements

### Type Safety

| Check | Rule | Enforcement |
|-------|------|-------------|
| TypeScript | `tsc --noEmit` — ZERO errors | Block commit |
| MyPy | Must not exceed baseline | Block commit |

### Linting

| Check | Rule | Enforcement |
|-------|------|-------------|
| ESLint | `--max-warnings 0` — ZERO tolerance | Block commit |
| Flake8 | `--max-line-length=120` | Block commit |

### Formatting

| Check | Rule | Enforcement |
|-------|------|-------------|
| Black | Python formatting required | Block commit |
| Prettier | Frontend formatting required | Block commit |
| isort | Import sorting required | Block commit |

### File Quality

| Check | Rule | Enforcement |
|-------|------|-------------|
| YAML Validation | All YAML files must be valid | Block commit |
| JSON Validation | All JSON files must be valid | Block commit |
| Markdown Linting | Markdown files must be properly formatted | Block commit |
| Trailing Whitespace | Remove trailing whitespace | Block commit |
| Merge Conflicts | Detect merge conflict markers | Block commit |

### Security

| Check | Rule | Enforcement |
|-------|------|-------------|
| Secret Detection | No hardcoded secrets | Block commit |

**No exceptions. No bypasses. All checks must pass.**

---

## CI/CD Quality Gates

### Build Stage

1. **Code Quality Checks**
   - SPDX compliance
   - PowerShell linting (PSScriptAnalyzer)
   - File quality (trailing whitespace, large files)
   - Branding compliance

2. **Backend Tests**
   - pytest with ≥90% coverage
   - All tests must pass

3. **Frontend Tests**
   - Vitest with ≥90% coverage
   - All tests must pass

4. **Linting**
   - Backend: black, flake8, mypy
   - Frontend: ESLint, TypeScript

**Failure Action**: Block merge to main

### Deployment Quality Gates

#### Pre-Deployment Checks

1. **Evidence Pack Completeness**
   - All required fields present
   - SBOM generated
   - Vulnerability scan completed
   - Signatures verified

2. **Risk Assessment**
   - Risk score calculated
   - CAB approval (if required)

3. **Rollback Validation**
   - Rollback plan present
   - Rollback strategy validated

4. **Promotion Gates**
   - Success rate threshold met
   - Time-to-compliance threshold met
   - Zero incidents

**Failure Action**: Block deployment

---

## Quality Gate Bypass

### Zero Tolerance Policy

**NO BYPASSES ALLOWED** for:
- Test coverage < 90%
- Type errors
- Linting warnings
- Hardcoded secrets
- Missing evidence packs

### Exception Process

For **critical** issues requiring temporary bypass:
1. **CAB Approval**: Required for any bypass
2. **Justification**: Documented reason
3. **Compensating Controls**: Additional testing/review
4. **Expiry Date**: Bypass expires automatically
5. **Audit Trail**: Immutable record in event store

---

## Quality Metrics

### Code Quality Metrics

- **Test Coverage**: ≥90% (measured)
- **Type Safety**: 100% (zero errors)
- **Linting**: 100% (zero warnings)
- **Secrets**: 0 (zero hardcoded secrets)

### Deployment Quality Metrics

- **Evidence Pack Completeness**: 100%
- **Risk Assessment Coverage**: 100%
- **CAB Approval Rate**: 100% (for required deployments)
- **Promotion Gate Pass Rate**: Target ≥95%

---

## Quality Gate Monitoring

### Dashboards

- **Code Quality Dashboard**: Coverage trends, linting errors, type errors
- **Deployment Quality Dashboard**: Evidence completeness, risk scores, gate pass rates

### Alerts

- **Coverage Drop**: Alert if coverage drops below 90%
- **Quality Gate Failures**: Alert on any gate failure
- **Bypass Usage**: Alert on any quality gate bypass

---

## References

- [Coding Standards](./coding-standards.md)
- [Testing Standards](../architecture/testing-standards.md)
- [Pre-Commit Hooks](../../.pre-commit-config.yaml)
- [CAB Workflow](../architecture/cab-workflow.md)
- [Promotion Gates](../architecture/promotion-gates.md)

---

**Classification**: PROPRIETARY — MANDATORY  
**Enforcement**: ABSOLUTE — No exceptions permitted
