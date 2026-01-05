# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Landscape connector implementation for Ubuntu/Linux.
.DESCRIPTION
    Manages APT repository packages, system profiles, and compliance reporting through the Landscape API.
    Supports bearer token authentication.
.NOTES
Version: 2.0
Author: Platform Engineering
Related Docs: docs/modules/landscape/connector-spec.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/ConnectorBase.ps1"

function New-LandscapePackageProfile {
    <#
    .SYNOPSIS
        Create package profile in Landscape.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER AccessToken
        Landscape API bearer token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $profile = New-LandscapePackageProfile -DeploymentIntent $intent -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'landscape'
    $profileUri = "$($config.api_url.TrimEnd('/'))/api/v2/package-profiles"

    # Build package profile payload
    $profilePayload = @{
        title = "$($DeploymentIntent.AppName) - $($DeploymentIntent.Ring)"
        description = $DeploymentIntent.Description
        access_group = $config.account_name
        tags = @("eucora", $DeploymentIntent.Ring.ToLower(), "correlation:$CorrelationId")
        packages = @(
            @{
                name = $DeploymentIntent.PackageName
                version = $DeploymentIntent.Version
            }
        )
    }

    $headers = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = 'application/json'
    }

    $response = Invoke-ConnectorRequest -Uri $profileUri -Method 'POST' -Body $profilePayload -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Info' -Message 'Landscape package profile created' -CorrelationId $CorrelationId -Metadata @{
        profile_id = $response.id
        profile_title = $response.title
    }

    return $response
}

function New-LandscapeActivity {
    <#
    .SYNOPSIS
        Create activity to apply package profile to computers.
    .PARAMETER ProfileId
        Landscape package profile ID.
    .PARAMETER ComputerQuery
        Computer query (tag-based or all).
    .PARAMETER AccessToken
        Landscape API bearer token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $activity = New-LandscapeActivity -ProfileId 123 -ComputerQuery 'tag:canary' -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$ProfileId,

        [Parameter(Mandatory = $true)]
        [string]$ComputerQuery,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'landscape'
    $activityUri = "$($config.api_url.TrimEnd('/'))/api/v2/activities"

    # Build activity payload
    $activityPayload = @{
        activity_type = "ApplyPackageProfile"
        package_profile_id = $ProfileId
        query = $ComputerQuery
        deliver_after = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
    }

    $headers = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = 'application/json'
    }

    $response = Invoke-ConnectorRequest -Uri $activityUri -Method 'POST' -Body $activityPayload -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Info' -Message 'Landscape activity created' -CorrelationId $CorrelationId -Metadata @{
        activity_id = $response.id
        profile_id = $ProfileId
        query = $ComputerQuery
    }

    return $response
}

function Publish-LandscapeApplication {
    <#
    .SYNOPSIS
        Publish application to Landscape.
    .DESCRIPTION
        Creates package profile and activity to apply to target computers.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Publish-LandscapeApplication -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'landscape'

    # Check if connector is configured
    if (-not $config.api_url -or -not $config.api_token) {
        Write-StructuredLog -Level 'Warning' -Message 'Landscape connector missing configuration, returning stub response' -CorrelationId $CorrelationId -Metadata @{ connector = 'landscape' }
        return @{
            status = 'stubbed'
            correlation_id = $CorrelationId
            intent = $DeploymentIntent
        }
    }

    $accessToken = $config.api_token

    # Create package profile
    $profile = New-LandscapePackageProfile -DeploymentIntent $DeploymentIntent -AccessToken $accessToken -CorrelationId $CorrelationId

    if ($profile.status -eq 'failed') {
        return $profile
    }

    # Create activity to apply profile to ring-tagged computers
    $computerQuery = "tag:$($DeploymentIntent.Ring.ToLower())"
    $activity = New-LandscapeActivity -ProfileId $profile.id -ComputerQuery $computerQuery -AccessToken $accessToken -CorrelationId $CorrelationId

    return @{
        status = 'published'
        correlation_id = $CorrelationId
        profile_id = $profile.id
        profile_title = $profile.title
        activity_id = $activity.id
        computer_query = $computerQuery
        connector = 'landscape'
    }
}

function Remove-LandscapeApplication {
    <#
    .SYNOPSIS
        Remove package profile from Landscape.
    .PARAMETER ApplicationId
        Landscape package profile ID.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Remove-LandscapeApplication -ApplicationId 123 -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'landscape'
    $accessToken = $config.api_token

    $deleteUri = "$($config.api_url.TrimEnd('/'))/api/v2/package-profiles/$ApplicationId"
    $headers = @{
        Authorization = "Bearer $accessToken"
    }

    $response = Invoke-ConnectorRequest -Uri $deleteUri -Method 'DELETE' -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Warning' -Message 'Landscape package profile removed' -CorrelationId $CorrelationId -Metadata @{
        profile_id = $ApplicationId
    }

    return @{
        status = 'removed'
        correlation_id = $CorrelationId
        profile_id = $ApplicationId
        connector = 'landscape'
    }
}

