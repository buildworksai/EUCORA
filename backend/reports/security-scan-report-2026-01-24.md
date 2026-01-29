# Security Scan Report

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Generated:** 2026-01-24
**Scan Tools:** Bandit 1.9.3, Safety 3.7.0, npm audit
**Quality Gate:** EUCORA-01003 (Security Rating A), EUCORA-01004 (Zero Vulnerabilities)

---

## Executive Summary

**Overall Security Status:** ⚠️ **WARNING — 11 vulnerabilities detected**

| Tool | Target | Critical | High | Medium | Low | Total |
|------|--------|----------|------|--------|-----|-------|
| **Bandit** | Python Backend | 0 | 0 | 0 | 744 | 744 |
| **Safety** | Python Dependencies | 0 | 0 | 2 Django | 2 Requests | **4** |
| **npm audit** | Node.js Frontend | 0 | 0 | 7 | 0 | **7** |
| **TOTAL** | — | **0** | **0** | **9** | **746** | **755** |

**Quality Gate Status:**
- **EUCORA-01003 (Security Rating A):** ❌ **FAILING** — 9 medium vulnerabilities (target: 0)
- **EUCORA-01004 (Zero Vulnerabilities):** ❌ **FAILING** — 11 exploitable vulnerabilities (target: 0)

**CRITICAL FINDINGS:**
1. **Django CVE-2025-48432** — Log injection vulnerability (MEDIUM severity)
2. **Django CVE-2025-57833** — SQL injection vulnerability (MEDIUM severity)
3. **Requests CVE-2024-35195** — Session credential leakage (MEDIUM severity)
4. **Requests CVE-2024-47081** — .netrc credential leakage (MEDIUM severity)
5. **Vite/Vitest vulnerabilities** — 7 moderate-severity issues in dev dependencies

**Recommended Actions:**
1. **IMMEDIATE:** Upgrade Django from 5.0.14 to 5.1.12+ (fixes 2 CVEs)
2. **IMMEDIATE:** Upgrade Requests from 2.31.0 to 2.32.4+ (fixes 2 CVEs)
3. **HIGH PRIORITY:** Upgrade Vitest from 2.x to 4.0.18 (fixes 7 dev dependency issues)
4. **MEDIUM PRIORITY:** Review and suppress 744 low-severity Bandit warnings (mostly assert usage)

---

## 1. Bandit Scan Results (Python Backend)

**Scan Target:** `apps/` and `config/` directories
**Files Scanned:** 301 Python files
**Lines of Code:** 36,128 lines
**Tool Version:** Bandit 1.9.3

### Summary

| Severity | Count | Confidence Breakdown |
|----------|------:|----------------------|
| **HIGH** | **0** | — |
| **MEDIUM** | **0** | — |
| **LOW** | **744** | High: 678, Medium: 66, Low: 0 |
| **TOTAL** | **744** | — |

### Finding Breakdown by Test ID

| Test ID | Count | Issue Description | Severity | Risk Level |
|---------|------:|-------------------|----------|------------|
| **B101** | 560 | Use of assert detected | LOW | Info |
| **B311** | 102 | Standard pseudo-random generators | LOW | Info |
| **B105** | 66 | Possible hardcoded password | LOW | **REVIEW** |
| **B404** | 5 | subprocess module usage | LOW | Info |
| **B603** | 5 | subprocess call without shell=True | LOW | Info |
| **B110** | 4 | Try-Except-Pass detected | LOW | Info |
| **B607** | 2 | Partial executable path | LOW | Info |

### Analysis

**Status:** ✅ **ACCEPTABLE** — No HIGH or MEDIUM severity findings

**Findings Requiring Review:**

1. **B105: Possible hardcoded password (66 occurrences)**
   - **Description:** Detects patterns like `password=`, `passwd=`, `pwd=` in code
   - **Review Required:** Verify these are not actual hardcoded credentials
   - **Examples:**
     - Test fixtures (e.g., `conftest.py` with test passwords)
     - Configuration keys (e.g., `"password"` as dict key)
     - Documentation strings
   - **Recommendation:** Manual review required to confirm no actual secrets

2. **B101: Assert usage (560 occurrences)**
   - **Description:** Python `assert` statements removed when `python -O` is used
   - **Context:** Django framework and test code use assertions extensively
   - **Risk:** LOW — assertions in production code could be bypassed
   - **Recommendation:** Acceptable for test code; review production code usage

