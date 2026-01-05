# Phase 3: Execution Plane Connectors - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 4 weeks
**Dependencies**: Phase 1 (Foundation), Phase 2 (Control Plane)

---

## Task Overview

Implement execution plane connectors for Intune, Jamf, SCCM, Landscape, and Ansible. These connectors are the ONLY components that interact with endpoint management systems. They translate deployment intents into platform-specific operations while maintaining idempotency, auditability, and error handling.

**Success Criteria**:
- All 5 connectors implemented with standardized interface
- Idempotency enforced via correlation IDs
- Error classification (Transient, Permanent, Unknown) per .agents/rules/08-connector-rules.md
- Throttling and pagination handled for all APIs
- ≥90% test coverage per connector
- Integration tests validate end-to-end deployment

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Execution Plane Only**: Connectors NEVER define policy, only execute intents
- ✅ **Thin Control Plane**: Control plane orchestrates, connectors execute
- ✅ **Idempotency**: Correlation IDs prevent duplicate operations
- ✅ **No Direct Endpoint Access**: Connectors use management APIs only (Intune Graph API, Jamf Pro API, SCCM REST, etc.)
- ✅ **Offline-First**: SCCM handles air-gapped Windows, APT mirrors for air-gapped Linux

### Quality Standards
- ✅ **PSScriptAnalyzer**: ZERO errors, ZERO warnings
- ✅ **Pester Tests**: ≥90% coverage per connector
- ✅ **Error Classification**: Transient (429, 503) vs Permanent (400, 404) vs Unknown (500)
- ✅ **Retry Logic**: Exponential backoff for transient errors only
- ✅ **Pagination**: Handle large device collections (>1000 devices)

### Security Requirements
- ✅ **Service Principals**: Scoped credentials per connector (Intune SP, Jamf SP, etc.)
- ✅ **Least Privilege**: Minimum required API permissions
- ✅ **Certificate Auth**: SCCM and Jamf use certificate-based auth
- ✅ **Audit Trail**: Every API call logged with correlation ID

---

## Connector Interface Standard

All connectors MUST implement this standard interface:

```powershell
# Publish-Application: Deploy application to target ring
function Publish-Application {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )
}

# Remove-Application: Rollback/uninstall application
function Remove-Application {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )
}

# Get-DeploymentStatus: Query deployment status
function Get-DeploymentStatus {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )
}

# Test-Connection: Validate API connectivity and authentication
function Test-Connection {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )
}

# Get-TargetDevices: Retrieve device list for ring
function Get-TargetDevices {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring
    )
}
```

---

## Scope: Intune Connector (scripts/connectors/intune/)

### Authentication
- **Method**: Microsoft Graph API with Entra ID service principal
- **Scopes**: `DeviceManagementApps.ReadWrite.All`, `DeviceManagementManagedDevices.Read.All`
- **Token**: OAuth 2.0 client credentials flow

### 1. Publish-IntuneApplication.ps1

