# Phase 1: Foundation - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 2 weeks
**Dependencies**: None (foundational phase)

---

## Task Overview

Implement foundational utilities and configuration that ALL other phases depend on. This phase establishes the technical bedrock: correlation IDs, retry logic, idempotency checks, configuration management, evidence pack validation, logging, and SIEM integration.

**Success Criteria**:
- All 11 utility functions implemented with ≥90% test coverage
- 4 configuration files created with JSON schema validation
- Zero PSScriptAnalyzer errors
- All functions have comment-based help
- Integration tests pass end-to-end

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Thin Control Plane**: Scripts orchestrate only; never replace Intune/Jamf/SCCM
- ✅ **Separation of Duties**: No function bypasses RBAC checks
- ✅ **Deterministic**: No randomness except correlation IDs; all logic formula-based
- ✅ **Evidence-First**: All operations create audit events
- ✅ **Idempotent**: All functions safe to retry with same correlation ID

### Quality Standards
- ✅ **PSScriptAnalyzer**: ZERO errors, ZERO warnings (severity Error/Warning)
- ✅ **Pester Tests**: ≥90% code coverage per function
- ✅ **Comment-Based Help**: `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE` mandatory
- ✅ **Error Handling**: Try/catch with structured errors, never swallow exceptions
- ✅ **Input Validation**: `[ValidateNotNullOrEmpty()]`, `[ValidatePattern()]`, `[ValidateRange()]` on all parameters

### Security Requirements
- ✅ **No Hardcoded Secrets**: Use Azure Key Vault via `Get-AzKeyVaultSecret`
- ✅ **Least Privilege**: Service principal scopes validated via `Test-ScopeValidity`
- ✅ **Audit Trail**: Every function call logged with correlation ID
- ✅ **Encryption**: Secrets encrypted at rest (vault), in transit (HTTPS)

---

## Scope: Utilities (scripts/utilities/)

### 1. Common Utilities (scripts/utilities/common/)

#### Get-CorrelationId.ps1
```powershell
<#
.SYNOPSIS
    Generates a UUIDv4 correlation ID with optional prefix.
.DESCRIPTION
    Creates unique correlation IDs for idempotent operations. Prefix format: <prefix>-<uuid>.
.PARAMETER Prefix
    Optional prefix for the correlation ID (e.g., "deploy", "rollback").
.EXAMPLE
    Get-CorrelationId -Prefix "deploy"
    # Returns: deploy-3f4e9a2b-8c1d-4f6e-9b3a-7e5c8d2f1a4b
#>
function Get-CorrelationId {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [ValidatePattern('^[a-z0-9-]+$')]
        [string]$Prefix
    )
    # Implementation: New-Guid with optional prefix
}
```

**Pester Tests Required**:
- UUIDs are unique across 1000 calls
- Prefix validation rejects invalid characters
- Format matches `^[a-z0-9-]+-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`

---

#### Invoke-RetryWithBackoff.ps1
```powershell
<#
.SYNOPSIS
    Retries a script block with exponential backoff.
.DESCRIPTION
    Executes a script block up to MaxRetries times with exponential backoff (2^retry * BaseDelay).
.PARAMETER ScriptBlock
    The script block to execute.
.PARAMETER MaxRetries
    Maximum retry attempts (default: 3).
.PARAMETER BaseDelaySeconds
    Base delay in seconds (default: 2).
.PARAMETER RetryableExceptions
    Array of exception types to retry (default: @('System.Net.WebException', 'System.TimeoutException')).
.EXAMPLE
    Invoke-RetryWithBackoff -ScriptBlock { Invoke-RestMethod -Uri $uri } -MaxRetries 5
#>
function Invoke-RetryWithBackoff {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$ScriptBlock,

        [Parameter(Mandatory = $false)]
        [ValidateRange(1, 10)]
        [int]$MaxRetries = 3,

        [Parameter(Mandatory = $false)]
        [ValidateRange(1, 60)]
        [int]$BaseDelaySeconds = 2,

        [Parameter(Mandatory = $false)]
        [string[]]$RetryableExceptions = @('System.Net.WebException', 'System.TimeoutException')
    )
    # Implementation: Loop with Start-Sleep (2^retry * BaseDelay)
}
```

**Pester Tests Required**:
- Succeeds on first try if script block succeeds
- Retries exactly MaxRetries times on retryable exception
- Does NOT retry on non-retryable exception
- Backoff delay matches 2^retry formula (measure with `Measure-Command`)

---

