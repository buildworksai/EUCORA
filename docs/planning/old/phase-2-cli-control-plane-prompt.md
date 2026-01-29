# Phase 2: CLI & Control Plane - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 3 weeks
**Dependencies**: Phase 1 (Foundation utilities)

---

## Task Overview

Implement the command-line interface (CLI) tool and core control plane components. The CLI provides the primary interface for Platform Admins, Packaging Engineers, and Publishers to interact with the system. Control plane scripts orchestrate policy enforcement, risk assessment, and deployment orchestration.

**Success Criteria**:
- CLI tool (`dapctl`) functional with all 12 commands
- 6 control plane components implemented (API Gateway, Policy Engine, Orchestrator, CAB Workflow, Evidence Store, Event Store)
- All operations auditable with correlation IDs
- Risk scoring deterministic and matches risk-model.md
- CAB workflow enforces approval gates
- ≥90% test coverage across all components

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Thin Control Plane**: Components define policy, orchestrate, record evidence ONLY
- ✅ **No Direct Endpoint Management**: All device operations delegated to execution planes
- ✅ **Deterministic Risk Scoring**: Formula-based, no AI/ML decisions
- ✅ **Evidence-First**: All decisions backed by immutable evidence packs
- ✅ **Separation of Duties**: CLI enforces RBAC, Publishers cannot approve own deployments

### Quality Standards
- ✅ **PSScriptAnalyzer**: ZERO errors, ZERO warnings
- ✅ **Pester Tests**: ≥90% coverage per component
- ✅ **API Validation**: All REST endpoints match OpenAPI specs exactly
- ✅ **Idempotency**: All operations safe to retry with same correlation ID
- ✅ **Error Handling**: Structured errors with exit codes per .agents/rules/08-connector-rules.md

### Security Requirements
- ✅ **Authentication**: All API calls require Entra ID bearer token
- ✅ **Authorization**: RBAC enforced via `Test-ScopeValidity` from Phase 1
- ✅ **Audit Trail**: Every operation logged to Event Store with correlation ID
- ✅ **Secrets**: No credentials in code, Azure Key Vault only

---

## Scope: CLI Tool (scripts/cli/)

### CLI Architecture
- **Entry Point**: `dapctl.ps1` (main dispatcher)
- **Commands**: Separate module per command in `scripts/cli/commands/`
- **Shared Modules**: `scripts/cli/modules/` (auth, formatting, error handling)

### Command Structure Template
```powershell
<#
.SYNOPSIS
    <Command description>
.DESCRIPTION
    <Detailed description>
.PARAMETER <ParamName>
    <Parameter description>
.EXAMPLE
    dapctl <command> <args>
#>
```

---

### 1. dapctl.ps1 (Main Entry Point)

```powershell
<#
.SYNOPSIS
    Desktop Application Packaging & Deployment Factory CLI.
.DESCRIPTION
    Command-line interface for managing deployments across Intune, Jamf, SCCM, Landscape, Ansible.
.PARAMETER Command
    Command to execute (deploy, status, rollback, etc.).
.EXAMPLE
    dapctl deploy --app "Notepad++" --ring "Canary" --correlation-id "deploy-123"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("deploy", "status", "rollback", "approve", "risk-score", "evidence", "logs", "config", "rings", "connectors", "test-connection", "version")]
    [string]$Command,

    [Parameter(Mandatory = $false, ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# Load shared modules
. "$PSScriptRoot/modules/Initialize-Auth.ps1"
. "$PSScriptRoot/modules/Format-Output.ps1"
. "$PSScriptRoot/modules/Write-ErrorMessage.ps1"

# Authenticate
$token = Initialize-Auth

# Dispatch to command module
$commandScript = "$PSScriptRoot/commands/Invoke-$Command.ps1"
if (Test-Path $commandScript) {
    & $commandScript @Arguments -AuthToken $token
} else {
    Write-ErrorMessage "Unknown command: $Command"
    exit 1
}
```

**Pester Tests Required**:
- Unknown command returns exit code 1
- Valid command dispatches to correct module
- Missing auth token fails gracefully

---

### 2. CLI Commands (scripts/cli/commands/)

