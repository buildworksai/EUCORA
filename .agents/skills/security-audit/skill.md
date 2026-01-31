---
name: security-audit
description: EUCORA security review checklist for CAB-compliant applications. Use when auditing code for vulnerabilities, reviewing access controls, or validating supply chain security. Covers session-based auth, SBOM/vuln scanning, correlation IDs, and SoD enforcement.
status: ✅ Working
last-validated: 2026-01-30
---

# Security Audit for EUCORA

Security review checklist aligned with EUCORA's CAB governance and enterprise security requirements.

---

## Quick Reference

| Security Domain | EUCORA Requirement |
|-----------------|-------------------|
| Authentication | Session-based (Django sessions) with Entra ID OAuth2 |
| Authorization | ABAC Policy Engine + Django permissions |
| Audit Trail | Correlation IDs on ALL deployment events |
| Supply Chain | SBOM + vulnerability scanning mandatory |
| Secrets | Azure Key Vault (production) / Vault (dev) |
| Access Reviews | Quarterly for Publisher/Platform Admin roles |

---

## FORBIDDEN Security Patterns

❌ **STRICTLY FORBIDDEN** — Violates EUCORA security requirements:

- **JWT tokens for web sessions** — Use session-based auth only
- **Shared service principals** — Separate credentials per role (SoD)
- **Hardcoded secrets or credentials** — Use vault with rotation
- **Missing correlation IDs** — All audit events require correlation_id
- **Unsigned packages** — Windows/macOS/Linux packages must be signed
- **Skipping SBOM/vulnerability scans** — All artifacts scanned before publish
- **Publishing without CAB approval** when Risk > 50

---

## Authentication & Authorization

### Session-Based Authentication (MANDATORY)

```python
# ✅ CORRECT - Django session authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'apps.core.backends.EntraIdBackend',  # Entra ID OAuth2
]

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'  # Redis

# ❌ FORBIDDEN - JWT tokens for web sessions
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # NEVER!
    ],
}
```

### Multi-Factor Authentication

- TOTP only (RFC 6238) via django-otp
- Required for Platform Admin, Publisher, CAB Approver roles
- MFA tokens NEVER stored in localStorage

### Authorization Checklist

- [ ] Every endpoint has explicit permission class
- [ ] Policy Engine evaluates ABAC rules before access
- [ ] Role-based scopes enforced (Packaging ≠ Publishing ≠ Approval)
- [ ] Cross-boundary access requires CAB approval
- [ ] Scope validation: `target_scope ⊆ publisher_scope`

---

## Separation of Duties (SoD)

### Role Boundaries (NON-NEGOTIABLE)

| Role | Can DO | CANNOT DO |
|------|--------|-----------|
| Packaging Engineer | Build, test, sign artifacts | Publish to production, approve CAB |
| Publisher | Publish approved artifacts (scoped) | Package, approve CAB |
| CAB Approver | Approve/deny, review evidence | Publish, modify artifacts |
| Platform Admin | Configure platform, integrations | Direct Intune production writes |

### SoD Enforcement Checklist

- [ ] Separate Entra ID groups for each role
- [ ] No shared service principals across roles
- [ ] Publisher credentials scoped to specific BU/boundary
- [ ] Credential rotation enforced (PIM/JIT for Publishers)
- [ ] Publish actions require CAB approval record + correlation ID

---

## Correlation ID Audit Trail (MANDATORY)

### Every Event Must Include

```python
# ✅ CORRECT - All events include correlation_id
emit_event({
    "correlation_id": "dp-20260130-0001",
    "type": "deployment_intent.created",
    "status": "pending",
    "user_id": request.user.id,
    "timestamp": timezone.now().isoformat(),
})

# ❌ FORBIDDEN - Missing correlation_id
emit_event({
    "type": "deployment_intent.created",  # No correlation ID!
    "status": "pending",
})
```

### Correlation ID Requirements

- [ ] All deployment events tagged with correlation_id
- [ ] Error classification included (transient/permanent/policy_violation)
- [ ] Events stored in append-only event store (immutable)
- [ ] SIEM integration for privileged actions
- [ ] Correlation IDs map to execution plane artifacts

---

## Supply Chain Security

### SBOM Requirements

- [ ] SBOM generated for every artifact (SPDX or CycloneDX format)
- [ ] SBOM stored with artifact metadata in object store
- [ ] Provenance metadata includes: builder identity, pipeline run ID, inputs, timestamps, hashes

### Vulnerability Scanning

```bash
# Mandatory scan before any publish
trivy fs --security-checks vuln --severity HIGH,CRITICAL ./artifacts/

# Scan policy enforcement
# - Block Critical/High vulnerabilities by default
# - Exceptions require: expiry date + compensating controls + Security Reviewer approval
```

### Scan Policy Checklist

- [ ] All artifacts scanned with Trivy/Grype/Snyk
- [ ] Malware scanning included
- [ ] Scan results stored in evidence pack
- [ ] Critical/High findings block publish by default
- [ ] Exceptions linked to deployment intent with expiry

### Signing Requirements

| Platform | Requirement |
|----------|-------------|
| Windows | Code-signing (Authenticode) with enterprise certificate |
| macOS | Signed PKG + notarization (Developer ID Installer) |
| Linux | APT repository GPG keys |
| Mobile | App Store/Play Store signing |

---

## Evidence Pack Security

