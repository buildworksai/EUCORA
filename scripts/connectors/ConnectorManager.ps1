# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Entry point for execution-plane connectors.
.DESCRIPTION
    Resolves the connector name from the deployment intent, imports the appropriate module, and routes Publish/Remove/Status/Test/TargetDevice calls. Ensures correlation ids and logging remain consistent across platforms.
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/execution-plane-connectors.md, .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/common/ConnectorBase.ps1"
. "$PSScriptRoot/../utilities/common/Get-CorrelationId.ps1"

$script:ConnectorMapping = @{
    intune = 'intune/IntuneConnector.ps1'
    jamf = 'jamf/JamfConnector.ps1'
    sccm = 'sccm/SccmConnector.ps1'
    landscape = 'landscape/LandscapeConnector.ps1'
    ansible = 'ansible/AnsibleConnector.ps1'
}
$script:LoadedConnectors = @{}

function Get-ConnectorPascalName {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $segments = $Name.Split('-')
    $pascal = ($segments | ForEach-Object {
        if ([string]::IsNullOrWhiteSpace($_)) { return '' }
        $lower = $_.ToLower()
        return $lower.Substring(0,1).ToUpper() + $lower.Substring(1)
    }) -join ''
    return $pascal
}

function Get-ConnectorFunctionName {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Verb,
        [Parameter(Mandatory = $true)]
        [string]$Connector,
        [Parameter(Mandatory = $true)]
        [string]$Suffix
    )

    $pascalName = Get-ConnectorPascalName -Name $Connector
    return "$Verb-$pascalName$Suffix"
}

function Resolve-ConnectorName {
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent
    )

    if ($DeploymentIntent.ContainsKey('Connector')) {
        return $DeploymentIntent.Connector.ToLower()
    }
    if ($DeploymentIntent.ContainsKey('Platform')) {
        return $DeploymentIntent.Platform.ToLower()
    }
    return 'intune'
}

function Import-ConnectorModule {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('intune','jamf','sccm','landscape','ansible')]
        [string]$Name
    )

    if ($script:LoadedConnectors.ContainsKey($Name)) {
        return
    }
    if (-not $script:ConnectorMapping.ContainsKey($Name)) {
        throw "Unknown connector target: $Name"
    }
    $path = Join-Path $PSScriptRoot $script:ConnectorMapping[$Name]
    . (Resolve-Path $path).Path
    $script:LoadedConnectors[$Name] = $true
}

function Publish-Application {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $connector = Resolve-ConnectorName -DeploymentIntent $DeploymentIntent
    Import-ConnectorModule -Name $connector
    $functionName = Get-ConnectorFunctionName -Verb 'Publish' -Connector $connector -Suffix 'Application'
    if (-not (Get-Command -Name $functionName -ErrorAction SilentlyContinue)) {
        throw "Connector function $functionName missing after import"
    }

    $result = & $functionName -DeploymentIntent $DeploymentIntent -CorrelationId $CorrelationId
    Write-StructuredLog -Level 'Info' -Message 'Connector publish invoked' -CorrelationId $CorrelationId -Metadata @{ connector = $connector; intent = $DeploymentIntent; result_status = $result.status }
    return $result
}

function Remove-Application {
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'ShouldProcess support added, suppression for analyzer compatibility')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,
        [Parameter(Mandatory = $false)]
        [ValidateSet('intune','jamf','sccm','landscape','ansible')]
        [string]$ConnectorName = 'intune'
    )

    $connector = $ConnectorName.ToLower()
    Import-ConnectorModule -Name $connector
    $functionName = Get-ConnectorFunctionName -Verb 'Remove' -Connector $connector -Suffix 'Application'
    if (-not (Get-Command -Name $functionName -ErrorAction SilentlyContinue)) {
        throw "Connector function $functionName missing for removal"
    }

    $result = & $functionName -ApplicationId $ApplicationId -CorrelationId $CorrelationId
    Write-StructuredLog -Level 'Warning' -Message 'Connector remove invoked' -CorrelationId $CorrelationId -Metadata @{ connector = $connector; application_id = $ApplicationId; result_status = $result.status }
    return $result
}

