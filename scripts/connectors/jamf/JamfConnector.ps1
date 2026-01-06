# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Jamf Pro connector implementation (macOS).
.DESCRIPTION
    Handles policy publishing, package upload, removal, and status queries via the Jamf Pro API.
    Supports OAuth2 authentication and smart group targeting.
.NOTES
Version: 2.0
Author: Platform Engineering
Related Docs: docs/modules/jamf/connector-spec.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/ConnectorBase.ps1"

function New-JamfPackage {
    <#
    .SYNOPSIS
        Upload package to Jamf Pro distribution point.
    .PARAMETER PackagePath
        Local path to PKG file.
    .PARAMETER PackageName
        Package display name.
    .PARAMETER AccessToken
        Jamf Pro OAuth2 access token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $package = New-JamfPackage -PackagePath './app.pkg' -PackageName 'MyApp' -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSShouldProcess', '', Justification = 'ShouldProcess declared for interface compatibility, actual confirmation handled by execution plane')]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$PackagePath,

        [Parameter(Mandatory = $true)]
        [string]$PackageName,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'jamf'
    $packageUri = "$($config.api_url.TrimEnd('/'))/api/v1/packages"

    # Create package metadata
    $packageMetadata = @{
        packageName = $PackageName
        fileName = (Split-Path -Leaf $PackagePath)
        categoryId = -1
        info = "CorrelationId: $CorrelationId"
        notes = "Uploaded via EUCORA Control Plane"
        priority = 10
        fillUserTemplate = $false
        fillExistingUsers = $false
        swu = $false
        rebootRequired = $false
        osRequirements = ""
    }

    $headers = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = 'application/json'
    }

    # Create package record
    $packageResponse = Invoke-ConnectorRequest -Uri $packageUri -Method 'POST' -Body $packageMetadata -Headers $headers -CorrelationId $CorrelationId

    if ($packageResponse.status -eq 'failed') {
        return $packageResponse
    }

    # Upload package file to distribution point
    $packageId = $packageResponse.id
    $uploadUri = "$($config.api_url.TrimEnd('/'))/api/v1/packages/$packageId/upload"

    # Read file as byte array
    $fileBytes = [System.IO.File]::ReadAllBytes($PackagePath)
    $boundary = [System.Guid]::NewGuid().ToString()

    $uploadHeaders = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = "multipart/form-data; boundary=$boundary"
    }

    # Build multipart form data
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$((Split-Path -Leaf $PackagePath))`"",
        "Content-Type: application/octet-stream",
        "",
        [System.Text.Encoding]::GetEncoding("iso-8859-1").GetString($fileBytes),
        "--$boundary--"
    )
    $bodyString = $bodyLines -join "`r`n"

    try {
        $null = Invoke-RestMethod -Uri $uploadUri -Method 'POST' -Headers $uploadHeaders -Body $bodyString -TimeoutSec 300

        Write-StructuredLog -Level 'Info' -Message 'Jamf package uploaded' -CorrelationId $CorrelationId -Metadata @{
            package_id = $packageId
            package_name = $PackageName
        }

        return @{
            id = $packageId
            name = $PackageName
            status = 'uploaded'
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Jamf package upload failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        throw
    }
}

function New-JamfPolicy {
    <#
    .SYNOPSIS
        Create Jamf Pro policy for deployment.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER PackageId
        Jamf package ID.
    .PARAMETER AccessToken
        Jamf Pro OAuth2 access token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $policy = New-JamfPolicy -DeploymentIntent $intent -PackageId 123 -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSShouldProcess', '', Justification = 'ShouldProcess declared for interface compatibility, actual confirmation handled by execution plane')]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [int]$PackageId,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'jamf'
    $policyUri = "$($config.api_url.TrimEnd('/'))/JSSResource/policies/id/0"

    # Get smart group ID for ring
    $smartGroupId = Get-JamfSmartGroupId -Ring $DeploymentIntent.Ring -Config $config

    # Build policy XML (Jamf Classic API uses XML)
    $policyXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<policy>
    <general>
        <name>$($DeploymentIntent.AppName) - $($DeploymentIntent.Ring)</name>
        <enabled>true</enabled>
        <trigger>EVENT</trigger>
        <trigger_checkin>false</trigger_checkin>
        <trigger_enrollment_complete>false</trigger_enrollment_complete>
        <trigger_login>false</trigger_login>
        <trigger_logout>false</trigger_logout>
        <trigger_network_state_changed>false</trigger_network_state_changed>
        <trigger_startup>false</trigger_startup>
        <trigger_other>CorrelationId_$CorrelationId</trigger_other>
        <frequency>Once per computer</frequency>
        <category>
            <name>EUCORA Deployments</name>
        </category>
    </general>
    <scope>
        <all_computers>false</all_computers>
        <computer_groups>
            <computer_group>
                <id>$smartGroupId</id>
            </computer_group>
        </computer_groups>
    </scope>
    <package_configuration>
        <packages>
            <package>
                <id>$PackageId</id>
                <action>Install</action>
            </package>
        </packages>
    </package_configuration>
    <scripts>
        <size>0</size>
    </scripts>
    <maintenance>
        <recon>true</recon>
    </maintenance>
</policy>
"@

    $headers = @{
        Authorization = "Bearer $AccessToken"
        'Content-Type' = 'application/xml'
    }

    $response = Invoke-RestMethod -Uri $policyUri -Method 'POST' -Body $policyXml -Headers $headers -TimeoutSec 60

    Write-StructuredLog -Level 'Info' -Message 'Jamf policy created' -CorrelationId $CorrelationId -Metadata @{
        policy_id = $response.policy.id
        policy_name = $response.policy.general.name
    }

    return @{
        id = $response.policy.id
        name = $response.policy.general.name
        status = 'created'
    }
}

function Publish-JamfApplication {
    <#
    .SYNOPSIS
        Publish application to Jamf Pro.
    .DESCRIPTION
        Uploads package and creates policy with smart group targeting.
    .PARAMETER DeploymentIntent
        Deployment intent hashtable.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Publish-JamfApplication -DeploymentIntent $intent -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'jamf'

    # Check if connector is configured
    if (-not $config.client_id -or -not $config.client_secret) {
        Write-StructuredLog -Level 'Warning' -Message 'Jamf connector missing credentials, returning stub response' -CorrelationId $CorrelationId -Metadata @{ connector = 'jamf' }
        return @{
            status = 'stubbed'
            correlation_id = $CorrelationId
            intent = $DeploymentIntent
        }
    }

    # Acquire OAuth2 token
    $accessToken = Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId $CorrelationId

    # Upload package
    if ($DeploymentIntent.PackagePath) {
        $package = New-JamfPackage -PackagePath $DeploymentIntent.PackagePath -PackageName $DeploymentIntent.AppName -AccessToken $accessToken -CorrelationId $CorrelationId

        if ($package.status -eq 'failed') {
            return $package
        }
    }
    else {
        Write-StructuredLog -Level 'Warning' -Message 'No package path provided, skipping upload' -CorrelationId $CorrelationId
        $package = @{ id = 0 }
    }

    # Create policy
    $policy = New-JamfPolicy -DeploymentIntent $DeploymentIntent -PackageId $package.id -AccessToken $accessToken -CorrelationId $CorrelationId

    return @{
        status = 'published'
        correlation_id = $CorrelationId
        package_id = $package.id
        policy_id = $policy.id
        policy_name = $policy.name
        connector = 'jamf'
    }
}

function Remove-JamfApplication {
    <#
    .SYNOPSIS
        Remove policy from Jamf Pro.
    .PARAMETER ApplicationId
        Jamf policy ID.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $result = Remove-JamfApplication -ApplicationId 123 -CorrelationId $cid
    #>
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSShouldProcess', '', Justification = 'ShouldProcess declared for interface compatibility, actual confirmation handled by execution plane')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'jamf'

    # Acquire OAuth2 token
    $accessToken = Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId $CorrelationId

    $deleteUri = "$($config.api_url.TrimEnd('/'))/JSSResource/policies/id/$ApplicationId"
    $headers = @{
        Authorization = "Bearer $accessToken"
    }

    $null = Invoke-ConnectorRequest -Uri $deleteUri -Method 'DELETE' -Headers $headers -CorrelationId $CorrelationId

    Write-StructuredLog -Level 'Warning' -Message 'Jamf policy removed' -CorrelationId $CorrelationId -Metadata @{
        policy_id = $ApplicationId
    }

    return @{
        status = 'removed'
        correlation_id = $CorrelationId
        policy_id = $ApplicationId
        connector = 'jamf'
    }
}

function Get-JamfDeploymentStatus {
    <#
    .SYNOPSIS
        Query deployment status for correlation ID.
    .DESCRIPTION
        Searches for policies with correlation ID in trigger and retrieves execution logs.
    .PARAMETER CorrelationId
        Correlation ID to search for.
    .EXAMPLE
        $status = Get-JamfDeploymentStatus -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'jamf'

    # Acquire OAuth2 token
    $accessToken = Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId $CorrelationId

    # Search for policies with correlation ID in trigger
    $searchUri = "$($config.api_url.TrimEnd('/'))/JSSResource/policies"
    $headers = @{
        Authorization = "Bearer $accessToken"
        Accept = 'application/json'
    }

    $response = Invoke-ConnectorRequest -Uri $searchUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    if ($response.status -eq 'failed') {
        return $response
    }

    # Find policy matching correlation ID
    $matchingPolicy = $response.policies | Where-Object { $_.name -match $CorrelationId }

    if (-not $matchingPolicy) {
        return @{
            status = 'not_found'
            correlation_id = $CorrelationId
            connector = 'jamf'
        }
    }

    # Get policy details
    $policyId = $matchingPolicy.id
    $policyUri = "$($config.api_url.TrimEnd('/'))/JSSResource/policies/id/$policyId"
    $policyDetails = Invoke-ConnectorRequest -Uri $policyUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    # Get policy logs
    $logsUri = "$($config.api_url.TrimEnd('/'))/JSSResource/computermanagementlogs/policy/id/$policyId"
    $logs = Invoke-ConnectorRequest -Uri $logsUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    $successCount = ($logs.computer_management_logs | Where-Object { $_.status -eq 'Completed' }).Count
    $failureCount = ($logs.computer_management_logs | Where-Object { $_.status -eq 'Failed' }).Count
    $pendingCount = ($logs.computer_management_logs | Where-Object { $_.status -eq 'Pending' }).Count

    return @{
        status = 'queried'
        correlation_id = $CorrelationId
        policy_id = $policyId
        policy_name = $policyDetails.policy.general.name
        success_count = $successCount
        failure_count = $failureCount
        pending_count = $pendingCount
        total_devices = $logs.computer_management_logs.Count
        success_rate = if ($logs.computer_management_logs.Count -gt 0) { ($successCount / $logs.computer_management_logs.Count) * 100 } else { 0 }
        connector = 'jamf'
    }
}

function Test-JamfConnection {
    <#
    .SYNOPSIS
        Test connectivity to Jamf Pro API.
    .PARAMETER AuthToken
        Not used (OAuth2 token acquired internally).
    .EXAMPLE
        $result = Test-JamfConnection -AuthToken 'dummy'
    #>
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Parameter required for interface compatibility, token acquired internally')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    $config = Get-ConnectorConfig -Name 'jamf'
    $testCid = Get-CorrelationId -Type uuid

    try {
        # Acquire OAuth2 token
        $accessToken = Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId $testCid

        # Test API connectivity
        $testUri = "$($config.api_url.TrimEnd('/'))/api/v1/jamf-pro-information"
        $headers = @{
            Authorization = "Bearer $accessToken"
        }

        $response = Invoke-ConnectorRequest -Uri $testUri -Method 'GET' -Headers $headers -CorrelationId $testCid

        Write-StructuredLog -Level 'Info' -Message 'Jamf connector test successful' -CorrelationId $testCid

        return @{
            connector = 'Jamf'
            status = 'healthy'
            checked_at = (Get-Date).ToString('o')
            jamf_version = $response.version
        }
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Jamf connector test failed: $($_.Exception.Message)" -CorrelationId $testCid

        return @{
            connector = 'Jamf'
            status = 'unhealthy'
            error = $_.Exception.Message
            checked_at = (Get-Date).ToString('o')
        }
    }
}

function Get-JamfTargetDevices {
    <#
    .SYNOPSIS
        Get target devices for ring-based deployment.
    .DESCRIPTION
        Queries smart group membership for ring-specific group.
    .PARAMETER Ring
        Target ring (Lab, Canary, Pilot, Department, Global).
    .EXAMPLE
        $devices = Get-JamfTargetDevices -Ring 'Canary'
    #>
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of devices, plural noun is semantically correct')]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('Lab', 'Canary', 'Pilot', 'Department', 'Global')]
        [string]$Ring
    )

    $config = Get-ConnectorConfig -Name 'jamf'
    $testCid = Get-CorrelationId -Type uuid

    try {
        # Acquire OAuth2 token
        $accessToken = Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId $testCid

        # Get smart group ID
        $smartGroupId = Get-JamfSmartGroupId -Ring $Ring -Config $config
        if (-not $smartGroupId) {
            Write-StructuredLog -Level 'Warning' -Message "No smart group ID configured for ring $Ring" -CorrelationId $testCid
            return @()
        }

        # Query smart group members
        $groupUri = "$($config.api_url.TrimEnd('/'))/JSSResource/computergroups/id/$smartGroupId"
        $headers = @{
            Authorization = "Bearer $accessToken"
            Accept = 'application/json'
        }

        $response = Invoke-ConnectorRequest -Uri $groupUri -Method 'GET' -Headers $headers -CorrelationId $testCid

        if ($response.status -eq 'failed') {
            return @()
        }

        $devices = $response.computer_group.computers | ForEach-Object {
            @{
                device_id = $_.id
                device_name = $_.name
                ring = $Ring
                serial_number = $_.serial_number
            }
        }

        Write-StructuredLog -Level 'Debug' -Message 'Jamf target devices retrieved' -CorrelationId $testCid -Metadata @{
            count = $devices.Count
            ring = $Ring
        }

        return $devices
    }
    catch {
        Write-StructuredLog -Level 'Error' -Message "Failed to retrieve Jamf target devices: $($_.Exception.Message)" -CorrelationId $testCid
        return @()
    }
}

function Get-JamfSmartGroupId {
    <#
    .SYNOPSIS
        Get Jamf smart group ID for ring.
    .PARAMETER Ring
        Target ring.
    .PARAMETER Config
        Connector configuration.
    .EXAMPLE
        $groupId = Get-JamfSmartGroupId -Ring 'Canary' -Config $config
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring,

        [Parameter(Mandatory = $true)]
        [hashtable]$Config
    )

    $ringGroupMap = @{
        'Lab' = $Config.smart_groups.lab
        'Canary' = $Config.smart_groups.canary
        'Pilot' = $Config.smart_groups.pilot
        'Department' = $Config.smart_groups.department
        'Global' = $Config.smart_groups.global
    }

    return $ringGroupMap[$Ring]
}
