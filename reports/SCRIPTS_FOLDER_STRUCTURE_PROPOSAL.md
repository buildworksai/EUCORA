# Scripts Folder Structure Proposal

**Version**: 1.0
**Date**: 2026-01-04
**Status**: Proposed

---

## Overview

This document proposes a comprehensive script folder structure aligned with the Enterprise Endpoint Application Packaging & Deployment Factory architecture. Scripts are organized by **Control Plane component**, **execution plane**, and **operational workflow**.

**Design Principle**: Scripts enforce the thin control plane discipline, with clear separation between policy/orchestration (Control Plane) and execution (Intune/Jamf/SCCM/Landscape/Ansible).

---

## Proposed Folder Structure

```
scripts/
├── control-plane/                    # Control Plane orchestration scripts
│   ├── api-gateway/
│   │   ├── deploy-api-gateway.ps1
│   │   ├── configure-waf-rules.ps1
│   │   └── rotate-api-certs.ps1
│   ├── policy-engine/
│   │   ├── compute-risk-score.ps1
│   │   ├── validate-scope.ps1
│   │   └── evaluate-promotion-gates.ps1
│   ├── orchestrator/
│   │   ├── create-deployment-intent.ps1
│   │   ├── trigger-ring-promotion.ps1
│   │   └── execute-reconciliation-loop.ps1
│   ├── cab-workflow/
│   │   ├── submit-to-cab.ps1
│   │   ├── generate-evidence-pack.ps1
│   │   └── approve-deployment.ps1
│   ├── evidence-store/
│   │   ├── upload-evidence-pack.ps1
│   │   ├── verify-evidence-immutability.ps1
│   │   └── query-evidence-pack.ps1
│   └── event-store/
│       ├── append-deployment-event.ps1
│       ├── query-events-by-correlation-id.ps1
│       └── export-audit-trail.ps1
│
├── packaging-factory/                # Packaging & Publishing Factory scripts
│   ├── build/
│   │   ├── build-win32-package.ps1
│   │   ├── build-msix-package.ps1
│   │   ├── build-macos-pkg.ps1
│   │   └── build-linux-deb.ps1
│   ├── signing/
│   │   ├── sign-windows-package.ps1
│   │   ├── sign-macos-package.sh
│   │   ├── sign-linux-repo.sh
│   │   └── notarize-macos-package.sh
│   ├── sbom/
│   │   ├── generate-sbom-spdx.ps1
│   │   ├── generate-sbom-cyclonedx.ps1
│   │   └── validate-sbom.ps1
│   ├── scanning/
│   │   ├── scan-vulnerabilities-trivy.sh
│   │   ├── scan-vulnerabilities-grype.sh
│   │   ├── scan-malware-defender.ps1
│   │   └── enforce-scan-policy.ps1
│   ├── testing/
│   │   ├── test-install-uninstall.ps1
│   │   ├── validate-detection-rules.ps1
│   │   └── test-rollback-strategy.ps1
│   └── provenance/
│       ├── record-build-provenance.ps1
│       └── verify-artifact-provenance.ps1
│
├── connectors/                       # Execution Plane connector scripts
│   ├── intune/
│   │   ├── publish-to-intune.ps1
│   │   ├── query-intune-status.ps1
│   │   ├── rollback-intune-deployment.ps1
│   │   ├── verify-idempotency.ps1
│   │   └── handle-graph-throttling.ps1
│   ├── jamf/
│   │   ├── publish-to-jamf.sh
│   │   ├── query-jamf-status.sh
│   │   ├── rollback-jamf-deployment.sh
│   │   └── pin-jamf-version.sh
│   ├── sccm/
│   │   ├── publish-to-sccm.ps1
│   │   ├── distribute-to-dps.ps1
│   │   ├── query-sccm-status.ps1
│   │   └── rollback-sccm-deployment.ps1
│   ├── landscape/
│   │   ├── publish-to-landscape.sh
│   │   ├── sync-apt-mirror.sh
│   │   ├── query-landscape-compliance.sh
│   │   └── remediate-drift.sh
│   └── ansible/
│       ├── publish-to-awx.sh
│       ├── execute-playbook.sh
│       ├── query-playbook-status.sh
│       └── rollback-via-ansible.sh
│
├── infrastructure/                   # Infrastructure setup & maintenance
│   ├── ha-dr/
│   │   ├── deploy-ha-topology.ps1
│   │   ├── failover-test.ps1
│   │   ├── backup-database.ps1
│   │   ├── restore-database.ps1
│   │   └── verify-geo-replication.ps1
│   ├── secrets-management/
│   │   ├── create-key-vault.ps1
│   │   ├── rotate-service-principal-cert.ps1
│   │   ├── rotate-api-token.ps1
│   │   └── audit-vault-access.ps1
│   ├── key-management/
│   │   ├── generate-code-signing-cert.ps1
│   │   ├── rotate-signing-cert.ps1
│   │   ├── revoke-signing-cert.ps1
│   │   └── export-public-key.ps1
│   ├── rbac/
│   │   ├── create-entra-groups.ps1
│   │   ├── assign-service-principal-permissions.ps1
│   │   ├── configure-pim.ps1
│   │   ├── create-break-glass-account.ps1
│   │   └── quarterly-access-review.ps1
│   └── siem/
│       ├── configure-log-forwarding.ps1
│       ├── create-alert-rules.ps1
│       ├── test-siem-integration.ps1
│       └── generate-compliance-report.ps1
│
├── operations/                       # Operational runbook scripts
│   ├── incident-response/
│   │   ├── trigger-p0-p1-response.ps1
│   │   ├── halt-deployments.ps1
│   │   ├── emergency-rollback.ps1
│   │   ├── notify-cab.ps1
│   │   └── generate-postmortem-report.ps1
│   ├── rollback/
│   │   ├── rollback-intune-ring.ps1
│   │   ├── rollback-jamf-ring.sh
│   │   ├── rollback-sccm-ring.ps1
│   │   ├── rollback-linux-ring.sh
│   │   ├── validate-rollback-success.ps1
│   │   └── rollback-all-rings.ps1
│   ├── ring-management/
│   │   ├── promote-to-next-ring.ps1
│   │   ├── pause-ring-promotion.ps1
│   │   ├── resume-ring-promotion.ps1
│   │   └── query-ring-health.ps1
│   ├── drift-detection/
│   │   ├── detect-drift.ps1
│   │   ├── remediate-drift.ps1
│   │   └── report-drift-summary.ps1
│   └── telemetry/
│       ├── query-success-rate.ps1
│       ├── query-time-to-compliance.ps1
│       ├── generate-ring-dashboard.ps1
│       └── export-telemetry-csv.ps1
│
├── utilities/                        # Common utility functions
│   ├── common/
│   │   ├── Get-CorrelationId.ps1
│   │   ├── Write-AuditEvent.ps1
│   │   ├── Test-IdempotencyKey.ps1
│   │   ├── Invoke-RetryWithBackoff.ps1
│   │   └── Get-ConfigValue.ps1
│   ├── validation/
│   │   ├── Test-EvidencePackCompleteness.ps1
│   │   ├── Test-ScopeValidity.ps1
│   │   ├── Test-CABApproval.ps1
│   │   └── Test-PromotionGates.ps1
│   └── logging/
│       ├── Write-StructuredLog.ps1
│       ├── Send-SIEMEvent.ps1
│       └── Export-AuditTrail.ps1
│
├── cli/                              # Control Plane CLI tool
│   ├── control-plane-cli.ps1        # Main CLI entry point
│   ├── commands/
│   │   ├── Deploy.ps1                # deploy --artifact <id> --ring <n>
│   │   ├── Rollback.ps1              # rollback --correlation-id <id>
│   │   ├── Submit-CAB.ps1            # submit-cab --evidence-pack <id>
│   │   ├── Query-Status.ps1          # status --correlation-id <id>
│   │   └── Generate-Report.ps1       # report --type telemetry
│   └── modules/
│       ├── ControlPlaneAPI.psm1
│       ├── ConnectorFactory.psm1
│       └── TelemetryClient.psm1
│
├── maintenance/                      # Scheduled maintenance tasks
│   ├── cleanup-old-artifacts.ps1
│   ├── rotate-all-credentials.ps1
│   ├── purge-expired-evidence-packs.ps1
│   ├── archive-audit-logs.ps1
│   └── update-risk-model-weights.ps1
│
└── testing/                          # Test scripts for CI/CD
    ├── unit/
    │   ├── Test-RiskScoreCalculation.Tests.ps1
    │   ├── Test-ScopeValidation.Tests.ps1
    │   └── Test-PromotionGates.Tests.ps1
    ├── integration/
    │   ├── Test-IntuneConnector.Tests.ps1
    │   ├── Test-JamfConnector.Tests.sh
    │   ├── Test-SCCMConnector.Tests.ps1
    │   └── Test-EvidencePackGeneration.Tests.ps1
    └── e2e/
        ├── Test-Ring0ToRing1Promotion.Tests.ps1
        ├── Test-CABWorkflow.Tests.ps1
        └── Test-RollbackExecution.Tests.ps1
```