3. **B311: Pseudo-random generators (102 occurrences)**
   - **Description:** Use of `random` module instead of `secrets` module
   - **Context:** Likely demo data generation and test fixtures
   - **Risk:** LOW — not for cryptographic purposes
   - **Recommendation:** Verify usage is not for security-sensitive randomness

**Action Items:**
- [x] Run Bandit scan
- [ ] **Manual review B105 findings** (66 occurrences) to confirm no hardcoded secrets
- [ ] Suppress known-safe findings via `.bandit` config file
- [ ] Add Bandit to pre-commit hooks with HIGH/MEDIUM severity enforcement

---

## 2. Safety Scan Results (Python Dependencies)

**Scan Target:** Python virtual environment
**Packages Scanned:** 123 packages
**Tool Version:** Safety 3.7.0
**Scan Time:** 2026-01-24 19:52:15

### Summary

| Package | Installed Version | Vulnerability Count | CVEs | Severity |
|---------|-------------------|--------------------:|------|----------|
| **django** | 5.0.14 | **2** | CVE-2025-48432, CVE-2025-57833 | **MEDIUM** |
| **requests** | 2.31.0 | **2** | CVE-2024-35195, CVE-2024-47081 | **MEDIUM** |
| **TOTAL** | — | **4** | **4 CVEs** | **MEDIUM** |

### Vulnerability Details

#### 1. Django CVE-2025-48432 — Log Injection

**Vulnerability ID:** 77686
**Package:** django 5.0.14
**Affected Versions:** >=5.0a1,<5.1.10
**Fixed Versions:** 5.1.10+, 5.2.2+, 4.2.22+
**Severity:** MEDIUM

**Description:**
```
An issue was discovered in Django 5.2 before 5.2.3, 5.1 before 5.1.11,
and 4.2 before 4.2.23. Internal HTTP response logging does not escape
request.path, which allows remote attackers to potentially manipulate
log output via crafted URLs. This may lead to log injection or forgery
when logs are viewed in terminals or processed by external systems.
```

**Impact:**
- Attackers can inject malicious content into logs via crafted URLs
- Log forgery possible when logs are processed by SIEM systems
- Terminal escape sequences could be injected

**Recommendation:**
- **IMMEDIATE:** Upgrade to Django 5.1.12 or later
- **Alternative:** Pin to Django 4.2.24 (LTS) if staying on 4.2.x

