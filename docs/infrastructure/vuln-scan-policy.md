# Vulnerability Scan Policy

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This document defines the **mandatory vulnerability scanning policy** for all artifacts. Packages with Critical/High vulnerabilities are **blocked** by default unless an approved exception exists.

**Design Principle**: Supply Chain Security — all artifacts must pass vulnerability scans or have approved exceptions.

---

## Scan Tools

### Recommended Tools

1. **Trivy** (Aqua Security)
   - Supports: All platforms
   - Databases: OSV, NVD, GitHub Security Advisories
   - Integration: CLI, API

2. **Grype** (Anchore)
   - Supports: All platforms
   - Databases: Multiple CVE databases
   - Integration: CLI, API

3. **Snyk**
   - Supports: All platforms
   - Databases: Snyk vulnerability database
   - Integration: CLI, API, SaaS

4. **Enterprise Tools**
   - Qualys, Rapid7, or approved enterprise scanner

### Tool Selection

- **Default**: Trivy (open-source, comprehensive)
- **Alternative**: Enterprise-approved scanner
- **Multi-Tool**: Use multiple tools for critical packages

---

## Scan Policy

### Severity Levels

- **Critical**: CVSS 9.0-10.0
- **High**: CVSS 7.0-8.9
- **Medium**: CVSS 4.0-6.9
- **Low**: CVSS 0.1-3.9

### Blocking Rules

**Default Policy**:
- **Block**: Critical and High vulnerabilities
- **Allow**: Medium and Low vulnerabilities (with monitoring)

**Scan Result Actions**:
- **Pass**: No Critical/High vulnerabilities → Proceed to publication
- **Fail**: Critical/High vulnerabilities present → Block publication
- **Exception**: Approved exception → Allow with compensating controls

---

## Exception Process

### Exception Requirements

1. **Security Reviewer Approval**: Required for all exceptions
2. **Justification**: Documented reason for exception
3. **Compensating Controls**: Specific, measurable controls
4. **Expiry Date**: Maximum 90 days

### Exception Types

1. **False Positive**: Vulnerability not applicable to deployment context
2. **Mitigated**: Vulnerability mitigated by compensating controls
3. **Critical Patch**: Security patch with known vulnerabilities (temporary)

### Exception Workflow

1. **Request Exception**: Packaging engineer submits exception request
2. **Security Review**: Security Reviewer evaluates request
3. **Approval/Denial**: Decision recorded in evidence store
4. **Monitoring**: Compensating controls monitored during exception period
5. **Expiry**: Exception expires automatically, re-approval required

---

## Scan Execution

### Pipeline Integration

1. **After SBOM Generation**
   - Scan package using SBOM
   - Scan package binary (if applicable)

2. **Scan Results Processing**
   - Parse scan results
   - Apply policy rules
   - Generate policy decision

3. **Policy Decision**
   - **Pass**: No blocking vulnerabilities
   - **Fail**: Blocking vulnerabilities present
   - **Exception**: Approved exception exists

### Command Examples

**Trivy**:
```bash
trivy image --severity HIGH,CRITICAL package.tar
trivy fs --severity HIGH,CRITICAL ./package-directory
```

**Grype**:
```bash
grype package.deb --only-fixed --fail-on high
```

---

## Scan Results Storage

### Storage Location

- **Artifact Store**: MinIO/S3 bucket `eucora-scan-results/`
- **Path Pattern**: `{platform}/{app_name}/{version}/scan.{format}`
- **Metadata**: Linked to artifact record

### Result Format

```json
{
  "scan_id": "uuid",
  "artifact_id": "uuid",
  "scan_tool": "trivy",
  "scan_timestamp": "2026-01-06T10:00:00Z",
  "vulnerabilities": [
    {
      "cve": "CVE-2024-1234",
      "severity": "HIGH",
      "component": "library-v1.2.3",
      "description": "Vulnerability description",
      "fixed_version": "1.2.4"
    }
  ],
  "policy_decision": "pass|fail|exception",
  "exception_id": "uuid"
}
```

---

## Malware Scanning

### Additional Scanning

- **Windows**: Windows Defender, ClamAV
- **macOS**: XProtect, ClamAV
- **Linux**: ClamAV

### Integration

- Run malware scan after vulnerability scan
- Block if malware detected (zero tolerance)
- No exceptions for malware detection

---

## Continuous Monitoring

### Post-Deployment Scanning

- **Frequency**: Weekly scans of deployed packages
- **New Vulnerabilities**: Alert if new vulnerabilities discovered
- **Remediation**: Trigger update workflow if critical vulnerabilities found

### Dependency Scanning

- **SBOM-Based**: Scan dependencies from SBOM
- **Frequency**: On every SBOM update
- **Alerting**: Notify if new vulnerabilities in dependencies

---

## References

- [SBOM Generation](./sbom-generation.md)
- [Exception Management](../architecture/exception-management.md)
- [Packaging Pipelines](./packaging-pipelines.md)