---

## Script Categories Explained

### 1. Control Plane Scripts (`control-plane/`)

**Purpose**: Orchestrate policy, approvals, and evidence collection.

**Key Scripts**:
- `compute-risk-score.ps1` - Implements risk formula from [risk-model.md](../docs/architecture/risk-model.md)
- `create-deployment-intent.ps1` - Creates deployment intent with correlation ID
- `submit-to-cab.ps1` - Submits evidence pack to CAB workflow
- `execute-reconciliation-loop.ps1` - Detects drift between desired vs actual state

**Technology**: PowerShell 7+ (cross-platform), Azure PowerShell modules

---

### 2. Packaging Factory Scripts (`packaging-factory/`)

**Purpose**: Build, sign, scan, and test artifacts with supply chain controls.

**Key Scripts**:
- `sign-windows-package.ps1` - Signs with Authenticode using Azure Key Vault HSM
- `generate-sbom-spdx.ps1` - Generates SPDX SBOM per [packaging-factory-rules.md](../.agents/rules/03-packaging-factory-rules.md)
- `scan-vulnerabilities-trivy.sh` - Scans for Critical/High CVEs
- `test-install-uninstall.ps1` - Validates install/uninstall in Ring 0

**Technology**: PowerShell, Bash, Trivy, Grype, Syft (SBOM), signtool, codesign