### Required Fields

- [ ] Artifact hashes (SHA-256)
- [ ] Artifact signatures
- [ ] SBOM (SPDX/CycloneDX)
- [ ] Vulnerability scan results
- [ ] Policy decision (pass/fail/exception)
- [ ] Rollout plan (rings, schedule, targeting)
- [ ] Rollback plan (plane-specific)
- [ ] Test evidence (lab + Ring 0 results)
- [ ] Exception records (with expiry dates)

### Evidence Pack Integrity

- [ ] Stored in WORM object storage (immutable)
- [ ] 7-year retention minimum
- [ ] Modifications require versioning + re-approval
- [ ] Schema versioned (v1.0, v1.1, etc.)

---

## Input Validation

### API Input Validation

```python
# ✅ CORRECT - Explicit validation with Zod (frontend) or DRF serializers
class DeploymentCreateSerializer(serializers.ModelSerializer):
    version = serializers.CharField(
        validators=[RegexValidator(r'^\d+\.\d+\.\d+$', 'Semantic version required')]
    )

    def validate_application_id(self, value):
        if not Application.objects.filter(id=value).exists():
            raise serializers.ValidationError("Application not found")
        return value
```

### SQL Injection Prevention

```python
# ✅ CORRECT - Django ORM (parameterized)
Deployment.objects.filter(status=user_input)

# ❌ FORBIDDEN - Raw SQL without parameterization
Deployment.objects.raw(f"SELECT * FROM deployment WHERE status = '{user_input}'")
```

### Validation Checklist

- [ ] All user input validated and sanitized
- [ ] SQL injection prevented (use ORM or parameterized queries)
- [ ] XSS prevention (output encoding, CSP headers)
- [ ] CSRF tokens on all state-changing operations
- [ ] File upload validation (type, size, content scanning)

---

## Data Protection

### Secrets Management

```python
# ✅ CORRECT - Vault integration
from apps.core.secrets import get_secret

api_key = get_secret('intune/api-key')  # From Azure Key Vault

# ❌ FORBIDDEN - Hardcoded secrets
API_KEY = "sk-1234567890abcdef"  # NEVER!
```

### Secrets Checklist

- [ ] All secrets in Azure Key Vault (production) or HashiCorp Vault (dev)
- [ ] Rotation policies enforced
- [ ] No secrets in source code or environment files
- [ ] Service principal credentials scoped and rotated
- [ ] Break-glass credentials require dual-control

### Encryption

- [ ] Sensitive data encrypted at rest (PostgreSQL TDE)
- [ ] TLS 1.3 for data in transit
- [ ] Key ownership documented (who owns signing keys)

---

## API Security

### Rate Limiting

```python
# ✅ CORRECT - Rate limiting on sensitive endpoints
@throttle_classes([StrictRateThrottle])
@permission_classes([IsAuthenticated])
def approve_deployment(request, correlation_id):
    ...
```

### API Security Checklist

- [ ] Rate limiting on all endpoints
- [ ] Authentication required (session-based)
- [ ] CORS properly configured (allowed origins only)
- [ ] API versioning via URL path (/api/v1/)
- [ ] Error messages don't leak sensitive info
- [ ] Correlation ID header (X-Correlation-ID) on all requests

---

## Security Headers

```python
# Django security middleware settings
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")  # For Tailwind
```

---

## OWASP Top 10 Checklist

| # | Vulnerability | EUCORA Mitigation |
|---|--------------|-------------------|
| 1 | Broken Access Control | ABAC Policy Engine + RBAC + SoD |
| 2 | Cryptographic Failures | TLS 1.3 + encryption at rest + secure key management |
| 3 | Injection | Django ORM + parameterized queries |
| 4 | Insecure Design | CAB approval workflow + evidence packs |
| 5 | Security Misconfiguration | Security headers + hardened defaults |
| 6 | Vulnerable Components | SBOM + vulnerability scanning + blocking |
| 7 | Authentication Failures | Session-based + MFA + Entra ID |
| 8 | Data Integrity Failures | Signed artifacts + SBOM + immutable evidence |
| 9 | Logging Failures | Correlation IDs + SIEM + append-only events |
| 10 | SSRF | Input validation + allowlisted external calls |

---

## CAB Security Requirements

### Risk > 50 Deployments

- [ ] CAB approval required before Ring 2+ promotion
- [ ] Evidence pack complete (all required fields)
- [ ] Approval recorded in immutable event store
- [ ] Correlation ID links approval to deployment

### Privileged Tooling

- [ ] Always requires CAB approval (regardless of risk score)
- [ ] Security Reviewer approval for exceptions
- [ ] Audit events logged to SIEM
- [ ] Rollback validated before Ring 2+

---

## Security Audit Checklist

### Pre-Deployment

```
☐ SBOM generated and stored
☐ Vulnerability scan passed (or approved exception)
☐ Artifact signed (platform-appropriate)
☐ Evidence pack complete
☐ CAB approval obtained (if Risk > 50)
```

### Post-Deployment

```
☐ Deployment event includes correlation_id
☐ Audit event logged to SIEM
☐ Rollback tested and validated
☐ Success metrics tracked
```

### Quarterly Review

```
☐ Publisher access reviewed (PIM/JIT)
☐ Service principal credentials rotated
☐ Exception records reviewed (expiry check)
☐ RBAC group membership audited
```