```powershell
<#
.SYNOPSIS
    Publish application to Intune.
.DESCRIPTION
    Creates Win32App or MSI app in Intune, assigns to ring-specific Azure AD group.
.PARAMETER DeploymentIntent
    Deployment intent with app metadata, package URI, target ring.
.PARAMETER CorrelationId
    Correlation ID for idempotency.
.EXAMPLE
    Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId "deploy-123"
#>
function Publish-IntuneApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Check idempotency: Query existing apps by correlation ID (stored in app notes field)
    $existingApp = Get-IntuneAppByCorrelationId -CorrelationId $CorrelationId
    if ($existingApp) {
        Write-StructuredLog -Level "Info" -Message "App already published (idempotent)" -CorrelationId $CorrelationId
        return $existingApp
    }

    # 2. Create app payload
    $appPayload = @{
        "@odata.type" = "#microsoft.graph.win32LobApp"
        displayName = $DeploymentIntent.AppName
        description = $DeploymentIntent.Description
        publisher = $DeploymentIntent.Publisher
        notes = "CorrelationId: $CorrelationId"  # Store correlation ID for idempotency
        installCommandLine = $DeploymentIntent.InstallCommand
        uninstallCommandLine = $DeploymentIntent.UninstallCommand
        installExperience = @{
            runAsAccount = "system"
            deviceRestartBehavior = "allow"
        }
        detectionRules = @(
            @{
                "@odata.type" = "#microsoft.graph.win32LobAppFileSystemDetection"
                path = $DeploymentIntent.DetectionPath
                fileOrFolderName = $DeploymentIntent.DetectionFile
                check32BitOn64System = $false
                detectionType = "exists"
            }
        )
    }

    # 3. Upload to Intune with retry
    $app = Invoke-RetryWithBackoff -ScriptBlock {
        Invoke-MgGraphRequest -Method POST -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps" `
            -Body ($appPayload | ConvertTo-Json -Depth 10) -ContentType "application/json"
    } -MaxRetries 5

    # 4. Upload .intunewin package content
    $contentVersionUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$($app.id)/microsoft.graph.win32LobApp/contentVersions"
    $contentVersion = Invoke-MgGraphRequest -Method POST -Uri $contentVersionUri -Body "{}"

    $packageUploadUri = "$contentVersionUri/$($contentVersion.id)/files"
    $fileUpload = Invoke-MgGraphRequest -Method POST -Uri $packageUploadUri -Body (@{
        "@odata.type" = "#microsoft.graph.mobileAppContentFile"
        name = "$($DeploymentIntent.AppName).intunewin"
        size = (Get-Item $DeploymentIntent.PackagePath).Length
    } | ConvertTo-Json)

    # Upload to Azure Storage SAS URL (multi-part upload for large files)
    Invoke-IntuneContentUpload -SasUri $fileUpload.azureStorageUri -FilePath $DeploymentIntent.PackagePath

    # Commit content version
    Invoke-MgGraphRequest -Method POST -Uri "$contentVersionUri/$($contentVersion.id)/commit" `
        -Body (@{ fileEncryptionInfo = $DeploymentIntent.EncryptionInfo } | ConvertTo-Json)

    # 5. Assign to ring-specific Azure AD group
    $targetGroup = Get-IntuneRingGroup -Ring $DeploymentIntent.Ring
    $assignmentPayload = @{
        mobileAppAssignments = @(
    @{
        "@odata.type" = "#microsoft.graph.mobileAppAssignment"
        intent = "required"
        target = @{
            "@odata.type" = "#microsoft.graph.groupAssignmentTarget"
            groupId = $targetGroup.id
        }
    }

## Implementation Status & Next Steps

### Status snapshot

- **Expanded dapctl surface**: new scripts cover health, deploy, status, rollback, approve, risk-score, evidence, logs, config, rings, connectors, test-connection, and version paths while enforcing correlation‑id logging, connector stubs, and control-plane policies.
- **Connector stubs & risk model**: `scripts/cli/modules/ConnectorStubs.ps1` and `RiskModel.ps1` keep idempotent semantics, deterministic scoring, and synthetic status reporting until plane-specific connectors replace them.
- **Config-driven guardrails**: `Invoke-config`, `Invoke-rings`, and `Invoke-evidence` read JSON schemas under `scripts/config/`, enforce measurable thresholds, and surface metadata needed by the CAB evidence pack.
- **Regression coverage**: `scripts/cli/dapctl.Tests.ps1` now runs healthy commands through the dispatcher, validates `deploy`, `status`, and `test-connection`, and ensures helper modules remain available under strict mode.

### Next actions

1. Replace connector stubs with real Intune/Jamf/SCCM/Landscape/Ansible adapters (reuse the existing interface, reuse `Invoke-Dapctl` to exercise new implementations).
2. Extend tests to cover idempotency (reusing correlation ids), retry/backoff flows, error classification, and structured logging output once real connectors are in place.
3. Publish the Phase 2 infrastructure docs (HA/DR, secrets/key management, SIEM) so the connectors ecosystem shares the same governance language during board reviews.
        )
    }

    Invoke-MgGraphRequest -Method POST -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$($app.id)/assign" `
        -Body ($assignmentPayload | ConvertTo-Json -Depth 10)

    # 6. Log to Event Store
    Write-Event -Event @{
        CorrelationId = $CorrelationId
        Action = "Publish"
        Connector = "Intune"
        Status = "Success"
        AppId = $app.id
        Ring = $DeploymentIntent.Ring
    }

    Write-StructuredLog -Level "Info" -Message "App published to Intune" -CorrelationId $CorrelationId -Metadata @{AppId = $app.id}
    return $app
}
```

**Helper Functions**:
- `Get-IntuneAppByCorrelationId`: Search apps by correlation ID in notes field
- `Get-IntuneRingGroup`: Map ring name to Azure AD group ID
- `Invoke-IntuneContentUpload`: Multi-part upload to Azure Storage

**Pester Tests Required**:
- New app creates successfully
- Idempotent call returns existing app
- Transient error (429) retries with backoff
- Permanent error (400) throws without retry
- App assigned to correct ring group

---

### 2. Remove-IntuneApplication.ps1

```powershell
<#
.SYNOPSIS
    Remove application from Intune.