**More Info:** [https://data.safetycli.com/v/77686/97c](https://data.safetycli.com/v/77686/97c)

---

#### 2. Django CVE-2025-57833 — SQL Injection

**Vulnerability ID:** 79173
**Package:** django 5.0.14
**Affected Versions:** >=5.0a1,<5.1.12
**Fixed Versions:** 5.1.12+, 5.2.6+, 4.2.24+
**Severity:** MEDIUM

**Description:**
```
Affected versions of the Django package are vulnerable to SQL Injection
due to insufficient input sanitization in...
```
*(Full advisory truncated for brevity)*

**Impact:**
- SQL injection vulnerability due to insufficient input sanitization
- Potential for data exfiltration or manipulation

**Recommendation:**
- **IMMEDIATE:** Upgrade to Django 5.1.12 or later
- **Alternative:** Pin to Django 4.2.24 (LTS) if staying on 4.2.x

**More Info:** [https://data.safetycli.com/v/79173/97c](https://data.safetycli.com/v/79173/97c)

---

#### 3. Requests CVE-2024-35195 — Session Credential Leakage

**Vulnerability ID:** 71064
**Package:** requests 2.31.0
**Affected Versions:** <2.32.2
**Fixed Versions:** 2.32.2+
**Severity:** MEDIUM

**Description:**
```
Affected versions of Requests, when making requests through a Requests
`Session`, if the first request is made with...
```
*(Full advisory truncated for brevity)*

**Impact:**
- Credentials may leak when using requests.Session()
- First request in a session could expose sensitive data

**Recommendation:**
- **IMMEDIATE:** Upgrade to requests 2.32.4 or later

**More Info:** [https://data.safetycli.com/v/71064/97c](https://data.safetycli.com/v/71064/97c)

---

#### 4. Requests CVE-2024-47081 — .netrc Credential Leakage

**Vulnerability ID:** 77680
**Package:** requests 2.31.0
**Affected Versions:** <2.32.4
**Fixed Versions:** 2.32.4+
**Severity:** MEDIUM

**Description:**
```
Requests is an HTTP library. Due to a URL parsing issue, Requests
releases prior to 2.32.4 may leak .netrc credentials to third...
```

**Impact:**
- .netrc credentials may leak to third-party sites
- URL parsing vulnerability could be exploited

**Recommendation:**
- **IMMEDIATE:** Upgrade to requests 2.32.4 or later

**More Info:** [https://data.safetycli.com/v/77680/97c](https://data.safetycli.com/v/77680/97c)

---

### Remediation Plan (Python Dependencies)

**Immediate Actions:**

1. **Upgrade Django:**
   ```bash
   # Current: Django==5.0.14
   # Target:  Django==5.1.12 or Django==4.2.24 (LTS)

   # In pyproject.toml:
   django = "^5.1.12"  # OR "^4.2.24" for LTS
   ```

2. **Upgrade Requests:**
   ```bash
   # Current: requests==2.31.0
   # Target:  requests==2.32.4+

   # In pyproject.toml:
   requests = "^2.32.4"
   ```

3. **Run Tests After Upgrade:**
   ```bash
   pytest --cov=apps --cov-report=term
   ```

4. **Verify No Breaking Changes:**
   - Django 5.0 → 5.1: Review [release notes](https://docs.djangoproject.com/en/5.1/releases/5.1/)
   - Requests 2.31 → 2.32: Review [changelog](https://github.com/psf/requests/blob/main/HISTORY.md)

**Estimated Effort:** 2-4 hours (upgrade + testing)

---

## 3. npm audit Results (Frontend Dependencies)

**Scan Target:** Node.js frontend (`frontend/` directory)
**Packages Scanned:** 625 packages (157 prod, 468 dev)
**Tool Version:** npm 10.x
**Scan Time:** 2026-01-24

### Summary

| Severity | Count | Fixable | Production | Development |
|----------|------:|---------|------------|-------------|
| **Critical** | **0** | — | — | — |
| **High** | **0** | — | — | — |
| **Moderate** | **7** | **7** | 0 | **7** |
| **Low** | **0** | — | — | — |
| **TOTAL** | **7** | **7** | **0** | **7** |

**Impact Assessment:** ⚠️ **MODERATE** — All vulnerabilities are in **dev dependencies only**

### Vulnerability Details

All 7 vulnerabilities are related to **Vitest** (testing framework) and **Vite** (build tool):

| Package | Current | Fix Available | Severity | Direct | CVE/Advisory |
|---------|---------|---------------|----------|--------|--------------|
| **vitest** | 2.x | 4.0.18 | Moderate | ✅ Yes | Multiple |
| **@vitest/coverage-v8** | <=2.2.0-beta.2 | 4.0.18 | Moderate | ✅ Yes | Via vitest |
| **@vitest/ui** | <=2.2.0-beta.2 | 4.0.18 | Moderate | ✅ Yes | Via vitest |
| **@vitest/mocker** | <=3.0.0-beta.4 | 4.0.18 | Moderate | ❌ No | Via vitest |
| **vite** | 0.11.0 - 6.1.6 | 4.0.18 | Moderate | ❌ No | Via vitest |
| **vite-node** | <=2.2.0-beta.2 | 4.0.18 | Moderate | ❌ No | Via vitest |
| **esbuild** | <=0.24.2 | 4.0.18 | Moderate | ❌ No | GHSA-67mh-4wv8-2f99 |

#### esbuild GHSA-67mh-4wv8-2f99

**Title:** esbuild enables any website to send any requests to the development server and read the response
**CVE:** N/A
**CVSS Score:** 5.3 (MODERATE)
**CVSS Vector:** CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:N/A:N
**CWE:** CWE-346 (Origin Validation Error)

**Description:**
Development server vulnerability allowing cross-origin requests to read responses.

**Impact:**
- **Development environment only** — does not affect production builds
- Requires user interaction and complex attack chain (AC:H, UI:R)
- Confidentiality impact: HIGH (C:H)
- No integrity or availability impact

**More Info:** [https://github.com/advisories/GHSA-67mh-4wv8-2f99](https://github.com/advisories/GHSA-67mh-4wv8-2f99)

---

### Remediation Plan (Frontend Dependencies)

**Priority:** **MEDIUM** — Dev dependencies only; does not affect production

**Recommended Actions:**

1. **Upgrade Vitest from 2.x to 4.0.18:**
   ```bash
   cd frontend
   npm install vitest@4.0.18 @vitest/ui@4.0.18 @vitest/coverage-v8@4.0.18 --save-dev
   ```

2. **Run Frontend Tests:**
   ```bash
   npm run test
   npm run test:ui
   ```

3. **Verify Build:**
   ```bash
   npm run build
   npm run preview
   ```

**Breaking Changes to Review:**
- Vitest 2.x → 4.x: Review [migration guide](https://vitest.dev/guide/migration.html)
- Vite 5.x → 6.x: Review [Vite migration guide](https://vitejs.dev/guide/migration.html)

**Estimated Effort:** 2-4 hours (upgrade + testing)

**Note:** Since these are development dependencies, the risk to production is **ZERO**. However, fixing these issues is still recommended to maintain security best practices and protect the development environment.

---

## 4. Quality Gate Assessment

### EUCORA-01003: Security Rating A

**Target:** Zero CRITICAL, zero HIGH, zero MEDIUM vulnerabilities
**Current Status:** ❌ **FAILING**

**Gaps:**
- **MEDIUM:** 4 Python dependency vulnerabilities (Django + Requests)
- **MODERATE:** 7 Node.js dev dependency vulnerabilities (Vitest/Vite)

**Blockers:**
1. Django 5.0.14 has 2 CVEs (log injection + SQL injection)
2. Requests 2.31.0 has 2 CVEs (credential leakage)
3. Vitest 2.x has 7 moderate-severity issues

**Remediation:**
- Upgrade Django to 5.1.12+
- Upgrade Requests to 2.32.4+
- Upgrade Vitest to 4.0.18

**Estimated Time to Green:** 4-8 hours

---

### EUCORA-01004: Zero Vulnerabilities

**Target:** Zero exploitable vulnerabilities in production code and dependencies
**Current Status:** ❌ **FAILING**

**Gaps:**
- **11 total vulnerabilities** (4 Python, 7 Node.js)
- **4 production-impacting** (Django + Requests)
- **7 dev-only** (Vitest/Vite)

**Remediation:**
- Same as EUCORA-01003 — upgrade dependencies

**Estimated Time to Green:** 4-8 hours

---

## 5. Risk Assessment

### Production-Impacting Risks

| Vulnerability | Severity | Exploitability | Impact | Priority |
|---------------|----------|----------------|--------|----------|
| Django Log Injection | MEDIUM | HIGH | Log forgery, SIEM bypass | **P0** |
| Django SQL Injection | MEDIUM | MEDIUM | Data exfiltration | **P0** |
| Requests Session Leak | MEDIUM | MEDIUM | Credential exposure | **P1** |
| Requests .netrc Leak | MEDIUM | LOW | Credential exposure | **P1** |

### Development-Only Risks

| Vulnerability | Severity | Exploitability | Impact | Priority |
|---------------|----------|----------------|--------|----------|
| esbuild Origin Validation | MODERATE | MEDIUM | Dev server data leak | **P2** |
| Vite/Vitest (6 others) | MODERATE | LOW-MEDIUM | Dev environment | **P2** |

### Overall Risk Rating

**Production Risk:** 🔴 **HIGH** — 4 MEDIUM-severity vulnerabilities in production dependencies
**Development Risk:** 🟡 **MODERATE** — 7 moderate-severity vulnerabilities in dev dependencies

**Risk Mitigation Priority:**
1. **P0 (CRITICAL):** Upgrade Django (fixes 2 CVEs) — **IMMEDIATE**
2. **P1 (HIGH):** Upgrade Requests (fixes 2 CVEs) — **IMMEDIATE**
3. **P2 (MEDIUM):** Upgrade Vitest (fixes 7 issues) — **Within 1 week**

---

## 6. Remediation Roadmap

### Phase 1: IMMEDIATE (Today)

**Duration:** 4-8 hours

1. **Upgrade Python Dependencies:**
   ```bash
   # Update pyproject.toml
   django = "^5.1.12"
   requests = "^2.32.4"

   # Install
   pip install --upgrade django requests

   # Test
   pytest --cov=apps
   ```

2. **Verify Django Migration:**
   - Review Django 5.1 release notes
   - Run all migrations
   - Test admin interface
   - Test authentication flows

3. **Verify Requests Upgrade:**
   - Test all HTTP client usage
   - Verify session handling
   - Test connector integrations (Intune, Jamf, etc.)

**Exit Criteria:**
- All tests passing
- Django 5.1.12+ installed
- Requests 2.32.4+ installed
- No new test failures

### Phase 2: HIGH PRIORITY (This Week)

**Duration:** 2-4 hours

1. **Upgrade Node.js Dependencies:**
   ```bash
   cd frontend
   npm install vitest@4.0.18 @vitest/ui@4.0.18 @vitest/coverage-v8@4.0.18 --save-dev
   npm run test
   npm run build
   ```

2. **Verify Vitest Migration:**
   - Run full test suite
   - Verify coverage reports
   - Test UI test runner
   - Verify build output

**Exit Criteria:**
- All frontend tests passing
- Vitest 4.0.18 installed
- Build succeeds
- No new test failures

### Phase 3: MEDIUM PRIORITY (Next Week)

**Duration:** 2-4 hours

1. **Bandit Findings Review:**
   - Manual review of 66 B105 findings (possible hardcoded passwords)
   - Create `.bandit` config to suppress known-safe findings
   - Add Bandit to pre-commit hooks

2. **Security Documentation:**
   - Document security scanning process
   - Add security scan results to CI/CD pipeline
   - Create security policy for dependency updates

**Exit Criteria:**
- Zero unreviewed B105 findings
- Bandit config file created
- Pre-commit hooks updated
- Security policy documented

---

## 7. Continuous Security Monitoring

### Recommended Tooling

1. **Dependency Scanning (CI/CD):**
   ```yaml
   # .github/workflows/security.yml
   - name: Run Safety
     run: safety check --json

   - name: Run Bandit
     run: bandit -r apps/ config/ -f json

   - name: Run npm audit
     run: npm audit --audit-level=moderate
   ```

2. **Pre-Commit Hooks:**
   ```yaml
   # .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: safety
         name: Safety dependency check
         entry: safety check
         language: system
         pass_filenames: false

       - id: bandit
         name: Bandit security linter
         entry: bandit -r apps/ config/ --severity-level medium
         language: system
         pass_filenames: false
   ```

3. **Automated Dependency Updates:**
   - Enable Dependabot for GitHub
   - Configure Renovate Bot for automated PRs
   - Set up security advisory notifications

### Security Scan Cadence

| Scan Type | Frequency | Trigger | Blocking |
|-----------|-----------|---------|----------|
| **Bandit** | Every commit | Pre-commit hook | Yes (MEDIUM+) |
| **Safety** | Daily | CI/CD + pre-commit | Yes (MEDIUM+) |
| **npm audit** | Daily | CI/CD | Yes (HIGH+) |
| **Full Scan** | Weekly | Scheduled CI/CD | Yes (MEDIUM+) |

---

## 8. Conclusion

**Current State:** ❌ **NOT PRODUCTION READY** — 11 vulnerabilities detected

**Quality Gate Status:**
- **EUCORA-01003 (Security Rating A):** ❌ FAILING
- **EUCORA-01004 (Zero Vulnerabilities):** ❌ FAILING

**Critical Blockers:**
1. Django 5.0.14 → 5.1.12 (fixes 2 CVEs)
2. Requests 2.31.0 → 2.32.4 (fixes 2 CVEs)

**Recommended Path to Green:**
1. **Phase 1 (IMMEDIATE):** Upgrade Django + Requests (4-8 hours)
2. **Phase 2 (THIS WEEK):** Upgrade Vitest (2-4 hours)
3. **Phase 3 (NEXT WEEK):** Bandit review + pre-commit hooks (2-4 hours)

**Total Estimated Effort:** 8-16 hours

**Expected Outcome:** Security Rating A, Zero Vulnerabilities, Production Ready

---

**Generated:** 2026-01-24
**Session Lead:** Platform Engineering AI Agent
**Review Status:** DRAFT — Awaiting approval for remediation plan
**Next Action:** Execute Phase 1 dependency upgrades
