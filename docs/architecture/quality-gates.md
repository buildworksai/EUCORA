# Quality Gates

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Quality gates are **non-negotiable** checks that **block** commits, builds, or deployments if standards are not met. **Zero tolerance** for quality gate failures.

**Design Principle**: Quality Gates — no compromises on pre-commit hooks, test coverage, type safety, or CAB evidence standards.

---

## Pre-Commit Quality Gates

### 1. Type Safety

**Backend**: mypy with django-stubs  
**Frontend**: TypeScript compilation  
**Enforcement**: Block commit if type errors  
**Tolerance**: Zero new errors beyond baseline

### 2. Linting

**Backend**: flake8 with `--max-warnings 0`  
**Frontend**: ESLint with `--max-warnings 0`  
**Enforcement**: Block commit if warnings  
**Tolerance**: Zero warnings

### 3. Code Formatting

**Backend**: black (auto-format)  
**Frontend**: Prettier (auto-format)  
**Enforcement**: Auto-format on commit  
**Tolerance**: All code must be formatted

### 4. Secrets Detection

**Tool**: detect-secrets  
**Enforcement**: Block commit if secrets detected  
**Tolerance**: Zero hardcoded secrets

### 5. Test Coverage

**Backend**: pytest with `--cov-fail-under=90`  
**Frontend**: Vitest with ≥90% thresholds  
**Enforcement**: Block commit if coverage < 90%  
**Tolerance**: ≥90% coverage required

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

---

## Deployment Quality Gates

### Pre-Deployment Checks

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

- [Testing Standards](./testing-standards.md)
- [Pre-Commit Hooks](../infrastructure/ci-cd-pipelines.md)
- [CAB Workflow](./cab-workflow.md)
- [Promotion Gates](./promotion-gates.md)

