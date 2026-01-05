# Scripts Folder Structure - Implementation Summary

**Date**: 2026-01-04
**Status**: ✅ Folder Structure Created

---

## Executive Summary

**YES, scripts are absolutely needed** to operationalize the Enterprise Endpoint Application Packaging & Deployment Factory architecture. A comprehensive folder structure has been **created and aligned** with the architecture.

**Folder Structure Created**: ✅ **46 directories** across 9 major categories

---

## Why Scripts Are Critical

### 1. **Control Plane Orchestration**
Scripts implement the thin control plane logic:
- Risk score calculation per [risk-model.md](../docs/architecture/risk-model.md)
- Deployment intent creation with correlation IDs
- Promotion gate evaluation (success rate ≥98%/97%/99%)
- Reconciliation loops (drift detection)

### 2. **Packaging Factory Automation**
Scripts enforce supply chain controls:
- SBOM generation (SPDX/CycloneDX) per [packaging-factory-rules.md](../.agents/rules/03-packaging-factory-rules.md)
- Vulnerability scanning (block Critical/High by default)
- Code signing (Windows Authenticode, macOS signing, Linux GPG)
- Provenance recording (builder identity, pipeline run ID)

### 3. **Execution Plane Integration**
Scripts provide idempotent connectors:
- Intune connector via Microsoft Graph API
- Jamf Pro connector for macOS
- SCCM connector for offline Windows sites
- Landscape/Ansible connectors for Linux

### 4. **Operational Runbooks**
Scripts execute operational procedures:
- Incident response (P0/P1/P2/P3 classification)
- Emergency rollback (≤4h SLA)
- Ring promotion (evaluate gates before promotion)
- Drift remediation

### 5. **Infrastructure Automation**
Scripts deploy and maintain infrastructure:
- HA/DR topology (99.9% availability, RPO ≤24h, RTO ≤8h)
- Secrets rotation (90-day certs, 30-day tokens)
- RBAC setup (Entra ID groups, PIM/JIT for Publishers)
- SIEM integration (alert rules, log forwarding)

---

## Folder Structure Overview

```
scripts/                          # 46 directories created
├── control-plane/               # 6 subdirs - Policy, orchestration, evidence
├── packaging-factory/           # 6 subdirs - Build, sign, scan, test
├── connectors/                  # 5 subdirs - Intune, Jamf, SCCM, Landscape, Ansible
├── infrastructure/              # 5 subdirs - HA/DR, secrets, keys, RBAC, SIEM
├── operations/                  # 5 subdirs - Incident, rollback, ring mgmt, drift, telemetry
├── utilities/                   # 3 subdirs - Common, validation, logging
├── cli/                         # 2 subdirs - Commands, modules (kubectl-like CLI)
├── maintenance/                 # 1 dir - Scheduled tasks
├── testing/                     # 3 subdirs - Unit, integration, E2E
└── config/                      # 1 dir - Configuration files
```

---

## Key Script Categories

### 1. Control Plane Scripts (6 folders)

**Purpose**: Implement thin control plane logic (policy + orchestration + evidence)

| Folder | Key Scripts | Purpose |
|---|---|---|
| `api-gateway/` | deploy-api-gateway.ps1, configure-waf-rules.ps1 | API Gateway deployment, WAF rules |
| `policy-engine/` | compute-risk-score.ps1, validate-scope.ps1 | Risk scoring, scope validation |
| `orchestrator/` | create-deployment-intent.ps1, trigger-ring-promotion.ps1 | Orchestration workflows |
| `cab-workflow/` | submit-to-cab.ps1, generate-evidence-pack.ps1 | CAB submission, evidence generation |
| `evidence-store/` | upload-evidence-pack.ps1, verify-evidence-immutability.ps1 | Evidence WORM storage |
| `event-store/` | append-deployment-event.ps1, query-events-by-correlation-id.ps1 | Immutable audit trail |

---

### 2. Packaging Factory Scripts (6 folders)

**Purpose**: Enforce supply chain controls (SBOM, scanning, signing, testing)

| Folder | Key Scripts | Purpose |
|---|---|---|
| `build/` | build-win32-package.ps1, build-msix-package.ps1 | Platform-specific builds |
| `signing/` | sign-windows-package.ps1, sign-macos-package.sh | Code signing with HSM certs |
| `sbom/` | generate-sbom-spdx.ps1, validate-sbom.ps1 | SBOM generation (SPDX/CycloneDX) |
| `scanning/` | scan-vulnerabilities-trivy.sh, enforce-scan-policy.ps1 | Vuln + malware scanning |
| `testing/` | test-install-uninstall.ps1, validate-detection-rules.ps1 | Ring 0 validation testing |
| `provenance/` | record-build-provenance.ps1 | Builder identity, pipeline tracking |

---

### 3. Connector Scripts (5 folders)

