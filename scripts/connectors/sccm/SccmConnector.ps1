# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    SCCM connector implementation for legacy/offline Windows.
.DESCRIPTION
    Uses SCCM AdminService REST API to publish packages, target collections, and report deployment status.
    Supports Windows Integrated Authentication (Kerberos/NTLM) for service account.
.NOTES
Version: 2.0
Author: Platform Engineering
Related Docs: docs/modules/sccm/connector-spec.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/ConnectorBase.ps1"

function Get-SccmAuthHeaders {
    <#
    .SYNOPSIS
        Get authentication headers for SCCM AdminService.
    .DESCRIPTION
        Uses Windows Integrated Authentication (current user context or service account).
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $headers = Get-SccmAuthHeaders -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # SCCM AdminService uses Windows Integrated Auth (Kerberos/NTLM)
    # No explicit token needed - uses current user context
    $headers = @{
        'Content-Type' = 'application/json'
        'X-Correlation-ID' = $CorrelationId
    }

    return $headers
}

function New-SccmApplication {
    <#
    .SYNOPSIS
        Create SCCM application.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $app = New-SccmApplication -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'sccm'
    $appUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_Application"

    # Build application payload
    $appPayload = @{
        LocalizedDisplayName = $DeploymentIntent.AppName
        LocalizedDescription = $DeploymentIntent.Description
        SoftwareVersion = $DeploymentIntent.Version
        Publisher = $DeploymentIntent.Publisher
        IsHidden = $false
        IsDeployed = $false
        IsSuperseded = $false
        IsSuperseding = $false
        IsEnabled = $true
        HasContent = $true
        LocalizedCategoryInstanceNames = @("EUCORA Deployments")
        SDMPackageXML = ""  # Will be populated by deployment type
    }

    $headers = Get-SccmAuthHeaders -CorrelationId $CorrelationId

    # Use -UseDefaultCredentials for Windows Integrated Auth
    try {
        $response = Invoke-RestMethod -Uri $appUri -Method 'POST' -Body ($appPayload | ConvertTo-Json -Depth 10) -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        Write-StructuredLog -Level 'Info' -Message 'SCCM application created' -CorrelationId $CorrelationId -Metadata @{
            app_name = $DeploymentIntent.AppName
            model_name = $response.ModelName
        }

        return $response
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "SCCM application creation failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        throw
    }
}

function New-SccmDeploymentType {
    <#
    .SYNOPSIS
        Create deployment type for SCCM application.
    .PARAMETER ApplicationModelName
        SCCM application model name (unique identifier).
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $dt = New-SccmDeploymentType -ApplicationModelName $modelName -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationModelName,

        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'sccm'
    $dtUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_DeploymentType"

    # Build deployment type payload (MSI or Script installer)
    $dtPayload = @{
        ApplicationName = $ApplicationModelName
        LocalizedDisplayName = "$($DeploymentIntent.AppName) - Deployment Type"
        Technology = "Script"  # or "MSI" for MSI installers
        InstallCommandLine = $DeploymentIntent.InstallCommand
        UninstallCommandLine = $DeploymentIntent.UninstallCommand
        ExecutionContext = if ($DeploymentIntent.RequiresAdmin) { "System" } else { "User" }
        RequiresUserInteraction = $false
        InstallationBehaviorType = "InstallForSystem"
        LogonRequirementType = "WhetherOrNotUserLoggedOn"
        MaxExecuteTime = 120  # minutes
        EstimatedInstallationTimeMinutes = 30
        RebootBehavior = "BasedOnExitCode"
    }

    $headers = Get-SccmAuthHeaders -CorrelationId $CorrelationId

    try {
        $response = Invoke-RestMethod -Uri $dtUri -Method 'POST' -Body ($dtPayload | ConvertTo-Json -Depth 10) -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        Write-StructuredLog -Level 'Info' -Message 'SCCM deployment type created' -CorrelationId $CorrelationId -Metadata @{
            app_name = $DeploymentIntent.AppName
            deployment_type = $response.LocalizedDisplayName
        }

        return $response
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "SCCM deployment type creation failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        throw
    }
}