---

### 3. Connector Scripts (`connectors/`)

**Purpose**: Idempotent operations against execution planes (Intune/Jamf/SCCM/Landscape/Ansible).

**Key Scripts**:
- `publish-to-intune.ps1` - Publishes via Graph API with idempotency check per [intune/connector-spec.md](../docs/modules/intune/connector-spec.md)
- `rollback-intune-deployment.ps1` - Executes supersedence rollback
- `verify-idempotency.ps1` - Checks correlation_id existence before publish
- `handle-graph-throttling.ps1` - Implements exponential backoff + circuit breaker

**Technology**: PowerShell (Intune/SCCM), Bash (Jamf/Landscape/Ansible), Microsoft Graph SDK, Jamf Pro API, AWX/Tower API

---

### 4. Infrastructure Scripts (`infrastructure/`)

**Purpose**: Setup HA/DR, secrets, keys, RBAC, SIEM per [infrastructure docs](../docs/infrastructure/).

**Key Scripts**:
- `deploy-ha-topology.ps1` - Deploys Azure resources per [ha-dr-requirements.md](../docs/infrastructure/ha-dr-requirements.md)
- `rotate-service-principal-cert.ps1` - 90-day rotation per [key-management.md](../docs/infrastructure/key-management.md)
- `configure-pim.ps1` - Sets up JIT for Publisher role per [rbac-configuration.md](../docs/infrastructure/rbac-configuration.md)
- `create-alert-rules.ps1` - Creates SIEM alerts per [siem-integration.md](../docs/infrastructure/siem-integration.md)

**Technology**: Azure PowerShell, Azure CLI, Bicep/ARM templates, Terraform (optional)

---

### 5. Operations Scripts (`operations/`)

**Purpose**: Execute operational runbooks (incident response, rollback, ring management).

**Key Scripts**:
- `trigger-p0-p1-response.ps1` - Executes [incident-response.md](../docs/runbooks/incident-response.md) runbook
- `emergency-rollback.ps1` - ≤4h SLA rollback per [rollback-execution.md](../docs/runbooks/rollback-execution.md)
- `promote-to-next-ring.ps1` - Evaluates gates and promotes per [ring-model.md](../docs/architecture/ring-model.md)
- `detect-drift.ps1` - Reconciliation loop per [control-plane-design.md](../docs/architecture/control-plane-design.md)

**Technology**: PowerShell, Bash, Azure Monitor queries, Log Analytics KQL