**Purpose**: Idempotent operations against execution planes

| Folder | Key Scripts | Purpose |
|---|---|---|
| `intune/` | publish-to-intune.ps1, verify-idempotency.ps1 | Graph API publish with idempotency |
| `jamf/` | publish-to-jamf.sh, pin-jamf-version.sh | Jamf Pro policy-based deployment |
| `sccm/` | publish-to-sccm.ps1, distribute-to-dps.ps1 | SCCM packages + DP distribution |
| `landscape/` | publish-to-landscape.sh, sync-apt-mirror.sh | Ubuntu Landscape + APT mirrors |
| `ansible/` | publish-to-awx.sh, execute-playbook.sh | AWX/Tower playbook execution |

---

### 4. Infrastructure Scripts (5 folders)

**Purpose**: Deploy and maintain HA/DR, secrets, keys, RBAC, SIEM

| Folder | Key Scripts | Purpose |
|---|---|---|
| `ha-dr/` | deploy-ha-topology.ps1, failover-test.ps1 | 99.9% availability, RPO/RTO |
| `secrets-management/` | rotate-service-principal-cert.ps1, audit-vault-access.ps1 | 90-day rotation, vault audit |
| `key-management/` | generate-code-signing-cert.ps1, rotate-signing-cert.ps1 | PKI, HSM FIPS 140-2 |
| `rbac/` | create-entra-groups.ps1, configure-pim.ps1 | SoD, JIT for Publishers |
| `siem/` | configure-log-forwarding.ps1, create-alert-rules.ps1 | Alert rules, compliance reports |

---

### 5. Operations Scripts (5 folders)

**Purpose**: Execute operational runbooks (incident response, rollback, telemetry)

| Folder | Key Scripts | Purpose |
|---|---|---|
| `incident-response/` | trigger-p0-p1-response.ps1, emergency-rollback.ps1 | ≤4h SLA rollback, CAB notification |
| `rollback/` | rollback-intune-ring.ps1, validate-rollback-success.ps1 | Plane-specific rollback strategies |
| `ring-management/` | promote-to-next-ring.ps1, query-ring-health.ps1 | Promotion gate evaluation |
| `drift-detection/` | detect-drift.ps1, remediate-drift.ps1 | Reconciliation loops |
| `telemetry/` | query-success-rate.ps1, generate-ring-dashboard.ps1 | Success rate, time-to-compliance |

---

### 6. Utilities Scripts (3 folders)

**Purpose**: Common functions (correlation IDs, retry, validation, logging)

| Folder | Key Scripts | Purpose |
|---|---|---|
| `common/` | Get-CorrelationId.ps1, Invoke-RetryWithBackoff.ps1 | UUIDv4 generation, exponential backoff |
| `validation/` | Test-EvidencePackCompleteness.ps1, Test-PromotionGates.ps1 | Validation functions |
| `logging/` | Write-StructuredLog.ps1, Send-SIEMEvent.ps1 | JSON logging, SIEM forwarding |

---

### 7. CLI Scripts (2 folders)

**Purpose**: Control Plane CLI (kubectl-like interface for operators)

**Example Usage**:
```powershell
# Deploy to Ring 1
.\control-plane-cli.ps1 deploy --artifact app-v2.4.1 --ring 1 --correlation-id dp-20260104-001

# Query status
.\control-plane-cli.ps1 status --correlation-id dp-20260104-001

# Submit to CAB
.\control-plane-cli.ps1 submit-cab --evidence-pack ep-abc123

# Trigger rollback
.\control-plane-cli.ps1 rollback --correlation-id dp-20260104-001 --ring 2
```

---

### 8. Maintenance Scripts (1 folder)

**Purpose**: Scheduled tasks (nightly/weekly/monthly)

| Script | Schedule | Purpose |
|---|---|---|
| `cleanup-old-artifacts.ps1` | Nightly | Purge artifacts > 90 days |
| `rotate-all-credentials.ps1` | Monthly | Batch credential rotation |
| `archive-audit-logs.ps1` | Weekly | Archive logs to cold storage |
| `update-risk-model-weights.ps1` | Quarterly | Risk model calibration |

---

### 9. Testing Scripts (3 folders)

**Purpose**: Unit, integration, E2E tests for CI/CD pipelines

| Folder | Test Type | Framework |
|---|---|---|
| `unit/` | Unit tests for utilities, risk scoring | Pester (PowerShell) |
| `integration/` | Integration tests for connectors | Pester, Bash test frameworks |
| `e2e/` | End-to-end tests for ring promotion | Pester, Bash |

---

## Technology Stack