function New-SccmDeployment {
    <#
    .SYNOPSIS
        Create SCCM deployment to collection.
    .PARAMETER ApplicationName
        SCCM application name.
    .PARAMETER CollectionId
        SCCM collection ID.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $deployment = New-SccmDeployment -ApplicationName $appName -CollectionId $collId -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationName,

        [Parameter(Mandatory = $true)]
        [string]$CollectionId,

        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'sccm'
    $deploymentUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_ApplicationAssignment"

    # Build deployment payload
    $deploymentPayload = @{
        ApplicationName = $ApplicationName
        AssignmentName = "$($DeploymentIntent.AppName) - $($DeploymentIntent.Ring)"
        CollectionName = $CollectionId
        DesiredConfigType = 1  # Required (1 = Required, 2 = Available)
        EnforcementDeadline = (Get-Date).AddHours(24).ToString("yyyyMMddHHmmss.000000+***")
        OfferTypeID = 0  # Required
        OverrideServiceWindows = $false
        RebootOutsideOfServiceWindows = $false
        UseGMTTimes = $false
        WoLEnabled = $false
        StartTime = (Get-Date).ToString("yyyyMMddHHmmss.000000+***")
        SuppressReboot = 0
        NotifyUser = $false
    }

    $headers = Get-SccmAuthHeaders -CorrelationId $CorrelationId

    try {
        $response = Invoke-RestMethod -Uri $deploymentUri -Method 'POST' -Body ($deploymentPayload | ConvertTo-Json -Depth 10) -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        Write-StructuredLog -Level 'Info' -Message 'SCCM deployment created' -CorrelationId $CorrelationId -Metadata @{
            app_name = $DeploymentIntent.AppName
            collection_id = $CollectionId
            assignment_id = $response.AssignmentID
        }

        return $response
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "SCCM deployment creation failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        throw
    }
}

function Publish-SccmApplication {
    <#
    .SYNOPSIS
        Publish application to SCCM.
    .DESCRIPTION
        Creates application, deployment type, and deployment to collection.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Publish-SccmApplication -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'sccm'

    # Check if connector is configured
    if (-not $config.api_url -or -not $config.site_code) {
        Write-StructuredLog -Level 'Warning' -Message 'SCCM connector missing configuration, returning stub response' -CorrelationId $CorrelationId -Metadata @{ connector = 'sccm' }
        return @{
            status = 'stubbed'
            correlation_id = $CorrelationId
            intent = $DeploymentIntent
        }
    }

    # Create application
    $app = New-SccmApplication -DeploymentIntent $DeploymentIntent -CorrelationId $CorrelationId

    # Create deployment type
    $deploymentType = New-SccmDeploymentType -ApplicationModelName $app.ModelName -DeploymentIntent $DeploymentIntent -CorrelationId $CorrelationId

    # Get collection ID for ring
    $collectionId = Get-SccmCollectionId -Ring $DeploymentIntent.Ring -Config $config

    # Create deployment
    $deployment = New-SccmDeployment -ApplicationName $app.LocalizedDisplayName -CollectionId $collectionId -DeploymentIntent $DeploymentIntent -CorrelationId $CorrelationId

    return @{
        status = 'published'
        correlation_id = $CorrelationId
        app_model_name = $app.ModelName
        app_name = $app.LocalizedDisplayName
        deployment_id = $deployment.AssignmentID
        collection_id = $collectionId
        connector = 'sccm'
    }
}

