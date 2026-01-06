# Evidence Pack Generation Runbook

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

This runbook provides step-by-step procedures for generating **complete evidence packs** required for CAB submissions.

**Requirement**: All evidence packs MUST include all required fields (no partial submissions).

---

## Prerequisites

- Package built and signed
- SBOM generated
- Vulnerability scan completed
- Test evidence available
- Rollback plan documented

---

## Evidence Pack Components

### 1. Artifact Information

- **Artifact Hash**: SHA-256 hash
- **Signature**: Signing certificate thumbprint
- **Notarization**: Notarization ticket (macOS)
- **Package Metadata**: Name, version, platform

### 2. SBOM Data

- **SBOM Format**: SPDX or CycloneDX
- **SBOM Hash**: SHA-256 hash of SBOM file
- **Component Inventory**: Complete dependency list

### 3. Vulnerability Scan Results

- **Scan Tool**: Trivy, Grype, Snyk, or enterprise tool
- **Scan Report**: Complete scan results
- **Policy Decision**: Pass/fail/exception
- **CVE List**: All vulnerabilities with severity

### 4. Test Evidence

- **Install Testing**: Lab test results
- **Uninstall Testing**: Uninstall test results
- **Detection Rules**: Detection rule validation
- **Ring 0 Results**: Automation test results

### 5. Rollout Plan

- **Ring Progression**: Lab → Canary → Pilot → Department → Global
- **Schedule**: Deployment timeline
- **Targeting**: Device groups/collections
- **Exclusions**: Excluded devices/groups

### 6. Rollback Plan

- **Rollback Strategy**: Plane-specific strategy
- **Rollback Commands**: Uninstall/downgrade commands
- **Rollback Testing**: Rollback test results
- **Estimated Duration**: Rollback time estimate

### 7. Exception Records

- **Exceptions**: Any approved exceptions
- **Expiry Dates**: Exception expiry dates
- **Compensating Controls**: Compensating control details

---

## Generation Process

### Step 1: Collect Artifact Information

```bash
# Generate SHA-256 hash
sha256sum package.msi > package.sha256

# Extract signature information
signtool verify /pa /v package.msi
```

### Step 2: Generate SBOM

```bash
# Generate SPDX SBOM
syft packages package.msi -o spdx-json > package.spdx.json

# Generate SHA-256 hash of SBOM
sha256sum package.spdx.json > package.spdx.sha256
```

### Step 3: Run Vulnerability Scan

```bash
# Run Trivy scan
trivy image --severity HIGH,CRITICAL package.tar > scan-results.json

# Generate policy decision
python scripts/utilities/evaluate-scan-policy.py scan-results.json
```

### Step 4: Collect Test Evidence

- Install test logs
- Uninstall test logs
- Detection rule validation results
- Ring 0 automation test results

### Step 5: Document Rollout Plan

- Define ring progression
- Specify targeting groups
- Document exclusions
- Set deployment schedule

### Step 6: Document Rollback Plan

- Define rollback strategy (plane-specific)
- Document rollback commands
- Include rollback test results
- Estimate rollback duration

### Step 7: Compile Evidence Pack

```python
evidence_pack = {
    "artifact_hash": "sha256:abc123...",
    "signature": {...},
    "sbom_data": {...},
    "vulnerability_scan_results": {...},
    "test_evidence": {...},
    "rollout_plan": {...},
    "rollback_plan": {...},
    "exceptions": [...]
}
```

### Step 8: Store Evidence Pack

- Store in evidence store (immutable)
- Link to deployment intent
- Generate evidence pack ID

---

## Validation Checklist

- [ ] Artifact hash present
- [ ] Signature information present
- [ ] SBOM data present
- [ ] Vulnerability scan results present
- [ ] Policy decision present
- [ ] Test evidence present
- [ ] Rollout plan present
- [ ] Rollback plan present
- [ ] Exception records present (if applicable)
- [ ] All fields validated

---

## References

- [Evidence Pack Schema](../architecture/evidence-pack-schema.md)
- [CAB Submission](./cab-submission.md)
- [Risk Model](../architecture/risk-model.md)