function Get-DeploymentStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,
        [Parameter(Mandatory = $false)]
        [ValidateSet('intune','jamf','sccm','landscape','ansible')]
        [string]$ConnectorName
    )

    $requested = if ($ConnectorName) { @($ConnectorName.ToLower()) } else { $script:ConnectorMapping.Keys }
    $statuses = @()

    foreach ($name in $requested) {
        try {
            Import-ConnectorModule -Name $name
            $functionName = Get-ConnectorFunctionName -Verb 'Get' -Connector $name -Suffix 'DeploymentStatus'
            if (-not (Get-Command -Name $functionName -ErrorAction SilentlyContinue)) {
                Write-StructuredLog -Level 'Debug' -Message "Connector $name does not expose deployment status" -CorrelationId $CorrelationId
                continue
            }
            $status = & $functionName -CorrelationId $CorrelationId
            $statuses += @{ connector = $name; result = $status }
        }
        catch {
            Write-StructuredLog -Level 'Warning' -Message "Error fetching deployment status from $name - $($_.Exception.Message)" -CorrelationId $CorrelationId -Metadata @{ connector = $name }
            $statuses += @{ connector = $name; result = @{ status = 'error'; error = $_.Exception.Message } }
        }
    }

    Write-StructuredLog -Level 'Info' -Message 'Deployment status aggregation' -CorrelationId $CorrelationId -Metadata @{ connectors = $statuses.Count }
    return @{ correlation_id = $CorrelationId; status_by_connector = $statuses }
}

function Test-ConnectorConnection {
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidOverwritingBuiltInCmdlets', '', Justification = 'Renamed to avoid conflict with built-in Test-Connection cmdlet')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    $reports = @()
    foreach ($name in $script:ConnectorMapping.Keys) {
        try {
            Import-ConnectorModule -Name $name
            $function = Get-ConnectorFunctionName -Verb 'Test' -Connector $name -Suffix 'Connection'
            if (-not (Get-Command -Name $function -ErrorAction SilentlyContinue)) {
                continue
            }
            $reports += & $function -AuthToken $AuthToken
        }
        catch {
            Write-StructuredLog -Level 'Warning' -Message "Connector $name reported test failure" -CorrelationId (Get-CorrelationId -Type uuid) -Metadata @{ connector = $name; error = $_.Exception.Message }
            $reports += @{ connector = $name; status = 'error'; error = $_.Exception.Message }
        }
    }

    Write-StructuredLog -Level 'Info' -Message 'Connector test connection executed' -CorrelationId (Get-CorrelationId -Type uuid) -Metadata @{ connector_count = $reports.Count }
    return $reports
}

function Get-TargetDevices {
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of devices, plural noun is semantically correct')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring,
        [Parameter(Mandatory = $false)]
        [ValidateSet('intune','jamf','sccm','landscape','ansible')]
        [string]$ConnectorName = 'intune'
    )

    $connector = $ConnectorName.ToLower()
    Import-ConnectorModule -Name $connector
    $functionName = Get-ConnectorFunctionName -Verb 'Get' -Connector $connector -Suffix 'TargetDevices'
    if (-not (Get-Command -Name $functionName -ErrorAction SilentlyContinue)) {
        Write-StructuredLog -Level 'Debug' -Message "Connector $connector missing target device helper" -CorrelationId (Get-CorrelationId -Type uuid)
        return @()
    }

    $devices = & $functionName -Ring $Ring
    Write-StructuredLog -Level 'Info' -Message 'Target devices retrieved' -CorrelationId (Get-CorrelationId -Type uuid) -Metadata @{ connector = $connector; ring = $Ring; count = ($devices.Count) }
    return $devices
}