#### Test-IdempotencyKey.ps1
```powershell
<#
.SYNOPSIS
    Checks if a correlation ID has already been processed.
.DESCRIPTION
    Queries Event Store for existing deployment with given correlation ID.
.PARAMETER CorrelationId
    The correlation ID to check.
.PARAMETER EventStoreUri
    URI of the Event Store API (default: from config).
.EXAMPLE
    Test-IdempotencyKey -CorrelationId "deploy-abc123"
    # Returns: $true if already processed, $false otherwise
#>
function Test-IdempotencyKey {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$CorrelationId,

        [Parameter(Mandatory = $false)]
        [string]$EventStoreUri = (Get-ConfigValue -Key "EventStoreUri")
    )
    # Implementation: GET /api/events?correlationId={id}
}
```

**Pester Tests Required**:
- Returns `$true` if event exists in mock Event Store
- Returns `$false` if event does not exist
- Throws error if Event Store unreachable (after retries)

---

### 2. Validation Utilities (scripts/utilities/validation/)

#### Get-ConfigValue.ps1
```powershell
<#
.SYNOPSIS
    Reads configuration value from settings.json with fallback.
.DESCRIPTION
    Reads config from scripts/config/settings.json, supports environment variable substitution.
.PARAMETER Key
    Configuration key (e.g., "EventStoreUri").
.PARAMETER DefaultValue
    Optional default value if key not found.
.EXAMPLE
    Get-ConfigValue -Key "VaultUri"
    # Returns: https://vault.example.com (from config)
#>
function Get-ConfigValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Key,

        [Parameter(Mandatory = $false)]
        [string]$DefaultValue
    )
    # Implementation: ConvertFrom-Json, replace ${ENV_VAR} patterns
}
```

**Pester Tests Required**:
- Reads value from settings.json
- Substitutes environment variables (e.g., `${VAULT_URI}`)
- Returns default value if key missing
- Throws error if settings.json missing and no default

---

#### Test-EvidencePackCompleteness.ps1
```powershell
<#
.SYNOPSIS
    Validates evidence pack against JSON schema.
.DESCRIPTION
    Ensures all required fields present per evidence-pack-schema.json.
.PARAMETER EvidencePack
    Hashtable or PSCustomObject representing evidence pack.
.EXAMPLE
    Test-EvidencePackCompleteness -EvidencePack $pack
    # Returns: $true if valid, throws ValidationException otherwise
#>
function Test-EvidencePackCompleteness {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNull()]
        [object]$EvidencePack
    )
    # Implementation: Load schema from scripts/config/evidence-pack-schema.json, validate
}
```

**Pester Tests Required**:
- Valid evidence pack passes
- Missing required field throws error with field name
- Invalid field type throws error

---

#### Test-ScopeValidity.ps1
```powershell
<#
.SYNOPSIS
    Validates service principal scope boundaries.
.DESCRIPTION
    Ensures service principal has only allowed scopes (e.g., Packaging SP cannot publish).
.PARAMETER PrincipalId
    Service principal object ID.
.PARAMETER RequiredScopes
    Array of required scopes (e.g., @("DeviceManagementApps.ReadWrite.All")).
.EXAMPLE
    Test-ScopeValidity -PrincipalId $spId -RequiredScopes @("DeviceManagementApps.ReadWrite.All")
#>
function Test-ScopeValidity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$PrincipalId,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string[]]$RequiredScopes
    )
    # Implementation: Get-AzADServicePrincipal, compare scopes
}
```

**Pester Tests Required**:
- Valid scopes pass
- Missing scope throws error
- Excessive scope throws error

---

#### Test-CABApproval.ps1
```powershell
<#
.SYNOPSIS
    Checks CAB approval status for deployment intent.
.DESCRIPTION
    Queries control plane API for CAB approval record.
.PARAMETER DeploymentIntentId
    Deployment intent ID.
.EXAMPLE
    Test-CABApproval -DeploymentIntentId "intent-123"
    # Returns: $true if approved, $false otherwise
#>
function Test-CABApproval {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$DeploymentIntentId
    )
    # Implementation: GET /api/cab-approvals/{id}
}
```

**Pester Tests Required**:
- Returns `$true` for approved intent
- Returns `$false` for pending/rejected intent
- Throws error if intent not found

---