.DESCRIPTION
    Deletes app assignment (not the app itself, for auditability).
.PARAMETER ApplicationId
    Intune app ID.
.PARAMETER CorrelationId
    Correlation ID for rollback.
.EXAMPLE
    Remove-IntuneApplication -ApplicationId "app-123" -CorrelationId "rollback-456"
#>
function Remove-IntuneApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # Remove assignment (keep app for audit trail)
    $assignments = Invoke-MgGraphRequest -Method GET -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$ApplicationId/assignments"

    foreach ($assignment in $assignments.value) {
        Invoke-RetryWithBackoff -ScriptBlock {
            Invoke-MgGraphRequest -Method DELETE -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$ApplicationId/assignments/$($assignment.id)"
        }
    }

    Write-Event -Event @{
        CorrelationId = $CorrelationId
        Action = "Remove"
        Connector = "Intune"
        Status = "Success"
        AppId = $ApplicationId
    }

    Write-StructuredLog -Level "Info" -Message "App assignments removed from Intune" -CorrelationId $CorrelationId
}
```

**Pester Tests Required**:
- Assignments removed successfully
- Non-existent app throws 404
- Idempotent (removing twice succeeds)

---

### 3. Get-IntuneDeploymentStatus.ps1

```powershell
<#
.SYNOPSIS
    Query deployment status from Intune.
.DESCRIPTION
    Retrieves device installation status for app.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Get-IntuneDeploymentStatus -CorrelationId "deploy-123"
#>
function Get-IntuneDeploymentStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Find app by correlation ID
    $app = Get-IntuneAppByCorrelationId -CorrelationId $CorrelationId
    if (-not $app) {
        throw "App not found for correlation ID: $CorrelationId"
    }

    # 2. Query device installation status
    $statusUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$($app.id)/deviceStatuses"
    $statuses = Invoke-MgGraphRequest -Method GET -Uri $statusUri

    # 3. Aggregate: Success, Failed, Pending
    $summary = @{
        TotalDevices = $statuses.value.Count
        Success = ($statuses.value | Where-Object { $_.installState -eq "installed" }).Count
        Failed = ($statuses.value | Where-Object { $_.installState -eq "failed" }).Count
        Pending = ($statuses.value | Where-Object { $_.installState -eq "notInstalled" -or $_.installState -eq "installing" }).Count
        SuccessRate = 0
    }

    if ($summary.TotalDevices -gt 0) {
        $summary.SuccessRate = [math]::Round(($summary.Success / $summary.TotalDevices) * 100, 2)
    }

    return $summary
}
```

**Pester Tests Required**:
- Returns status for valid correlation ID
- Success rate calculated correctly
- Handles pagination (>1000 devices)

---

### 4. Test-IntuneConnection.ps1

```powershell
<#
.SYNOPSIS
    Test Intune API connectivity.
.EXAMPLE
    Test-IntuneConnection -AuthToken $token