---

### 6. Utilities Scripts (`utilities/`)

**Purpose**: Common functions for correlation IDs, audit events, retries, validation.

**Key Scripts**:
- `Get-CorrelationId.ps1` - Generates UUIDv4 correlation IDs
- `Invoke-RetryWithBackoff.ps1` - Exponential backoff retry logic per [connector-rules.md](../.agents/rules/08-connector-rules.md)
- `Test-EvidencePackCompleteness.ps1` - Validates evidence pack per [evidence-pack-rules.md](../.agents/rules/10-evidence-pack-rules.md)
- `Send-SIEMEvent.ps1` - Forwards structured logs to SIEM

**Technology**: PowerShell modules (reusable .psm1 files)

---

### 7. CLI Scripts (`cli/`)

**Purpose**: Control Plane CLI for operators (similar to `kubectl`, `az`, `aws`).

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

**Technology**: PowerShell Advanced Functions with parameter validation, tab completion

---

### 8. Maintenance Scripts (`maintenance/`)

**Purpose**: Scheduled tasks (nightly/weekly/monthly).

**Key Scripts**:
- `cleanup-old-artifacts.ps1` - Purges artifacts older than 90 days per retention policy
- `rotate-all-credentials.ps1` - Batch credential rotation (runs monthly)
- `archive-audit-logs.ps1` - Archives logs to cold storage per retention policy
- `update-risk-model-weights.ps1` - Quarterly risk model calibration

**Technology**: PowerShell, Azure Automation runbooks, scheduled tasks

---

### 9. Testing Scripts (`testing/`)

**Purpose**: Unit, integration, E2E tests for CI/CD pipelines.

**Key Scripts**:
- `Test-RiskScoreCalculation.Tests.ps1` - Pester tests for risk scoring
- `Test-IntuneConnector.Tests.ps1` - Integration tests for Intune connector idempotency
- `Test-Ring0ToRing1Promotion.Tests.ps1` - E2E test for promotion gates

**Technology**: Pester (PowerShell testing framework), Bash test frameworks (bats, shunit2)

---

## Naming Conventions

### PowerShell Scripts
- **Verb-Noun** pattern (e.g., `Get-CorrelationId.ps1`, `Invoke-RetryWithBackoff.ps1`)
- Approved verbs: `Get`, `Set`, `New`, `Remove`, `Invoke`, `Test`, `Submit`, `Publish`, `Query`

### Bash Scripts
- **kebab-case** (e.g., `sign-macos-package.sh`, `sync-apt-mirror.sh`)
- `.sh` extension for shell scripts

### Module Files
- **PascalCase** (e.g., `ControlPlaneAPI.psm1`, `ConnectorFactory.psm1`)
- `.psm1` extension for PowerShell modules

---

## Technology Stack Per Script Type

| Script Type | Primary Tech | Secondary Tech | Dependencies |
|---|---|---|---|
| Control Plane | PowerShell 7+ | Azure PowerShell | Az.* modules |
| Packaging (Windows) | PowerShell 7+ | signtool, MSBuild | Windows SDK |
| Packaging (macOS) | Bash | codesign, notarytool | Xcode CLI tools |
| Packaging (Linux) | Bash | dpkg-deb, rpmbuild | GPG, debhelper |
| SBOM | Bash/PowerShell | Syft, CycloneDX CLI | Docker (optional) |
| Scanning | Bash/PowerShell | Trivy, Grype, Snyk | Docker (optional) |
| Intune Connector | PowerShell 7+ | Microsoft.Graph SDK | Graph API access |
| Jamf Connector | Bash | curl, jq | Jamf Pro API access |
| SCCM Connector | PowerShell 5.1+ | ConfigMgr module | SCCM site access |
| Landscape Connector | Bash | landscape-api CLI | Landscape API token |
| Ansible Connector | Bash | ansible, awx CLI | AWX/Tower API |
| HA/DR | PowerShell 7+ | Azure CLI, Bicep | Azure subscription |
| SIEM | PowerShell 7+ | Az.Monitor, KQL | Log Analytics access |

---

## Configuration Management