#### Test-PromotionGates.ps1
```powershell
<#
.SYNOPSIS
    Evaluates ring promotion gates.
.DESCRIPTION
    Checks if current ring meets success rate thresholds from promotion-gates.json.
.PARAMETER Ring
    Current ring (Canary, Pilot, Department, Global).
.PARAMETER SuccessRate
    Current success rate (0-100).
.EXAMPLE
    Test-PromotionGates -Ring "Canary" -SuccessRate 99.5
    # Returns: $true if ≥98% (from promotion-gates.json)
#>
function Test-PromotionGates {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Lab", "Canary", "Pilot", "Department", "Global")]
        [string]$Ring,

        [Parameter(Mandatory = $true)]
        [ValidateRange(0, 100)]
        [double]$SuccessRate
    )
    # Implementation: Load promotion-gates.json, compare
}
```

**Pester Tests Required**:
- Returns `$true` if success rate meets threshold
- Returns `$false` if below threshold
- Throws error if ring not in config

---

### 3. Logging Utilities (scripts/utilities/logging/)

#### Write-StructuredLog.ps1
```powershell
<#
.SYNOPSIS
    Writes structured JSON logs to console, file, and optionally SIEM.
.DESCRIPTION
    Creates JSON log entries with timestamp, level, correlation ID, message, and metadata.
.PARAMETER Level
    Log level (Debug, Info, Warning, Error, Critical).
.PARAMETER Message
    Log message.
.PARAMETER CorrelationId
    Correlation ID for this operation.
.PARAMETER Metadata
    Optional hashtable of additional fields.
.EXAMPLE
    Write-StructuredLog -Level "Info" -Message "Deployment started" -CorrelationId $cid -Metadata @{Ring="Canary"}
#>
function Write-StructuredLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Debug", "Info", "Warning", "Error", "Critical")]
        [string]$Level,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Message,

        [Parameter(Mandatory = $false)]
        [string]$CorrelationId,

        [Parameter(Mandatory = $false)]
        [hashtable]$Metadata
    )
    # Implementation: ConvertTo-Json, Write-Host (color-coded), append to log file
}
```

**Pester Tests Required**:
- JSON output valid and parseable
- Log file created if not exists
- Console output color matches level (Error=Red, Warning=Yellow, etc.)

---

#### Send-SIEMEvent.ps1
```powershell
<#
.SYNOPSIS
    Forwards structured event to Azure Sentinel.
.DESCRIPTION
    Sends JSON event to Log Analytics workspace via Data Collector API.
.PARAMETER Event
    Hashtable representing the event.
.PARAMETER LogType
    Log Analytics table name (default: "DeploymentEvents").
.EXAMPLE
    Send-SIEMEvent -Event @{Action="Deploy"; Status="Success"} -LogType "DeploymentEvents"
#>
function Send-SIEMEvent {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNull()]
        [hashtable]$Event,

        [Parameter(Mandatory = $false)]
        [string]$LogType = "DeploymentEvents"
    )
    # Implementation: POST to Log Analytics Data Collector API
}
```

**Pester Tests Required**:
- Mock HTTP call to Data Collector API
- Verify JSON body matches event
- Verify authorization header present

---

#### Export-AuditTrail.ps1
```powershell
<#
.SYNOPSIS
    Exports audit trail for correlation ID.
.DESCRIPTION
    Queries Event Store for all events matching correlation ID, exports to JSON/CSV.
.PARAMETER CorrelationId
    Correlation ID to export.
.PARAMETER OutputPath
    Output file path.
.PARAMETER Format
    Export format (JSON or CSV, default: JSON).
.EXAMPLE
    Export-AuditTrail -CorrelationId "deploy-123" -OutputPath "audit.json" -Format "JSON"
#>
function Export-AuditTrail {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$CorrelationId,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$OutputPath,

        [Parameter(Mandatory = $false)]
        [ValidateSet("JSON", "CSV")]
        [string]$Format = "JSON"
    )
    # Implementation: GET /api/events?correlationId={id}, export
}
```

**Pester Tests Required**:
- JSON export valid and parseable
- CSV export has headers and rows
- Throws error if no events found

---

## Scope: Configuration (scripts/config/)

### 1. settings.json
```json
{
  "VaultUri": "${AZURE_VAULT_URI}",
  "EventStoreUri": "${EVENT_STORE_URI}",
  "SIEMWorkspaceId": "${SIEM_WORKSPACE_ID}",
  "SIEMWorkspaceKey": "${SIEM_WORKSPACE_KEY}",
  "ControlPlaneApiUri": "${CONTROL_PLANE_API_URI}",
  "DefaultRetryCount": 3,
  "DefaultRetryDelaySeconds": 2,
  "LogFilePath": "${LOG_FILE_PATH}",
  "LogLevel": "Info"
}
```