#>
function Test-IntuneConnection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    try {
        $response = Invoke-MgGraphRequest -Method GET -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps?`$top=1"
        return @{ Status = "Connected"; AppCount = $response.'@odata.count' }
    } catch {
        return @{ Status = "Failed"; Error = $_.Exception.Message }
    }
}
```

**Pester Tests Required**:
- Valid token returns "Connected"
- Invalid token returns "Failed"

---

### 5. Get-IntuneTargetDevices.ps1

```powershell
<#
.SYNOPSIS
    Get devices for ring.
.PARAMETER Ring
    Ring name.
.EXAMPLE
    Get-IntuneTargetDevices -Ring "Canary"
#>
function Get-IntuneTargetDevices {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Lab", "Canary", "Pilot", "Department", "Global")]
        [string]$Ring
    )

    $group = Get-IntuneRingGroup -Ring $Ring
    $devicesUri = "https://graph.microsoft.com/v1.0/groups/$($group.id)/members"
    $devices = Invoke-MgGraphRequest -Method GET -Uri $devicesUri

    return $devices.value
}
```

**Pester Tests Required**:
- Returns devices for valid ring
- Unknown ring throws error

---

## Scope: Jamf Connector (scripts/connectors/jamf/)

### Authentication
- **Method**: Jamf Pro API with client certificate
- **Endpoint**: `https://jamf.example.com/api/v1`
- **Auth**: Bearer token from `/api/v1/auth/token`

### 1. Publish-JamfApplication.ps1

```powershell
<#
.SYNOPSIS
    Publish application to Jamf Pro.
.DESCRIPTION
    Creates macOS policy with package, assigns to ring-specific smart group.
.PARAMETER DeploymentIntent
    Deployment intent.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Publish-JamfApplication -DeploymentIntent $intent -CorrelationId "deploy-123"
#>
function Publish-JamfApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Check idempotency
    $existingPolicy = Get-JamfPolicyByCorrelationId -CorrelationId $CorrelationId
    if ($existingPolicy) {
        return $existingPolicy
    }

    # 2. Upload package to Jamf Distribution Point
    $package = Upload-JamfPackage -PackagePath $DeploymentIntent.PackagePath -PackageName "$($DeploymentIntent.AppName).pkg"

    # 3. Create policy
    $policyPayload = @{
        general = @{
            name = "$($DeploymentIntent.AppName) - $($DeploymentIntent.Ring)"
            enabled = $true
            category = @{ name = "Managed Applications" }
        }
        scope = @{
            computer_groups = @(
                @{ name = "Ring-$($DeploymentIntent.Ring)" }
            )
        }
        package_configuration = @{
            packages = @(
                @{
                    name = $package.name
                    action = "Install"
                }
            )
        }
        user_interaction = @{
            message_start = "Installing $($DeploymentIntent.AppName)..."
            allow_users_to_defer = $false
        }
    }

    $policy = Invoke-RestMethod -Uri "$jamfApiUri/api/v1/policies" -Method POST `
        -Body ($policyPayload | ConvertTo-Json -Depth 10) -Headers $jamfHeaders -Certificate $jamfCert

    # 4. Store correlation ID in policy notes
    Update-JamfPolicyNotes -PolicyId $policy.id -Notes "CorrelationId: $CorrelationId"

    # 5. Log event
    Write-Event -Event @{
        CorrelationId = $CorrelationId
        Action = "Publish"
        Connector = "Jamf"
        Status = "Success"
        PolicyId = $policy.id
        Ring = $DeploymentIntent.Ring
    }

    return $policy
}
```

**Helper Functions**:
- `Get-JamfPolicyByCorrelationId`: Search policies by correlation ID in notes
- `Upload-JamfPackage`: Upload PKG to Jamf Cloud Distribution Point
- `Update-JamfPolicyNotes`: Update policy notes field

**Pester Tests Required**:
- Policy created successfully
- Package uploaded to distribution point
- Idempotent call returns existing policy
- Policy scoped to correct ring group

---

### 2-5. Remove-JamfApplication.ps1, Get-JamfDeploymentStatus.ps1, Test-JamfConnection.ps1, Get-JamfTargetDevices.ps1

Similar structure to Intune connector, adapted for Jamf Pro API.

---

## Scope: SCCM Connector (scripts/connectors/sccm/)

### Authentication
- **Method**: SCCM AdminService REST API (Windows Authentication or certificate)
- **Endpoint**: `https://sccm.example.com/AdminService/wmi`
- **Offline Support**: Distribution Points for air-gapped sites

