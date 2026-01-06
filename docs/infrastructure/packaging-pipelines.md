# Packaging Pipelines

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Packaging pipelines are **reproducible build processes** that transform source artifacts into enterprise-ready packages with supply chain controls (signing, SBOM, vulnerability scanning).

**Design Principle**: Supply Chain Gates — all artifacts must pass mandatory gates before publication.

---

## Pipeline Stages

### 1. Build Stage

**Inputs**:
- Source artifacts (MSI, EXE, PKG, DEB, etc.)
- Build configuration
- Version metadata

**Outputs**:
- Platform-specific package (MSIX, .intunewin, PKG, APT package)

**Requirements**:
- Reproducible builds (deterministic outputs)
- Idempotent operations (safe retries)

### 2. Signing Stage

**Windows**:
- Code-signing with enterprise certificate
- Timestamp server integration

**macOS**:
- Package signing with Developer ID
- Notarization (where applicable)

**Linux**:
- APT repository signing with GPG key

**Outputs**:
- Signed package
- Signing certificate metadata
- Notarization ticket (macOS)

### 3. SBOM Generation Stage

**Format**: SPDX or CycloneDX  
**Tool**: syft, cyclonedx-cli, or enterprise-standard tool

**Outputs**:
- SBOM file (JSON/XML)
- Component inventory
- Dependency tree

### 4. Vulnerability Scanning Stage

**Tools**: Trivy, Grype, Snyk, or enterprise-standard scanner  
**Additional**: Malware scanning (ClamAV, Windows Defender)

**Outputs**:
- Vulnerability scan report
- Policy decision (pass/fail/exception)
- CVE list with severity

**Policy**:
- **Block Critical/High** vulnerabilities by default
- Exceptions require Security Reviewer approval

### 5. Testing Stage

**Types**:
- Install/uninstall testing
- Detection rule validation
- Silent install verification
- Exit code mapping validation

**Outputs**:
- Test evidence report
- Installation logs
- Test results

### 6. Artifact Storage Stage

**Storage**: Immutable object store (MinIO/S3)  
**Metadata**:
- SHA-256 hash
- Signing metadata
- SBOM reference
- Scan results
- Provenance data

**Outputs**:
- Artifact URL
- Artifact metadata record

---

## Pipeline Configuration

### Windows Pipeline

```yaml
stages:
  - build:
      tool: intunewinutil
      inputs: [msi_file, install_cmd, uninstall_cmd, detection_rules]
  - sign:
      tool: signtool
      certificate: enterprise_code_signing_cert
      timestamp_server: http://timestamp.digicert.com
  - sbom:
      tool: syft
      format: spdx-json
  - scan:
      tool: trivy
      severity: [CRITICAL, HIGH, MEDIUM, LOW]
  - test:
      script: test-install.ps1
  - store:
      bucket: eucora-artifacts
      path: windows/{app_name}/{version}/
```

### macOS Pipeline

```yaml
stages:
  - build:
      tool: pkgbuild
      inputs: [pkg_source, install_scripts]
  - sign:
      tool: codesign
      identity: Developer ID Application
  - notarize:
      tool: notarytool
      team_id: {team_id}
  - sbom:
      tool: syft
      format: spdx-json
  - scan:
      tool: trivy
  - test:
      script: test-install.sh
  - store:
      bucket: eucora-artifacts
      path: macos/{app_name}/{version}/
```

### Linux Pipeline

```yaml
stages:
  - build:
      tool: dpkg-buildpackage
      inputs: [source_dir, debian_control]
  - sign:
      tool: debsign
      key: apt_repo_signing_key
  - sbom:
      tool: cyclonedx-cli
      format: json
  - scan:
      tool: trivy
  - test:
      script: test-install.sh
  - store:
      bucket: eucora-artifacts
      path: linux/{app_name}/{version}/
```

---

## Idempotency

All pipeline stages are **idempotent**:
- Same inputs → same outputs
- Safe to retry failed stages
- Deterministic artifact hashes

**Implementation**:
- Use deterministic build tools
- Pin dependency versions
- Use idempotent storage operations

---

## Provenance

All artifacts include provenance metadata:

```json
{
  "provenance": {
    "builder_identity": "packaging-engineer@example.com",
    "pipeline_run_id": "uuid",
    "pipeline_version": "1.0",
    "build_timestamp": "2026-01-06T10:00:00Z",
    "source_references": [
      "https://github.com/vendor/app/releases/tag/v1.2.3"
    ],
    "inputs": {
      "source_hash": "sha256:abc123...",
      "build_config_hash": "sha256:def456..."
    }
  }
}
```

---

## Failure Handling

### Stage Failures

1. **Retry**: Automatic retry (3 attempts with exponential backoff)
2. **Notification**: Alert packaging engineer
3. **Logging**: Detailed error logs in event store

### Policy Failures

1. **Block**: Artifact blocked from publication
2. **Exception Workflow**: Security Reviewer approval required
3. **Audit**: Failure recorded in event store

---

## References

- [Signing Procedures](./signing-procedures.md)
- [SBOM Generation](./sbom-generation.md)
- [Vulnerability Scan Policy](./vuln-scan-policy.md)
- [Evidence Pack Schema](../architecture/evidence-pack-schema.md)