**Validation**:
- All environment variables documented in README
- JSON schema provided (`settings-schema.json`)

---

### 2. risk-model-v1.0.json
```json
{
  "version": "1.0",
  "factors": [
    {
      "name": "Privilege Elevation",
      "weight": 0.25,
      "rubric": {
        "0": "No privilege change",
        "50": "Requests admin during install",
        "100": "Runs as SYSTEM/root always"
      }
    },
    {
      "name": "Blast Radius",
      "weight": 0.20,
      "rubric": {
        "0": "<100 devices",
        "50": "100-1000 devices",
        "100": ">10,000 devices"
      }
    }
    // ... 6 more factors per risk-model.md
  ],
  "threshold": 50
}
```

**Validation**:
- Sum of weights = 1.0
- All 8 factors from risk-model.md present

---

### 3. promotion-gates.json
```json
{
  "Lab": {
    "successRateThreshold": 100.0,
    "minDwellTimeHours": 24
  },
  "Canary": {
    "successRateThreshold": 98.0,
    "minDwellTimeHours": 48
  },
  "Pilot": {
    "successRateThreshold": 95.0,
    "minDwellTimeHours": 72
  },
  "Department": {
    "successRateThreshold": 95.0,
    "minDwellTimeHours": 168
  },
  "Global": {
    "successRateThreshold": 95.0,
    "minDwellTimeHours": 0
  }
}
```

**Validation**:
- All 5 rings present
- Thresholds match ring-model.md

---

### 4. evidence-pack-schema.json
Copy from [docs/architecture/evidence-pack-schema.md](../../architecture/evidence-pack-schema.md), extracting JSON schema block.

---

## Quality Checklist

### Per Function
- [ ] PSScriptAnalyzer passes with ZERO errors/warnings
- [ ] Pester tests ≥90% coverage
- [ ] Comment-based help complete (`.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER`, `.EXAMPLE`)
- [ ] Input validation on all parameters
- [ ] Try/catch with structured errors
- [ ] Correlation ID logged in all operations
- [ ] No hardcoded secrets (vault-only)

### Per Configuration File
- [ ] JSON valid (passes `Test-Json` or `ConvertFrom-Json`)
- [ ] JSON schema provided
- [ ] All environment variables documented
- [ ] Values match corresponding documentation (risk-model.md, ring-model.md, etc.)

### Integration Tests
- [ ] End-to-end test: Generate correlation ID → Validate evidence pack → Log to SIEM → Export audit trail
- [ ] Retry logic tested with network failures (mock `Invoke-RestMethod` to fail N times)
- [ ] Config loading tested with missing environment variables (should throw clear error)

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. PSScriptAnalyzer reports ANY error or warning (severity Error/Warning)
2. Pester test coverage falls below 90% for any function
3. Any function contains hardcoded credentials or secrets
4. Any function bypasses RBAC checks or SoD enforcement
5. Any function directly manages endpoints (must use execution planes only)

**Escalate to human if**:
- Azure Key Vault access failing (vault URI incorrect?)
- Event Store API unreachable (firewall/network issue?)
- SIEM integration failing (workspace ID/key incorrect?)

---

## Delivery Checklist

- [ ] All 11 functions implemented in `scripts/utilities/`
- [ ] All 4 config files created in `scripts/config/`
- [ ] PSScriptAnalyzer report: 0 errors, 0 warnings
- [ ] Pester test report: ≥90% coverage per function
- [ ] Integration test passes end-to-end
- [ ] README.md created with setup instructions (environment variables, Azure prerequisites)
- [ ] All functions cross-referenced in CLAUDE.md and relevant agent rules

---

## Related Documentation

- [.agents/rules/01-getting-started.md](../../.agents/rules/01-getting-started.md)
- [.agents/rules/11-testing-quality-rules.md](../../.agents/rules/11-testing-quality-rules.md)
- [docs/architecture/control-plane-design.md](../../architecture/control-plane-design.md)
- [docs/architecture/evidence-pack-schema.md](../../architecture/evidence-pack-schema.md)
- [docs/architecture/risk-model.md](../../architecture/risk-model.md)
- [docs/architecture/ring-model.md](../../architecture/ring-model.md)
- [docs/infrastructure/secrets-management.md](../../infrastructure/secrets-management.md)
- [docs/infrastructure/siem-integration.md](../../infrastructure/siem-integration.md)

---

**End of Phase 1 Prompt**