### 1. Publish-SCCMApplication.ps1

```powershell
<#
.SYNOPSIS
    Publish application to SCCM.
.DESCRIPTION
    Creates SCCM application, deployment type, distributes to DPs, deploys to ring collection.
.PARAMETER DeploymentIntent
    Deployment intent.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Publish-SCCMApplication -DeploymentIntent $intent -CorrelationId "deploy-123"
#>
function Publish-SCCMApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Check idempotency
    $existingApp = Get-SCCMAppByCorrelationId -CorrelationId $CorrelationId
    if ($existingApp) {
        return $existingApp
    }

    # 2. Create application
    $appParams = @{
        Name = "$($DeploymentIntent.AppName) v$($DeploymentIntent.Version)"
        Description = "CorrelationId: $CorrelationId"
        LocalizedDisplayName = $DeploymentIntent.AppName
        Publisher = $DeploymentIntent.Publisher
        SoftwareVersion = $DeploymentIntent.Version
    }

    $app = New-CMApplication @appParams

    # 3. Add deployment type (MSI or Script Installer)
    Add-CMDeploymentType -ApplicationName $app.LocalizedDisplayName `
        -InstallCommand $DeploymentIntent.InstallCommand `
        -UninstallCommand $DeploymentIntent.UninstallCommand `
        -DetectionClauseType File -Path $DeploymentIntent.DetectionPath -FileName $DeploymentIntent.DetectionFile

    # 4. Distribute content to DPs (critical for offline sites)
    $dpGroups = Get-CMDistributionPointGroup
    foreach ($dpGroup in $dpGroups) {
        Start-CMContentDistribution -ApplicationName $app.LocalizedDisplayName -DistributionPointGroupName $dpGroup.Name
    }

    # Wait for distribution (poll status)
    Wait-SCCMContentDistribution -ApplicationName $app.LocalizedDisplayName -TimeoutMinutes 30

    # 5. Deploy to ring collection
    $collection = Get-CMDeviceCollection -Name "Ring-$($DeploymentIntent.Ring)"
    New-CMApplicationDeployment -ApplicationName $app.LocalizedDisplayName `
        -CollectionName $collection.Name -DeployAction Install -DeployPurpose Required `
        -UserNotification DisplaySoftwareCenterOnly

    # 6. Log event
    Write-Event -Event @{
        CorrelationId = $CorrelationId
        Action = "Publish"
        Connector = "SCCM"
        Status = "Success"
        ApplicationId = $app.CI_ID
        Ring = $DeploymentIntent.Ring
    }

    return $app
}
```

**Helper Functions**:
- `Get-SCCMAppByCorrelationId`: Search apps by correlation ID in description
- `Wait-SCCMContentDistribution`: Poll distribution status until complete

**Pester Tests Required**:
- Application created successfully
- Content distributed to all DPs
- Deployment created for ring collection
- Idempotent call returns existing app

---

### 2-5. Remove-SCCMApplication.ps1, Get-SCCMDeploymentStatus.ps1, Test-SCCMConnection.ps1, Get-SCCMTargetDevices.ps1

Similar structure to Intune connector, adapted for SCCM ConfigMgr cmdlets.

---

## Scope: Landscape Connector (scripts/connectors/landscape/)

### Authentication
- **Method**: Landscape API with API key
- **Endpoint**: `https://landscape.canonical.com/api/v2`
- **Target**: Ubuntu devices

### 1. Publish-LandscapeApplication.ps1