function Get-LandscapeDeploymentStatus {
    <#
    .SYNOPSIS
        Query deployment status for correlation ID.
    .DESCRIPTION
        Searches for package profiles with correlation ID in tags and retrieves activity status.
    .PARAMETER CorrelationId
        Correlation ID to search for.
    .EXAMPLE
        $status = Get-LandscapeDeploymentStatus -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'landscape'
    $accessToken = $config.api_token

    # Search for package profiles with correlation ID in tags
    $searchUri = "$($config.api_url.TrimEnd('/'))/api/v2/package-profiles?tags=correlation:$CorrelationId"
    $headers = @{
        Authorization = "Bearer $accessToken"
        Accept = 'application/json'
    }

    $response = Invoke-ConnectorRequest -Uri $searchUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    if ($response.status -eq 'failed') {
        return $response
    }

    if ($response.Count -eq 0) {
        return @{
            status = 'not_found'
            correlation_id = $CorrelationId
            connector = 'landscape'
        }
    }

    $profile = $response[0]
    $profileId = $profile.id

    # Get activities for this profile
    $activitiesUri = "$($config.api_url.TrimEnd('/'))/api/v2/activities?package_profile_id=$profileId"
    $activitiesResponse = Invoke-ConnectorRequest -Uri $activitiesUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    if ($activitiesResponse.Count -eq 0) {
        return @{
            status = 'no_activities'
            correlation_id = $CorrelationId
            profile_id = $profileId
            connector = 'landscape'
        }
    }

    # Get activity results
    $activity = $activitiesResponse[0]
    $activityId = $activity.id

    $resultsUri = "$($config.api_url.TrimEnd('/'))/api/v2/activities/$activityId/results"
    $resultsResponse = Invoke-ConnectorRequest -Uri $resultsUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    $results = $resultsResponse
    $successCount = ($results | Where-Object { $_.status -eq 'succeeded' }).Count
    $failureCount = ($results | Where-Object { $_.status -eq 'failed' }).Count
    $pendingCount = ($results | Where-Object { $_.status -in @('pending', 'running') }).Count

    return @{
        status = 'queried'
        correlation_id = $CorrelationId
        profile_id = $profileId
        profile_title = $profile.title
        activity_id = $activityId
        success_count = $successCount
        failure_count = $failureCount
        pending_count = $pendingCount
        total_computers = $results.Count
        success_rate = if ($results.Count -gt 0) { ($successCount / $results.Count) * 100 } else { 0 }
        connector = 'landscape'
    }
}

function Test-LandscapeConnection {
    <#
    .SYNOPSIS
        Test connectivity to Landscape API.
    .PARAMETER AuthToken
        Not used (API token from config).
    .EXAMPLE
        $result = Test-LandscapeConnection -AuthToken 'dummy'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    $config = Get-ConnectorConfig -Name 'landscape'
    $testCid = Get-CorrelationId -Type uuid

    try {
        $accessToken = $config.api_token

        # Test API connectivity
        $testUri = "$($config.api_url.TrimEnd('/'))/api/v2/computers?limit=1"
        $headers = @{
            Authorization = "Bearer $accessToken"
        }

        $response = Invoke-ConnectorRequest -Uri $testUri -Method 'GET' -Headers $headers -CorrelationId $testCid

        Write-StructuredLog -Level 'Info' -Message 'Landscape connector test successful' -CorrelationId $testCid

        return @{
            connector = 'Landscape'
            status = 'healthy'
            checked_at = (Get-Date).ToString('o')
            account_name = $config.account_name
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Landscape connector test failed: $($_.Exception.Message)" -CorrelationId $testCid

        return @{
            connector = 'Landscape'
            status = 'unhealthy'
            error = $_.Exception.Message
            checked_at = (Get-Date).ToString('o')
        }
    }
}

function Get-LandscapeTargetDevices {
    <#
    .SYNOPSIS
        Get target devices for ring-based deployment.
    .DESCRIPTION
        Queries computers with ring-specific tag.
    .PARAMETER Ring
        Target ring (Lab, Canary, Pilot, Department, Global).
    .EXAMPLE
        $devices = Get-LandscapeTargetDevices -Ring 'Canary'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Lab', 'Canary', 'Pilot', 'Department', 'Global')]
        [string]$Ring
    )

    $config = Get-ConnectorConfig -Name 'landscape'
    $testCid = Get-CorrelationId -Type uuid

    try {
        $accessToken = $config.api_token

        # Query computers with ring tag
        $ringTag = $Ring.ToLower()
        $computersUri = "$($config.api_url.TrimEnd('/'))/api/v2/computers?tags=$ringTag"
        $headers = @{
            Authorization = "Bearer $accessToken"
        }

        $response = Invoke-ConnectorRequest -Uri $computersUri -Method 'GET' -Headers $headers -CorrelationId $testCid

        if ($response.status -eq 'failed') {
            return @()
        }

        $devices = $response | ForEach-Object {
            @{
                device_id = $_.id
                device_name = $_.hostname
                ring = $Ring
                tags = $_.tags
                last_ping = $_.last_ping_time
                distribution = $_.distribution
            }
        }

        Write-StructuredLog -Level 'Debug' -Message 'Landscape target devices retrieved' -CorrelationId $testCid -Metadata @{
            count = $devices.Count
            ring = $Ring
        }

        return $devices
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Failed to retrieve Landscape target devices: $($_.Exception.Message)" -CorrelationId $testCid
        return @()
    }
}