### Environment Variables
```powershell
# .env or environment variables
CONTROL_PLANE_API_URL="https://api.control-plane.corp/v1"
AZURE_TENANT_ID="00000000-0000-0000-0000-000000000000"
INTUNE_CLIENT_ID="11111111-1111-1111-1111-111111111111"
KEY_VAULT_NAME="kv-control-plane-prod"
SIEM_WORKSPACE_ID="22222222-2222-2222-2222-222222222222"
```

### Configuration Files
```
scripts/config/
├── settings.json               # Global settings (API URLs, timeouts, retry counts)
├── risk-model-v1.0.json        # Risk model weights and thresholds
├── promotion-gates.json        # Success rate thresholds per ring
├── retention-policies.json     # Artifact, evidence pack, log retention
└── execution-planes.json       # Connector endpoints and credentials (refs to vault)
```

---

## Security Considerations

### Credential Storage
- ❌ **FORBIDDEN**: Hardcoded credentials in scripts
- ✅ **REQUIRED**: All credentials stored in Azure Key Vault
- ✅ **REQUIRED**: Scripts use Managed Identities or service principal certs
- ✅ **REQUIRED**: All vault access logged to SIEM

### Audit Logging
- ✅ **REQUIRED**: All scripts log to structured JSON with correlation IDs
- ✅ **REQUIRED**: Privileged operations (publish, rollback, CAB approval) log to SIEM
- ✅ **REQUIRED**: Break-glass script usage triggers immediate alert

### Input Validation
- ✅ **REQUIRED**: All user inputs validated (correlation IDs match UUID format, ring numbers 0-4, etc.)
- ✅ **REQUIRED**: Path traversal prevention (no `../` in file paths)
- ✅ **REQUIRED**: Command injection prevention (no string concatenation for shell commands)

---

## CI/CD Integration

### Pre-Commit Hooks
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
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test PowerShell Scripts
        run: |
          pwsh -Command "Invoke-Pester -Path scripts/testing/ -Output Detailed"
      - name: Test Bash Scripts
        run: |
          bash scripts/testing/integration/test-all.sh
```

---

## Documentation Requirements

### Per-Script Headers
```powershell
<#
.SYNOPSIS
    Publishes artifact to Intune via Graph API with idempotency.

.DESCRIPTION
    Implements the Intune connector publish operation per docs/modules/intune/connector-spec.md.
    Uses correlation_id as idempotent key. Handles Graph API throttling with exponential backoff.

.PARAMETER CorrelationId
    Deployment intent correlation ID (UUIDv4 format).

.PARAMETER ArtifactId
    Artifact ID from packaging factory.

.PARAMETER Ring
    Target ring (0-4).

.EXAMPLE
    .\publish-to-intune.ps1 -CorrelationId "dp-20260104-001" -ArtifactId "app-v2.4.1" -Ring 1

.NOTES
    Version: 1.0
    Author: Platform Engineering
    Related Docs: docs/modules/intune/connector-spec.md, .agents/rules/08-connector-rules.md
#>
```

### README per Folder
Each script subfolder should have a `README.md`:
- Purpose of scripts in folder
- Prerequisites (modules, credentials, access)
- Usage examples
- Related documentation links

---

## Next Steps

### Immediate
1. **Create folder structure**: `mkdir -p scripts/{control-plane,packaging-factory,connectors,...}`
2. **Create placeholder scripts**: Touch files with header comments
3. **Document dependencies**: List required PowerShell modules, CLI tools, APIs

### Short-Term
4. **Implement utilities first**: Common functions (correlation IDs, retry, validation)
5. **Implement CLI skeleton**: Basic commands (deploy, status, rollback)
6. **Implement one connector**: Intune connector as MVP

### Medium-Term
7. **Implement packaging factory scripts**: SBOM, scanning, signing
8. **Implement infrastructure scripts**: HA/DR, secrets, RBAC setup
9. **Implement testing suite**: Pester tests for all utilities and connectors
10. **CI/CD integration**: GitHub Actions or Azure Pipelines for script testing

---

## Related Documentation

- [Architecture Overview](../docs/architecture/architecture-overview.md)
- [Control Plane Design](../docs/architecture/control-plane-design.md)
- [Connector Rules](../.agents/rules/08-connector-rules.md)
- [Packaging Factory Rules](../.agents/rules/03-packaging-factory-rules.md)
- [Testing Quality Rules](../.agents/rules/11-testing-quality-rules.md)

---

**Scripts Folder Structure Proposal v1.0 — Pending Approval**
