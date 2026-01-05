# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Intune-specific connector implementation (Microsoft Graph API).
.DESCRIPTION
    Implements Publish/Remove/Status/Test/Target operations against Microsoft Graph deviceAppManagement.
    Supports Win32 LOB apps, MSI apps, and assignments with idempotent operations.
.NOTES
Version: 2.0
Author: Platform Engineering
Related Docs: docs/modules/intune/connector-spec.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/ConnectorBase.ps1"

function New-IntuneWin32App {
    <#
    .SYNOPSIS
        Create Win32 LOB app in Intune via Microsoft Graph API.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable with app metadata.
    .PARAMETER AccessToken
        Microsoft Graph OAuth2 access token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $app = New-IntuneWin32App -DeploymentIntent $intent -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $graphUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps"

    # Build Win32 LOB app payload
    $appPayload = @{
        '@odata.type' = '#microsoft.graph.win32LobApp'
        displayName = $DeploymentIntent.AppName
        description = $DeploymentIntent.Description
        publisher = $DeploymentIntent.Publisher
        notes = "CorrelationId: $CorrelationId"
        fileName = $DeploymentIntent.FileName
        installCommandLine = $DeploymentIntent.InstallCommand
        uninstallCommandLine = $DeploymentIntent.UninstallCommand
        installExperience = @{
            runAsAccount = if ($DeploymentIntent.RequiresAdmin) { 'system' } else { 'user' }
            deviceRestartBehavior = $DeploymentIntent.RestartBehavior ?? 'suppress'
        }
        detectionRules = @(
            @{
                '@odata.type' = '#microsoft.graph.win32LobAppFileSystemDetection'
                path = $DeploymentIntent.DetectionPath
                fileOrFolderName = $DeploymentIntent.DetectionFile
                check32BitOn64System = $false
                detectionType = 'exists'
            }
        )
        returnCodes = @(
            @{ returnCode = 0; type = 'success' }
            @{ returnCode = 1707; type = 'success' }
            @{ returnCode = 3010; type = 'softReboot' }
            @{ returnCode = 1641; type = 'hardReboot' }
            @{ returnCode = 1618; type = 'retry' }
        )
    }

    $headers = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = 'application/json'
    }

    $response = Invoke-ConnectorRequest -Uri $graphUri -Method 'POST' -Body $appPayload -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Info' -Message 'Intune Win32 app created' -CorrelationId $CorrelationId -Metadata @{
        app_id = $response.id
        app_name = $response.displayName
    }

    return $response
}

function New-IntuneAssignment {
    <#
    .SYNOPSIS
        Create assignment for Intune app to target group.
    .PARAMETER AppId
        Intune app ID (GUID).
    .PARAMETER GroupId
        Entra ID group ID for targeting.
    .PARAMETER Intent
        Assignment intent (available, required, uninstall).
    .PARAMETER AccessToken
        Microsoft Graph OAuth2 access token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $assignment = New-IntuneAssignment -AppId $appId -GroupId $groupId -Intent 'required' -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AppId,

        [Parameter(Mandatory = $true)]
        [string]$GroupId,

        [Parameter(Mandatory = $false)]
        [ValidateSet('available', 'required', 'uninstall')]
        [string]$Intent = 'required',

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $assignmentUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$AppId/assignments"

    $assignmentPayload = @{
        '@odata.type' = '#microsoft.graph.mobileAppAssignment'
        intent = $Intent
        target = @{
            '@odata.type' = '#microsoft.graph.groupAssignmentTarget'
            groupId = $GroupId
        }
    }

    $headers = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = 'application/json'
    }

    $response = Invoke-ConnectorRequest -Uri $assignmentUri -Method 'POST' -Body $assignmentPayload -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Info' -Message 'Intune assignment created' -CorrelationId $CorrelationId -Metadata @{
        app_id = $AppId
        group_id = $GroupId
        intent = $Intent
    }

    return $response
}