| Script Type | Primary Tech | Dependencies |
|---|---|---|
| Control Plane | PowerShell 7+ | Az.* modules, Microsoft.Graph SDK |
| Packaging (Windows) | PowerShell 7+ | signtool, MSBuild, Windows SDK |
| Packaging (macOS) | Bash | codesign, notarytool, Xcode CLI tools |
| Packaging (Linux) | Bash | dpkg-deb, rpmbuild, GPG, debhelper |
| SBOM | Bash/PowerShell | Syft, CycloneDX CLI |
| Scanning | Bash/PowerShell | Trivy, Grype, Snyk |
| Intune Connector | PowerShell 7+ | Microsoft.Graph SDK |
| Jamf Connector | Bash | curl, jq, Jamf Pro API |
| SCCM Connector | PowerShell 5.1+ | ConfigMgr module |
| Landscape Connector | Bash | landscape-api CLI |
| Ansible Connector | Bash | ansible, awx CLI |
| HA/DR | PowerShell 7+ | Azure CLI, Bicep |
| SIEM | PowerShell 7+ | Az.Monitor, KQL |

---

## Naming Conventions

### PowerShell Scripts
- **Verb-Noun** pattern: `Get-CorrelationId.ps1`, `Invoke-RetryWithBackoff.ps1`
- Approved verbs: `Get`, `Set`, `New`, `Remove`, `Invoke`, `Test`, `Submit`, `Publish`, `Query`

### Bash Scripts
- **kebab-case**: `sign-macos-package.sh`, `sync-apt-mirror.sh`
- `.sh` extension

### Module Files
- **PascalCase**: `ControlPlaneAPI.psm1`, `ConnectorFactory.psm1`
- `.psm1` extension for PowerShell modules

---

## Security Requirements

### ❌ FORBIDDEN
- Hardcoded credentials in scripts
- Storing secrets in environment variables
- Command injection via string concatenation
- Path traversal attacks (no `../` in file paths)

### ✅ REQUIRED
- All credentials stored in Azure Key Vault
- Scripts use Managed Identities or service principal certs
- All vault access logged to SIEM
- All user inputs validated (UUIDs, ring numbers 0-4, etc.)
- All privileged operations logged with correlation IDs

---

## Configuration Management

### Configuration Files (`scripts/config/`)

```json
// settings.json - Global settings
{
  "control_plane_api_url": "https://api.control-plane.corp/v1",
  "azure_tenant_id": "00000000-0000-0000-0000-000000000000",
  "key_vault_name": "kv-control-plane-prod",
  "siem_workspace_id": "22222222-2222-2222-2222-222222222222",
  "retry_max_attempts": 5,
  "retry_base_seconds": 4,
  "retry_max_seconds": 60,
  "circuit_breaker_threshold": 5
}
```

```json
// risk-model-v1.0.json - Risk model weights
{
  "version": "v1.0",
  "factors": {
    "privilege_impact": {"weight": 20, "max_normalized": 1.0},
    "supply_chain_trust": {"weight": 15, "max_normalized": 1.0},
    "exploitability": {"weight": 10, "max_normalized": 1.0},
    "data_access": {"weight": 10, "max_normalized": 1.0},
    "sbom_vulnerability": {"weight": 15, "max_normalized": 1.0},
    "blast_radius": {"weight": 10, "max_normalized": 1.0},
    "operational_complexity": {"weight": 10, "max_normalized": 1.0},
    "history": {"weight": 10, "max_normalized": 1.0}
  },
  "thresholds": {
    "automated_allowed": 50,
    "cab_required": 51
  }
}
```

```json
// promotion-gates.json - Success rate thresholds
{
  "ring_0_lab": {"success_rate": 0.95, "time_to_compliance_hours": 4},
  "ring_1_canary": {"success_rate": 0.98, "time_to_compliance_hours": 24},
  "ring_2_pilot": {"success_rate": 0.97, "time_to_compliance_hours": 24},
  "ring_3_department": {"success_rate": 0.99, "time_to_compliance_hours": 24},
  "ring_4_global": {"success_rate": 0.99, "time_to_compliance_hours": 24}
}
```

---

## CI/CD Integration

### Pre-Commit Hook (PowerShell Script Analyzer)
```yaml
# .pre-commit-config.yaml addition
  - repo: local
    hooks:
      - id: powershell-scriptanalyzer
        name: PowerShell Script Analyzer
        entry: pwsh -Command "Invoke-ScriptAnalyzer -Path scripts/ -Recurse -Severity Error"
        language: system
        files: \.ps1$
```

### GitHub Actions / Azure Pipelines
```yaml
# .github/workflows/test-scripts.yml
name: Test Scripts
on: [push, pull_request]
jobs:
  test-powershell:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test PowerShell Scripts
        run: Invoke-Pester -Path scripts/testing/ -Output Detailed

  test-bash:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Bash Scripts
        run: bash scripts/testing/integration/test-all.sh
```

---

## Documentation Requirements