#### Invoke-Deploy.ps1
```powershell
<#
.SYNOPSIS
    Submit deployment intent.
.DESCRIPTION
    Creates deployment intent, validates evidence pack, calculates risk score, routes to CAB if high-risk.
.PARAMETER AppName
    Application name.
.PARAMETER Version
    Application version.
.PARAMETER Ring
    Target ring (Lab, Canary, Pilot, Department, Global).
.PARAMETER CorrelationId
    Optional correlation ID (generated if not provided).
.PARAMETER EvidencePackPath
    Path to evidence pack JSON file.
.EXAMPLE
    dapctl deploy --app "Notepad++" --version "8.5.1" --ring "Canary" --evidence "./evidence.json"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AppName,

    [Parameter(Mandatory = $true)]
    [string]$Version,

    [Parameter(Mandatory = $true)]
    [ValidateSet("Lab", "Canary", "Pilot", "Department", "Global")]
    [string]$Ring,

    [Parameter(Mandatory = $false)]
    [string]$CorrelationId = (Get-CorrelationId -Prefix "deploy"),

    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path $_ })]
    [string]$EvidencePackPath,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

# 1. Load and validate evidence pack
$evidencePack = Get-Content $EvidencePackPath | ConvertFrom-Json
Test-EvidencePackCompleteness -EvidencePack $evidencePack

# 2. Check idempotency
if (Test-IdempotencyKey -CorrelationId $CorrelationId) {
    Write-Host "Deployment with correlation ID $CorrelationId already processed."
    exit 0
}

# 3. Calculate risk score
$riskScore = Invoke-RiskAssessment -EvidencePack $evidencePack

# 4. Create deployment intent
$intent = @{
    correlationId = $CorrelationId
    appName = $AppName
    version = $Version
    ring = $Ring
    riskScore = $riskScore
    evidencePack = $evidencePack
}

# 5. Submit to control plane
$response = Invoke-RestMethod -Uri "$($global:Config.ControlPlaneApiUri)/api/deployment-intents" `
    -Method POST -Body ($intent | ConvertTo-Json -Depth 10) `
    -Headers @{ Authorization = "Bearer $AuthToken" } `
    -ContentType "application/json"

# 6. Route to CAB if high-risk
if ($riskScore -gt 50) {
    Write-Host "High-risk deployment (score: $riskScore). Submitting to CAB for approval..."
    Invoke-CABSubmission -DeploymentIntentId $response.id -AuthToken $AuthToken
} else {
    Write-Host "Low-risk deployment (score: $riskScore). Auto-approved."
}

Write-Host "Deployment intent created: $($response.id)"
Write-StructuredLog -Level "Info" -Message "Deployment intent created" -CorrelationId $CorrelationId -Metadata @{IntentId = $response.id; RiskScore = $riskScore}
```

**Pester Tests Required**:
- Valid evidence pack creates intent
- Idempotent key prevents duplicate submission
- High-risk (>50) routes to CAB
- Low-risk auto-approves
- Invalid evidence pack throws validation error

---

#### Invoke-Status.ps1
```powershell
<#
.SYNOPSIS
    Check deployment status.
.DESCRIPTION
    Queries deployment intent status by correlation ID or intent ID.
.PARAMETER CorrelationId
    Correlation ID of deployment.
.PARAMETER IntentId
    Intent ID (alternative to correlation ID).
.EXAMPLE
    dapctl status --correlation-id "deploy-123"