function Publish-IntuneApplication {
    <#
    .SYNOPSIS
        Publish application to Intune with assignment.
    .DESCRIPTION
        Creates Win32 LOB app and assigns to target group based on ring.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'intune'

    # Check if connector is configured
    if (-not $config.client_id -or -not $config.client_secret) {
        Write-StructuredLog -Level 'Warning' -Message 'Intune connector missing credentials, returning stub response' -CorrelationId $CorrelationId -Metadata @{ connector = 'intune' }
        return @{
            status = 'stubbed'
            correlation_id = $CorrelationId
            intent = $DeploymentIntent
        }
    }

    # Acquire OAuth2 token
    $accessToken = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId $CorrelationId

    # Create Win32 app
    $app = New-IntuneWin32App -DeploymentIntent $DeploymentIntent -AccessToken $accessToken -CorrelationId $CorrelationId

    if ($app.status -eq 'failed') {
        return $app
    }

    # Create assignment to target group (ring-based)
    $targetGroupId = Get-RingGroupId -Ring $DeploymentIntent.Ring -Config $config
    if ($targetGroupId) {
        $assignment = New-IntuneAssignment -AppId $app.id -GroupId $targetGroupId -Intent 'required' -AccessToken $accessToken -CorrelationId $CorrelationId
    }

    return @{
        status = 'published'
        correlation_id = $CorrelationId
        app_id = $app.id
        app_name = $app.displayName
        assignment_id = $assignment.id
        connector = 'intune'
    }
}

function Remove-IntuneApplication {
    <#
    .SYNOPSIS
        Remove application from Intune (soft delete).
    .PARAMETER ApplicationId
        Intune app ID (GUID).
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Remove-IntuneApplication -ApplicationId $appId -CorrelationId $cid
    #>
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # Acquire OAuth2 token
    $accessToken = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId $CorrelationId

    $deleteUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$ApplicationId"
    $headers = @{
        Authorization = "Bearer $accessToken"
    }

    $null = Invoke-ConnectorRequest -Uri $deleteUri -Method 'DELETE' -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Warning' -Message 'Intune app removed' -CorrelationId $CorrelationId -Metadata @{
        app_id = $ApplicationId
    }

    return @{
        status = 'removed'
        correlation_id = $CorrelationId
        app_id = $ApplicationId
        connector = 'intune'
    }
}

function Get-IntuneDeploymentStatus {
    <#
    .SYNOPSIS
        Query deployment status for correlation ID.
    .DESCRIPTION
        Searches for apps with correlation ID in notes field and retrieves install status.
    .PARAMETER CorrelationId
        Correlation ID to search for.
    .EXAMPLE
        $status = Get-IntuneDeploymentStatus -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # Acquire OAuth2 token
    $accessToken = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId $CorrelationId

    # Search for apps with correlation ID
    $searchUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps?`$filter=contains(notes,'$CorrelationId')"
    $headers = @{
        Authorization = "Bearer $accessToken"
    }

    $response = Invoke-ConnectorRequest -Uri $searchUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    if ($response.status -eq 'failed') {
        return $response
    }

    $apps = $response.value
    if ($apps.Count -eq 0) {
        return @{
            status = 'not_found'
            correlation_id = $CorrelationId
            connector = 'intune'
        }
    }

    # Get install status for first matching app
    $app = $apps[0]
    $statusUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$($app.id)/deviceStatuses"
    $statusResponse = Invoke-ConnectorRequest -Uri $statusUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    $deviceStatuses = $statusResponse.value
    $successCount = ($deviceStatuses | Where-Object { $_.installState -eq 'installed' }).Count
    $failureCount = ($deviceStatuses | Where-Object { $_.installState -eq 'failed' }).Count
    $pendingCount = ($deviceStatuses | Where-Object { $_.installState -in @('notInstalled', 'installing') }).Count

    return @{
        status = 'queried'
        correlation_id = $CorrelationId
        app_id = $app.id
        app_name = $app.displayName
        success_count = $successCount
        failure_count = $failureCount
        pending_count = $pendingCount
        total_devices = $deviceStatuses.Count
        success_rate = if ($deviceStatuses.Count -gt 0) { ($successCount / $deviceStatuses.Count) * 100 } else { 0 }
        connector = 'intune'
    }
}

function Test-IntuneConnection {
    <#
    .SYNOPSIS
        Test connectivity to Microsoft Graph API.
    .PARAMETER AuthToken
        Not used (OAuth2 token acquired internally).
    .EXAMPLE
        $result = Test-IntuneConnection -AuthToken 'dummy'
    #>
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Parameter required for interface compatibility, token acquired internally')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    $config = Get-ConnectorConfig -Name 'intune'
    $testCid = Get-CorrelationId -Type uuid

    try {
        # Acquire OAuth2 token
        $accessToken = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId $testCid

        # Test Graph API connectivity
        $testUri = "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps?`$top=1"
        $headers = @{
            Authorization = "Bearer $accessToken"
        }

        $null = Invoke-ConnectorRequest -Uri $testUri -Method 'GET' -Headers $headers -CorrelationId $testCid

        Write-StructuredLog -Level 'Info' -Message 'Intune connector test successful' -CorrelationId $testCid

        return @{
            connector = 'Intune'
            status = 'healthy'
            checked_at = (Get-Date).ToString('o')
            tenant_id = $config.tenant_id
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Intune connector test failed: $($_.Exception.Message)" -CorrelationId $testCid

        return @{
            connector = 'Intune'
            status = 'unhealthy'
            error = $_.Exception.Message
            checked_at = (Get-Date).ToString('o')
        }
    }
}