### Per-Script Header Template
```powershell
<#
.SYNOPSIS
    [One-line description]

.DESCRIPTION
    [Detailed description referencing architecture docs]
    Implements [component/pattern] per [docs link].

.PARAMETER ParameterName
    [Parameter description]

.EXAMPLE
    .\script-name.ps1 -Parameter "value"

.NOTES
    Version: 1.0
    Author: Platform Engineering
    Related Docs: [links to architecture docs, agent rules]
#>
```

### README per Folder
Each script subfolder should have a `README.md`:
- Purpose of scripts in folder
- Prerequisites (modules, credentials, access)
- Usage examples
- Related documentation links

---

## Implementation Priority

### Phase 1: Foundation (Week 1-2)
1. ✅ Create folder structure **COMPLETED**
2. Create `utilities/common/` functions (Get-CorrelationId, Invoke-RetryWithBackoff)
3. Create `utilities/validation/` functions (Test-EvidencePackCompleteness)
4. Create `utilities/logging/` functions (Write-StructuredLog, Send-SIEMEvent)
5. Create `scripts/config/` configuration files (settings.json, risk-model-v1.0.json)

### Phase 2: CLI & Control Plane (Week 3-4)
6. Create `cli/control-plane-cli.ps1` skeleton with basic commands
7. Create `control-plane/policy-engine/compute-risk-score.ps1`
8. Create `control-plane/orchestrator/create-deployment-intent.ps1`
9. Create `control-plane/cab-workflow/generate-evidence-pack.ps1`

### Phase 3: Connectors (Week 5-8)
10. Create `connectors/intune/publish-to-intune.ps1` (MVP connector)
11. Create `connectors/intune/verify-idempotency.ps1`
12. Create `connectors/intune/rollback-intune-deployment.ps1`
13. Extend to Jamf/SCCM/Landscape/Ansible connectors

### Phase 4: Packaging Factory (Week 9-12)
14. Create `packaging-factory/sbom/generate-sbom-spdx.ps1`
15. Create `packaging-factory/scanning/scan-vulnerabilities-trivy.sh`
16. Create `packaging-factory/signing/sign-windows-package.ps1`
17. Create `packaging-factory/testing/test-install-uninstall.ps1`

### Phase 5: Operations & Infrastructure (Week 13-16)
18. Create `operations/incident-response/trigger-p0-p1-response.ps1`
19. Create `operations/rollback/emergency-rollback.ps1`
20. Create `infrastructure/ha-dr/deploy-ha-topology.ps1`
21. Create `infrastructure/rbac/create-entra-groups.ps1`

---

## Related Documentation

- **Folder Structure Proposal**: [SCRIPTS_FOLDER_STRUCTURE_PROPOSAL.md](SCRIPTS_FOLDER_STRUCTURE_PROPOSAL.md)
- **Architecture Overview**: [architecture-overview.md](../docs/architecture/architecture-overview.md)
- **Control Plane Design**: [control-plane-design.md](../docs/architecture/control-plane-design.md)
- **Connector Rules**: [08-connector-rules.md](../.agents/rules/08-connector-rules.md)
- **Packaging Factory Rules**: [03-packaging-factory-rules.md](../.agents/rules/03-packaging-factory-rules.md)
- **Testing Quality Rules**: [11-testing-quality-rules.md](../.agents/rules/11-testing-quality-rules.md)

---

## Summary

### ✅ Scripts Are Critical
Scripts operationalize the entire architecture:
- Control Plane orchestration
- Packaging Factory automation
- Execution Plane integration
- Operational runbooks
- Infrastructure deployment

### ✅ Folder Structure Created
**46 directories** organized into **9 major categories**:
- control-plane/ (6 subdirs)
- packaging-factory/ (6 subdirs)
- connectors/ (5 subdirs)
- infrastructure/ (5 subdirs)
- operations/ (5 subdirs)
- utilities/ (3 subdirs)
- cli/ (2 subdirs)
- maintenance/ (1 dir)
- testing/ (3 subdirs)
- config/ (1 dir)

### ✅ Aligned with Architecture
All script categories map directly to architecture components:
- Thin control plane principle (policy + orchestration + evidence)
- Separation of duties (Packaging ≠ Publishing ≠ Approval)
- Idempotency (correlation IDs, verify_idempotency())
- Evidence-first governance (evidence pack generation)
- Offline-first (SCCM DP, APT mirrors)

### ✅ Technology Stack Defined
- PowerShell 7+ for Control Plane, Windows packaging, connectors
- Bash for macOS/Linux packaging, Jamf/Landscape/Ansible connectors
- Trivy/Grype for vulnerability scanning
- Syft/CycloneDX for SBOM generation
- Microsoft.Graph SDK for Intune integration

---

**Implementation Status**: ✅ Folder structure created, ready for script development
**Next Step**: Implement Phase 1 (Foundation utilities and configuration files)