function Remove-SccmApplication {
    <#
    .SYNOPSIS
        Remove application from SCCM.
    .PARAMETER ApplicationId
        SCCM application model name.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Remove-SccmApplication -ApplicationId $modelName -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'sccm'
    $deleteUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_Application(ModelName='$ApplicationId')"

    $headers = Get-SccmAuthHeaders -CorrelationId $CorrelationId

    try {
        Invoke-RestMethod -Uri $deleteUri -Method 'DELETE' -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        Write-StructuredLog -Level 'Warning' -Message 'SCCM application removed' -CorrelationId $CorrelationId -Metadata @{
            app_model_name = $ApplicationId
        }

        return @{
            status = 'removed'
            correlation_id = $CorrelationId
            app_model_name = $ApplicationId
            connector = 'sccm'
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "SCCM application removal failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        throw
    }
}

function Get-SccmDeploymentStatus {
    <#
    .SYNOPSIS
        Query deployment status for correlation ID.
    .DESCRIPTION
        Queries deployment asset details for install status.
    .PARAMETER CorrelationId
        Correlation ID to search for.
    .EXAMPLE
        $status = Get-SccmDeploymentStatus -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'sccm'

    # Search for deployments with correlation ID in assignment name
    $searchUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_ApplicationAssignment?`$filter=contains(AssignmentName,'$CorrelationId')"
    $headers = Get-SccmAuthHeaders -CorrelationId $CorrelationId

    try {
        $response = Invoke-RestMethod -Uri $searchUri -Method 'GET' -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        if ($response.value.Count -eq 0) {
            return @{
                status = 'not_found'
                correlation_id = $CorrelationId
                connector = 'sccm'
            }
        }

        $assignment = $response.value[0]
        $assignmentId = $assignment.AssignmentID

        # Get deployment asset details
        $statusUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_AppDeploymentAssetDetails?`$filter=AssignmentID eq $assignmentId"
        $statusResponse = Invoke-RestMethod -Uri $statusUri -Method 'GET' -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        $assetDetails = $statusResponse.value
        $successCount = ($assetDetails | Where-Object { $_.ComplianceState -eq 1 }).Count  # 1 = Compliant (Installed)
        $failureCount = ($assetDetails | Where-Object { $_.ComplianceState -eq 2 }).Count  # 2 = Error
        $pendingCount = ($assetDetails | Where-Object { $_.ComplianceState -in @(0, 3) }).Count  # 0 = Unknown, 3 = In Progress

        return @{
            status = 'queried'
            correlation_id = $CorrelationId
            assignment_id = $assignmentId
            assignment_name = $assignment.AssignmentName
            success_count = $successCount
            failure_count = $failureCount
            pending_count = $pendingCount
            total_devices = $assetDetails.Count
            success_rate = if ($assetDetails.Count -gt 0) { ($successCount / $assetDetails.Count) * 100 } else { 0 }
            connector = 'sccm'
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "SCCM deployment status query failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        throw
    }
}

function Test-SccmConnection {
    <#
    .SYNOPSIS
        Test connectivity to SCCM AdminService.
    .PARAMETER AuthToken
        Not used (Windows Integrated Auth).
    .EXAMPLE
        $result = Test-SccmConnection -AuthToken 'dummy'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    $config = Get-ConnectorConfig -Name 'sccm'
    $testCid = Get-CorrelationId -Prefix 'test'

    try {
        # Test AdminService connectivity
        $testUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_Site"
        $headers = Get-SccmAuthHeaders -CorrelationId $testCid

        $response = Invoke-RestMethod -Uri $testUri -Method 'GET' -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        Write-StructuredLog -Level 'Info' -Message 'SCCM connector test successful' -CorrelationId $testCid

        return @{
            connector = 'SCCM'
            status = 'healthy'
            checked_at = (Get-Date).ToString('o')
            site_code = $config.site_code
            site_count = $response.value.Count
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "SCCM connector test failed: $($_.Exception.Message)" -CorrelationId $testCid

        return @{
            connector = 'SCCM'
            status = 'unhealthy'
            error = $_.Exception.Message
            checked_at = (Get-Date).ToString('o')
        }
    }
}

function Get-SccmTargetDevices {
    <#
    .SYNOPSIS
        Get target devices for ring-based deployment.
    .DESCRIPTION
        Queries collection membership for ring-specific collection.
    .PARAMETER Ring
        Target ring (Lab, Canary, Pilot, Department, Global).
    .EXAMPLE
        $devices = Get-SccmTargetDevices -Ring 'Canary'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Lab', 'Canary', 'Pilot', 'Department', 'Global')]
        [string]$Ring
    )

    $config = Get-ConnectorConfig -Name 'sccm'
    $testCid = Get-CorrelationId -Prefix 'devices'

    try {
        # Get collection ID
        $collectionId = Get-SccmCollectionId -Ring $Ring -Config $config
        if (-not $collectionId) {
            Write-StructuredLog -Level 'Warning' -Message "No collection ID configured for ring $Ring" -CorrelationId $testCid
            return @()
        }

        # Query collection members
        $membersUri = "$($config.api_url.TrimEnd('/'))/wmi/SMS_FullCollectionMembership?`$filter=CollectionID eq '$collectionId'"
        $headers = Get-SccmAuthHeaders -CorrelationId $testCid

        $response = Invoke-RestMethod -Uri $membersUri -Method 'GET' -Headers $headers -UseDefaultCredentials -TimeoutSec 60

        $devices = $response.value | ForEach-Object {
            @{
                device_id = $_.ResourceID
                device_name = $_.Name
                ring = $Ring
                collection_id = $collectionId
                last_heartbeat = $_.LastHeartbeat
            }
        }

        Write-StructuredLog -Level 'Debug' -Message 'SCCM target devices retrieved' -CorrelationId $testCid -Metadata @{
            count = $devices.Count
            ring = $Ring
        }

        return $devices
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Failed to retrieve SCCM target devices: $($_.Exception.Message)" -CorrelationId $testCid
        return @()
    }
}

function Get-SccmCollectionId {
    <#
    .SYNOPSIS
        Get SCCM collection ID for ring.
    .PARAMETER Ring
        Target ring.
    .PARAMETER Config
        Connector configuration.
    .EXAMPLE
        $collectionId = Get-SccmCollectionId -Ring 'Canary' -Config $config
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring,

        [Parameter(Mandatory = $true)]
        [hashtable]$Config
    )

    $ringCollectionMap = @{
        'Lab' = $Config.collections.lab
        'Canary' = $Config.collections.canary
        'Pilot' = $Config.collections.pilot
        'Department' = $Config.collections.department
        'Global' = $Config.collections.global
    }

    return $ringCollectionMap[$Ring]
}