```powershell
<#
.SYNOPSIS
    Publish package to Landscape.
.DESCRIPTION
    Creates repository pocket, uploads DEB package, assigns to ring computer group.
.PARAMETER DeploymentIntent
    Deployment intent.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Publish-LandscapeApplication -DeploymentIntent $intent -CorrelationId "deploy-123"
#>
function Publish-LandscapeApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Check idempotency
    $existingActivity = Get-LandscapeActivityByCorrelationId -CorrelationId $CorrelationId
    if ($existingActivity) {
        return $existingActivity
    }

    # 2. Upload package to repository pocket
    $pocketName = "$($DeploymentIntent.AppName)-$($DeploymentIntent.Version)"
    $pocket = New-LandscapePocket -Name $pocketName -Description "CorrelationId: $CorrelationId"

    Upload-LandscapePackage -PocketId $pocket.id -PackagePath $DeploymentIntent.PackagePath

    # 3. Create installation activity
    $computerGroup = Get-LandscapeComputerGroup -Name "Ring-$($DeploymentIntent.Ring)"
    $activity = New-LandscapeActivity -Type "InstallPackages" `
        -ComputerGroupId $computerGroup.id `
        -Packages @($DeploymentIntent.PackageName) `
        -Comment "CorrelationId: $CorrelationId"

    # 4. Log event
    Write-Event -Event @{
        CorrelationId = $CorrelationId
        Action = "Publish"
        Connector = "Landscape"
        Status = "Success"
        ActivityId = $activity.id
        Ring = $DeploymentIntent.Ring
    }

    return $activity
}
```

**Helper Functions**:
- `Get-LandscapeActivityByCorrelationId`: Search activities by comment field
- `New-LandscapePocket`: Create repository pocket for custom packages
- `Upload-LandscapePackage`: Upload DEB to pocket

**Pester Tests Required**:
- Pocket created successfully
- Package uploaded
- Activity created for ring group
- Idempotent call returns existing activity

---

### 2-5. Remove-LandscapeApplication.ps1, Get-LandscapeDeploymentStatus.ps1, Test-LandscapeConnection.ps1, Get-LandscapeTargetDevices.ps1

Similar structure to Intune connector, adapted for Landscape API.

---

## Scope: Ansible Connector (scripts/connectors/ansible/)

### Authentication
- **Method**: Ansible Tower/AWX REST API with token
- **Endpoint**: `https://awx.example.com/api/v2`
- **Target**: RHEL/CentOS devices

### 1. Publish-AnsibleApplication.ps1