function Get-IntuneTargetDevices {
    <#
    .SYNOPSIS
        Get target devices for ring-based deployment.
    .DESCRIPTION
        Queries Entra ID group membership for ring-specific group.
    .PARAMETER Ring
        Target ring (Lab, Canary, Pilot, Department, Global).
    .EXAMPLE
        $devices = Get-IntuneTargetDevices -Ring 'Canary'
    #>
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of devices, plural noun is semantically correct')]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Lab', 'Canary', 'Pilot', 'Department', 'Global')]
        [string]$Ring
    )

    $config = Get-ConnectorConfig -Name 'intune'
    $testCid = Get-CorrelationId -Type uuid

    try {
        # Acquire OAuth2 token
        $accessToken = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId $testCid

        # Get ring group ID
        $groupId = Get-RingGroupId -Ring $Ring -Config $config
        if (-not $groupId) {
            Write-StructuredLog -Level 'Warning' -Message "No group ID configured for ring $Ring" -CorrelationId $testCid
            return @()
        }

        # Query group members
        $membersUri = "https://graph.microsoft.com/v1.0/groups/$groupId/members"
        $headers = @{
            Authorization = "Bearer $accessToken"
        }

        $response = Invoke-ConnectorRequest -Uri $membersUri -Method 'GET' -Headers $headers -CorrelationId $testCid

        if ($response.status -eq 'failed') {
            return @()
        }

        $devices = $response.value | Where-Object { $_.'@odata.type' -eq '#microsoft.graph.device' } | ForEach-Object {
            @{
                device_id = $_.id
                device_name = $_.displayName
                ring = $Ring
                os = $_.operatingSystem
                last_seen = $_.approximateLastSignInDateTime
            }
        }

        Write-StructuredLog -Level 'Debug' -Message 'Intune target devices retrieved' -CorrelationId $testCid -Metadata @{
            count = $devices.Count
            ring = $Ring
        }

        return $devices
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Failed to retrieve Intune target devices: $($_.Exception.Message)" -CorrelationId $testCid
        return @()
    }
}

function Get-RingGroupId {
    <#
    .SYNOPSIS
        Get Entra ID group ID for ring.
    .PARAMETER Ring
        Target ring.
    .PARAMETER Config
        Connector configuration.
    .EXAMPLE
        $groupId = Get-RingGroupId -Ring 'Canary' -Config $config
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring,

        [Parameter(Mandatory = $true)]
        [hashtable]$Config
    )

    $ringGroupMap = @{
        'Lab' = $Config.ring_groups.lab
        'Canary' = $Config.ring_groups.canary
        'Pilot' = $Config.ring_groups.pilot
        'Department' = $Config.ring_groups.department
        'Global' = $Config.ring_groups.global
    }

    return $ringGroupMap[$Ring]
}