#>
param(
    [Parameter(Mandatory = $false)]
    [string]$CorrelationId,

    [Parameter(Mandatory = $false)]
    [string]$IntentId,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

if (-not $CorrelationId -and -not $IntentId) {
    throw "Either CorrelationId or IntentId required"
}

$queryParam = if ($CorrelationId) { "correlationId=$CorrelationId" } else { "id=$IntentId" }
$response = Invoke-RestMethod -Uri "$($global:Config.ControlPlaneApiUri)/api/deployment-intents?$queryParam" `
    -Method GET -Headers @{ Authorization = "Bearer $AuthToken" }

Format-Output -Data $response -Format "Table"
```

**Pester Tests Required**:
- Query by correlation ID returns intent
- Query by intent ID returns intent
- Missing both parameters throws error
- Unknown ID returns 404

---

#### Invoke-Rollback.ps1
```powershell
<#
.SYNOPSIS
    Rollback deployment.
.DESCRIPTION
    Creates rollback intent, validates CAB approval, executes via execution planes.
.PARAMETER CorrelationId
    Correlation ID of deployment to rollback.
.PARAMETER Reason
    Rollback reason.
.EXAMPLE
    dapctl rollback --correlation-id "deploy-123" --reason "Critical bug found"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$CorrelationId,

    [Parameter(Mandatory = $true)]
    [string]$Reason,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

# 1. Generate rollback correlation ID
$rollbackCid = Get-CorrelationId -Prefix "rollback"

# 2. Create rollback intent
$intent = @{
    correlationId = $rollbackCid
    originalDeploymentCorrelationId = $CorrelationId
    reason = $Reason
}

$response = Invoke-RestMethod -Uri "$($global:Config.ControlPlaneApiUri)/api/rollback-intents" `
    -Method POST -Body ($intent | ConvertTo-Json) `
    -Headers @{ Authorization = "Bearer $AuthToken" } `
    -ContentType "application/json"

Write-Host "Rollback initiated: $($response.id)"
Write-StructuredLog -Level "Warning" -Message "Rollback initiated" -CorrelationId $rollbackCid -Metadata @{OriginalCid = $CorrelationId; Reason = $Reason}
```

**Pester Tests Required**:
- Valid rollback creates intent
- Rollback correlation ID has "rollback" prefix
- Logs rollback reason

---

#### Invoke-Approve.ps1 (CAB Approver Only)
```powershell
<#
.SYNOPSIS
    Approve or reject CAB submission.
.DESCRIPTION
    Records CAB decision in CAB Workflow component.
.PARAMETER IntentId
    Deployment intent ID.
.PARAMETER Decision
    Approve or Reject.
.PARAMETER Comments
    Approval comments.
.EXAMPLE
    dapctl approve --intent-id "intent-123" --decision "Approve" --comments "Evidence complete"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$IntentId,

    [Parameter(Mandatory = $true)]
    [ValidateSet("Approve", "Reject")]
    [string]$Decision,

    [Parameter(Mandatory = $true)]
    [string]$Comments,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

# Validate user is CAB Approver (check Entra ID group membership)
# Implementation: Get-AzADUserMemberOf, check for CAB Approvers group

$approval = @{
    intentId = $IntentId
    decision = $Decision
    comments = $Comments
    approver = $env:USERNAME
    timestamp = (Get-Date -Format "o")
}

$response = Invoke-RestMethod -Uri "$($global:Config.ControlPlaneApiUri)/api/cab-approvals" `
    -Method POST -Body ($approval | ConvertTo-Json) `
    -Headers @{ Authorization = "Bearer $AuthToken" } `
    -ContentType "application/json"

Write-Host "CAB decision recorded: $Decision"
Write-StructuredLog -Level "Info" -Message "CAB decision recorded" -Metadata @{IntentId = $IntentId; Decision = $Decision}
```

**Pester Tests Required**:
- Approve decision creates approval record
- Reject decision creates rejection record
- Non-CAB user throws authorization error

---

#### Invoke-RiskScore.ps1
```powershell
<#
.SYNOPSIS
    Calculate risk score for evidence pack.
.DESCRIPTION
    Evaluates evidence pack against risk-model-v1.0.json.
.PARAMETER EvidencePackPath
    Path to evidence pack JSON.
.EXAMPLE
    dapctl risk-score --evidence "./evidence.json"
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ Test-Path $_ })]
    [string]$EvidencePackPath,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

$evidencePack = Get-Content $EvidencePackPath | ConvertFrom-Json
$riskScore = Invoke-RiskAssessment -EvidencePack $evidencePack

Write-Host "Risk Score: $riskScore"
if ($riskScore -gt 50) {
    Write-Host "HIGH RISK - CAB approval required"
} else {
    Write-Host "LOW RISK - Auto-approved"
}
```

**Pester Tests Required**:
- High-risk evidence pack returns score >50
- Low-risk evidence pack returns score ≤50
- Invalid evidence pack throws error

---

#### Invoke-Evidence.ps1
```powershell
<#
.SYNOPSIS
    Retrieve evidence pack for deployment.
.DESCRIPTION
    Queries Evidence Store by correlation ID.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    dapctl evidence --correlation-id "deploy-123"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$CorrelationId,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

$response = Invoke-RestMethod -Uri "$($global:Config.ControlPlaneApiUri)/api/evidence-packs?correlationId=$CorrelationId" `
    -Method GET -Headers @{ Authorization = "Bearer $AuthToken" }

Format-Output -Data $response -Format "JSON"
```

**Pester Tests Required**:
- Returns evidence pack for valid correlation ID
- Returns 404 for unknown correlation ID

---

#### Invoke-Logs.ps1
```powershell
<#
.SYNOPSIS
    Export audit trail for correlation ID.
.DESCRIPTION
    Calls Export-AuditTrail from Phase 1.
.PARAMETER CorrelationId
    Correlation ID.
.PARAMETER OutputPath
    Output file path.
.PARAMETER Format
    JSON or CSV.
.EXAMPLE
    dapctl logs --correlation-id "deploy-123" --output "audit.json" --format "JSON"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$CorrelationId,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [Parameter(Mandatory = $false)]
    [ValidateSet("JSON", "CSV")]
    [string]$Format = "JSON",

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

Export-AuditTrail -CorrelationId $CorrelationId -OutputPath $OutputPath -Format $Format
Write-Host "Audit trail exported to $OutputPath"
```

**Pester Tests Required**:
- JSON export creates valid file
- CSV export creates valid file
- Unknown correlation ID throws error

---

#### Invoke-Config.ps1
```powershell
<#
.SYNOPSIS
    Display or update configuration.
.DESCRIPTION
    Reads/writes settings.json.
.PARAMETER Key
    Config key to read.
.PARAMETER Value
    Config value to set.
.EXAMPLE
    dapctl config --key "VaultUri"
    dapctl config --key "LogLevel" --value "Debug"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Key,

    [Parameter(Mandatory = $false)]
    [string]$Value,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

if ($Value) {
    # Set config value
    Set-ConfigValue -Key $Key -Value $Value
    Write-Host "Configuration updated: $Key = $Value"
} else {
    # Get config value
    $configValue = Get-ConfigValue -Key $Key
    Write-Host "$Key = $configValue"
}
```

**Pester Tests Required**:
- Get returns value
- Set updates settings.json
- Invalid key throws error

---

#### Invoke-Rings.ps1
```powershell
<#
.SYNOPSIS
    List ring definitions and promotion gates.
.DESCRIPTION
    Displays promotion-gates.json.
.EXAMPLE
    dapctl rings
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

$gates = Get-Content "$PSScriptRoot/../../config/promotion-gates.json" | ConvertFrom-Json
Format-Output -Data $gates -Format "Table"
```

**Pester Tests Required**:
- Displays all 5 rings
- Shows success rate thresholds

---

#### Invoke-Connectors.ps1
```powershell
<#
.SYNOPSIS
    List configured connectors and test connectivity.
.DESCRIPTION
    Displays connector status (Intune, Jamf, SCCM, Landscape, Ansible).
.EXAMPLE
    dapctl connectors
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

$connectors = @("Intune", "Jamf", "SCCM", "Landscape", "Ansible")
$status = @()

foreach ($connector in $connectors) {
    $testScript = "$PSScriptRoot/../../connectors/$($connector.ToLower())/Test-Connection.ps1"
    if (Test-Path $testScript) {
        $result = & $testScript -AuthToken $AuthToken
        $status += @{ Connector = $connector; Status = $result }
    } else {
        $status += @{ Connector = $connector; Status = "Not Configured" }
    }
}

Format-Output -Data $status -Format "Table"
```

**Pester Tests Required**:
- Lists all 5 connectors
- Shows connectivity status

---

#### Invoke-TestConnection.ps1
```powershell
<#
.SYNOPSIS
    Test connectivity to control plane and connectors.
.DESCRIPTION
    Validates API reachability, authentication, RBAC.
.EXAMPLE
    dapctl test-connection
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

# Test control plane API
try {
    $response = Invoke-RestMethod -Uri "$($global:Config.ControlPlaneApiUri)/health" `
        -Method GET -Headers @{ Authorization = "Bearer $AuthToken" }
    Write-Host "✓ Control Plane API: $($response.status)"
} catch {
    Write-Host "✗ Control Plane API: Unreachable"
}

# Test connectors (delegate to Invoke-Connectors)
& "$PSScriptRoot/Invoke-Connectors.ps1" -AuthToken $AuthToken
```

**Pester Tests Required**:
- Control plane reachable shows checkmark
- Control plane unreachable shows X

---

#### Invoke-Version.ps1
```powershell
<#
.SYNOPSIS
    Display CLI version.
.EXAMPLE
    dapctl version
#>
param(
    [Parameter(Mandatory = $false)]
    [string]$AuthToken
)

Write-Host "dapctl version 1.0.0"
Write-Host "Control Plane API: $($global:Config.ControlPlaneApiUri)"
```

**Pester Tests Required**:
- Displays version number

---

### 3. Shared Modules (scripts/cli/modules/)

#### Initialize-Auth.ps1
```powershell
<#
.SYNOPSIS
    Authenticate to Entra ID and obtain bearer token.
.DESCRIPTION
    Uses Azure CLI or Entra ID SDK to obtain token for Microsoft Graph API.
.EXAMPLE
    $token = Initialize-Auth
#>
function Initialize-Auth {
    [CmdletBinding()]
    param()

    # Use Azure CLI for simplicity: az account get-access-token --resource https://graph.microsoft.com
    $tokenJson = az account get-access-token --resource "https://graph.microsoft.com" | ConvertFrom-Json
    return $tokenJson.accessToken
}
```

**Pester Tests Required**:
- Returns valid JWT token
- Throws error if not logged in to Azure CLI

---

#### Format-Output.ps1
```powershell
<#
.SYNOPSIS
    Format output as Table, JSON, or CSV.
.PARAMETER Data
    Data to format.
.PARAMETER Format
    Output format (Table, JSON, CSV).
.EXAMPLE
    Format-Output -Data $response -Format "Table"
#>
function Format-Output {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Data,

        [Parameter(Mandatory = $false)]
        [ValidateSet("Table", "JSON", "CSV")]
        [string]$Format = "Table"
    )

    switch ($Format) {
        "Table" { $Data | Format-Table -AutoSize }
        "JSON" { $Data | ConvertTo-Json -Depth 10 }
        "CSV" { $Data | ConvertTo-Csv -NoTypeInformation }
    }
}
```

**Pester Tests Required**:
- Table format displays columns
- JSON format valid
- CSV format valid

---

#### Write-ErrorMessage.ps1
```powershell
<#
.SYNOPSIS
    Write structured error message to console.
.PARAMETER Message
    Error message.
.EXAMPLE
    Write-ErrorMessage "Deployment failed"
#>
function Write-ErrorMessage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "ERROR: $Message" -ForegroundColor Red
    Write-StructuredLog -Level "Error" -Message $Message
}
```

**Pester Tests Required**:
- Error message displayed in red
- Logged to structured log

---

## Scope: Control Plane Components (scripts/control-plane/)

### 1. API Gateway (scripts/control-plane/api-gateway/)

**Purpose**: REST API entry point, authentication, rate limiting, routing.

#### Start-ApiGateway.ps1
```powershell
<#
.SYNOPSIS
    Start API Gateway HTTP listener.
.DESCRIPTION
    Hosts REST API endpoints defined in control-plane-api.yaml.
.PARAMETER Port
    HTTP port (default: 8080).
.EXAMPLE
    Start-ApiGateway -Port 8080
#>
param(
    [Parameter(Mandatory = $false)]
    [int]$Port = 8080
)

# Implementation: Use Pode (PowerShell web framework) or .NET HttpListener
# Route /api/deployment-intents to Policy Engine
# Route /api/cab-approvals to CAB Workflow
# Route /api/evidence-packs to Evidence Store
# Route /api/events to Event Store
```

**Pester Tests Required**:
- GET /health returns 200
- POST /api/deployment-intents without auth returns 401
- POST /api/deployment-intents with valid auth returns 201

---

### 2. Policy Engine (scripts/control-plane/policy-engine/)

#### Invoke-PolicyEvaluation.ps1
```powershell
<#
.SYNOPSIS
    Evaluate deployment intent against policies.
.DESCRIPTION
    Validates ring eligibility, RBAC, promotion gates.
.PARAMETER DeploymentIntent
    Deployment intent object.
.EXAMPLE
    Invoke-PolicyEvaluation -DeploymentIntent $intent
#>
param(
    [Parameter(Mandatory = $true)]
    [hashtable]$DeploymentIntent
)

# 1. Validate RBAC: Is user authorized for this ring?
# 2. Validate promotion gates: Does previous ring meet success rate?
# 3. Validate CAB approval: If high-risk, is CAB approval present?
# 4. Return policy decision: Approve or Reject
```

**Pester Tests Required**:
- Valid intent passes policy
- Missing CAB approval for high-risk rejects
- User not in RBAC group rejects

---

### 3. Orchestrator (scripts/control-plane/orchestrator/)

#### Invoke-DeploymentOrchestration.ps1
```powershell
<#
.SYNOPSIS
    Orchestrate deployment across execution planes.
.DESCRIPTION
    Routes deployment to appropriate connectors (Intune, Jamf, SCCM, etc.).
.PARAMETER DeploymentIntent
    Deployment intent object.
.EXAMPLE
    Invoke-DeploymentOrchestration -DeploymentIntent $intent
#>
param(
    [Parameter(Mandatory = $true)]
    [hashtable]$DeploymentIntent
)

# 1. Determine target platform (Windows, macOS, Linux, Mobile)
# 2. Select connector (Intune for Windows online, SCCM for Windows offline, Jamf for macOS, etc.)
# 3. Call connector's Publish function
# 4. Record result in Event Store
```

**Pester Tests Required**:
- Windows online routes to Intune
- Windows offline routes to SCCM
- macOS routes to Jamf
- Linux routes to Landscape/Ansible

---

### 4. CAB Workflow (scripts/control-plane/cab-workflow/)

#### Invoke-CABSubmission.ps1
```powershell
<#
.SYNOPSIS
    Submit deployment intent to CAB for approval.
.DESCRIPTION
    Creates CAB submission record, notifies CAB Approvers.
.PARAMETER DeploymentIntentId
    Deployment intent ID.
.EXAMPLE
    Invoke-CABSubmission -DeploymentIntentId "intent-123"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$DeploymentIntentId,

    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)

# 1. Create CAB submission record
# 2. Send notification email to CAB Approvers group
# 3. Return submission ID
```

**Pester Tests Required**:
- Creates submission record
- Sends email notification (mock)

---

#### Get-CABApprovalStatus.ps1
```powershell
<#
.SYNOPSIS
    Check CAB approval status.
.PARAMETER DeploymentIntentId
    Deployment intent ID.
.EXAMPLE
    Get-CABApprovalStatus -DeploymentIntentId "intent-123"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$DeploymentIntentId
)

# Query CAB approvals table for intent ID
# Return: Approved, Rejected, Pending
```

**Pester Tests Required**:
- Approved intent returns "Approved"
- Pending intent returns "Pending"
- Rejected intent returns "Rejected"

---

### 5. Evidence Store (scripts/control-plane/evidence-store/)

#### Save-EvidencePack.ps1
```powershell
<#
.SYNOPSIS
    Save evidence pack to immutable store.
.DESCRIPTION
    Stores evidence pack in Azure Blob Storage (WORM policy).
.PARAMETER EvidencePack
    Evidence pack object.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Save-EvidencePack -EvidencePack $pack -CorrelationId "deploy-123"
#>
param(
    [Parameter(Mandatory = $true)]
    [hashtable]$EvidencePack,

    [Parameter(Mandatory = $true)]
    [string]$CorrelationId
)

# 1. Convert to JSON
# 2. Upload to Azure Blob Storage with WORM policy
# 3. Return blob URI
```

**Pester Tests Required**:
- Evidence pack saved to blob storage (mock)
- Blob URI returned

---

#### Get-EvidencePack.ps1
```powershell
<#
.SYNOPSIS
    Retrieve evidence pack by correlation ID.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Get-EvidencePack -CorrelationId "deploy-123"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$CorrelationId
)

# Query blob storage for evidence pack
# Return JSON object
```

**Pester Tests Required**:
- Returns evidence pack for valid correlation ID
- Throws error for unknown correlation ID

---

### 6. Event Store (scripts/control-plane/event-store/)

#### Write-Event.ps1
```powershell
<#
.SYNOPSIS
    Write event to immutable event store.
.DESCRIPTION
    Appends event to Azure Table Storage or SQL Database.
.PARAMETER Event
    Event object (correlation ID, timestamp, action, status, metadata).
.EXAMPLE
    Write-Event -Event @{CorrelationId="deploy-123"; Action="Deploy"; Status="Success"}
#>
param(
    [Parameter(Mandatory = $true)]
    [hashtable]$Event
)

# 1. Add timestamp if not present
# 2. Insert into Azure Table Storage or SQL Database
# 3. Return event ID
```

**Pester Tests Required**:
- Event written to store (mock)
- Event ID returned

---

#### Get-Events.ps1
```powershell
<#
.SYNOPSIS
    Query events by correlation ID.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Get-Events -CorrelationId "deploy-123"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$CorrelationId
)

# Query event store for correlation ID
# Return array of events
```

**Pester Tests Required**:
- Returns events for valid correlation ID
- Returns empty array for unknown correlation ID

---

### 7. Risk Assessment (scripts/control-plane/risk-assessment/)

#### Invoke-RiskAssessment.ps1
```powershell
<#
.SYNOPSIS
    Calculate risk score for evidence pack.
.DESCRIPTION
    Evaluates evidence pack against risk-model-v1.0.json, returns score 0-100.
.PARAMETER EvidencePack
    Evidence pack object.
.EXAMPLE
    $score = Invoke-RiskAssessment -EvidencePack $pack
#>
param(
    [Parameter(Mandatory = $true)]
    [hashtable]$EvidencePack
)

# 1. Load risk-model-v1.0.json
# 2. For each factor:
#    - Extract value from evidence pack
#    - Normalize to 0-100
#    - Multiply by weight
# 3. Sum weighted factors
# 4. Clamp to 0-100
# 5. Return score
```

**Pester Tests Required**:
- High-privilege app returns score >50
- Low-privilege app returns score ≤50
- Score matches manual calculation
- Missing factor throws error

---

## Quality Checklist

### Per Component
- [ ] PSScriptAnalyzer ZERO errors/warnings
- [ ] Pester tests ≥90% coverage
- [ ] Comment-based help complete
- [ ] API endpoints match OpenAPI spec exactly
- [ ] All operations idempotent
- [ ] All operations logged to Event Store
- [ ] No hardcoded credentials

### Integration Tests
- [ ] End-to-end: CLI deploy → Policy evaluation → Orchestration → Connector publish → Event logged
- [ ] CAB workflow: High-risk intent → CAB submission → Approval → Deployment proceeds
- [ ] Rollback: CLI rollback → Orchestration → Connector rollback → Event logged

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. Any component bypasses RBAC or SoD enforcement
2. Any component directly manages endpoints (must delegate to connectors)
3. Risk scoring produces non-deterministic results
4. Any API endpoint missing authentication check
5. Any operation not logged to Event Store

**Escalate to human if**:
- Entra ID authentication failing
- Azure Blob Storage WORM policy not configured
- Event Store writes failing

---

## Delivery Checklist

- [ ] CLI tool (`dapctl.ps1`) functional with all 12 commands
- [ ] 6 control plane components implemented
- [ ] PSScriptAnalyzer: 0 errors, 0 warnings
- [ ] Pester tests: ≥90% coverage
- [ ] Integration tests pass
- [ ] API endpoints match OpenAPI specs
- [ ] README with CLI usage examples

---

## Related Documentation

- [docs/api/control-plane-api.yaml](../../api/control-plane-api.yaml)
- [docs/api/deployment-intent-api.yaml](../../api/deployment-intent-api.yaml)
- [docs/api/risk-assessment-api.yaml](../../api/risk-assessment-api.yaml)
- [docs/architecture/control-plane-design.md](../../architecture/control-plane-design.md)
- [docs/architecture/risk-model.md](../../architecture/risk-model.md)
- [docs/architecture/cab-workflow.md](../../architecture/cab-workflow.md)
- [.agents/rules/02-control-plane-rules.md](../../.agents/rules/02-control-plane-rules.md)
- [.agents/rules/04-risk-scoring-rules.md](../../.agents/rules/04-risk-scoring-rules.md)
- [.agents/rules/05-cab-approval-rules.md](../../.agents/rules/05-cab-approval-rules.md)

---

**End of Phase 2 Prompt**