```powershell
<#
.SYNOPSIS
    Publish package via Ansible playbook.
.DESCRIPTION
    Launches Ansible job template for package installation on ring inventory.
.PARAMETER DeploymentIntent
    Deployment intent.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Publish-AnsibleApplication -DeploymentIntent $intent -CorrelationId "deploy-123"
#>
function Publish-AnsibleApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # 1. Check idempotency
    $existingJob = Get-AnsibleJobByCorrelationId -CorrelationId $CorrelationId
    if ($existingJob) {
        return $existingJob
    }

    # 2. Launch job template
    $jobTemplate = Get-AnsibleJobTemplate -Name "Install-RPM-Package"
    $extraVars = @{
        package_name = $DeploymentIntent.PackageName
        package_url = $DeploymentIntent.PackageUri
        correlation_id = $CorrelationId
    }

    $inventory = Get-AnsibleInventory -Name "Ring-$($DeploymentIntent.Ring)"

    $job = Launch-AnsibleJob -JobTemplateId $jobTemplate.id -InventoryId $inventory.id `
        -ExtraVars ($extraVars | ConvertTo-Json)

    # 3. Log event
    Write-Event -Event @{
        CorrelationId = $CorrelationId
        Action = "Publish"
        Connector = "Ansible"
        Status = "Success"
        JobId = $job.id
        Ring = $DeploymentIntent.Ring
    }

    return $job
}
```

**Helper Functions**:
- `Get-AnsibleJobByCorrelationId`: Search jobs by extra_vars.correlation_id
- `Get-AnsibleJobTemplate`: Retrieve job template by name
- `Launch-AnsibleJob`: Launch job with inventory and vars

**Pester Tests Required**:
- Job launched successfully
- Extra vars include correlation ID
- Job targeted at correct ring inventory
- Idempotent call returns existing job

---

### 2-5. Remove-AnsibleApplication.ps1, Get-AnsibleDeploymentStatus.ps1, Test-AnsibleConnection.ps1, Get-AnsibleTargetDevices.ps1

Similar structure to Intune connector, adapted for Ansible Tower/AWX API.

---

## Error Classification & Retry Logic

Per [.agents/rules/08-connector-rules.md](../../.agents/rules/08-connector-rules.md):

```powershell
function Invoke-ConnectorApiCall {
    param(
        [scriptblock]$ApiCall,
        [string]$CorrelationId
    )

    try {
        $result = Invoke-RetryWithBackoff -ScriptBlock $ApiCall -RetryableExceptions @(
            'System.Net.WebException',  # Network issues
            'Throttled',                 # 429 Too Many Requests
            'ServiceUnavailable'         # 503 Service Unavailable
        )
        return $result
    } catch {
        $errorType = switch ($_.Exception.Response.StatusCode) {
            400 { "Permanent" }  # Bad Request
            401 { "Permanent" }  # Unauthorized
            403 { "Permanent" }  # Forbidden
            404 { "Permanent" }  # Not Found
            429 { "Transient" }  # Too Many Requests
            500 { "Unknown" }    # Internal Server Error
            503 { "Transient" }  # Service Unavailable
            default { "Unknown" }
        }

        Write-StructuredLog -Level "Error" -Message "Connector API call failed" `
            -CorrelationId $CorrelationId -Metadata @{
                ErrorType = $errorType
                StatusCode = $_.Exception.Response.StatusCode
                Message = $_.Exception.Message
            }

        throw
    }
}
```

---

## Quality Checklist

### Per Connector
- [ ] All 5 interface functions implemented
- [ ] Idempotency enforced via correlation IDs
- [ ] Error classification (Transient/Permanent/Unknown)
- [ ] Retry logic with exponential backoff
- [ ] Pagination handled (>1000 devices)
- [ ] PSScriptAnalyzer ZERO errors/warnings
- [ ] Pester tests ≥90% coverage
- [ ] All API calls logged to Event Store

### Integration Tests
- [ ] End-to-end: Control plane → Connector publish → Platform deployment
- [ ] Idempotency: Duplicate publish returns existing resource
- [ ] Rollback: Connector remove → Platform uninstall
- [ ] Status: Connector status → Accurate device counts

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. Any connector defines policy or approval logic (execution only)
2. Any connector directly accesses endpoints (must use management APIs)
3. Idempotency not enforced (duplicate operations execute)
4. Transient errors not retried (429, 503 fail permanently)
5. Permanent errors retried (400, 404 retry infinitely)

**Escalate to human if**:
- API authentication failing across all connectors
- Distribution Point synchronization failing (SCCM offline sites broken)
- Throttling limits too aggressive (need rate limit increase)

---

## Delivery Checklist

- [ ] All 5 connectors implemented (Intune, Jamf, SCCM, Landscape, Ansible)
- [ ] Standard interface implemented consistently
- [ ] Idempotency validated via integration tests
- [ ] Error handling tested with mock failures
- [ ] PSScriptAnalyzer: 0 errors, 0 warnings
- [ ] Pester tests: ≥90% coverage per connector
- [ ] README with API prerequisites per connector

---

## Related Documentation

- [docs/modules/intune/connector-spec.md](../../modules/intune/connector-spec.md)
- [docs/modules/jamf/connector-spec.md](../../modules/jamf/connector-spec.md)
- [docs/modules/sccm/connector-spec.md](../../modules/sccm/connector-spec.md)
- [docs/modules/landscape/connector-spec.md](../../modules/landscape/connector-spec.md)
- [docs/modules/ansible/connector-spec.md](../../modules/ansible/connector-spec.md)
- [docs/architecture/execution-plane-connectors.md](../../architecture/execution-plane-connectors.md)
- [.agents/rules/08-connector-rules.md](../../.agents/rules/08-connector-rules.md)

---

**End of Phase 3 Prompt**
