# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Connector stub implementations for CLI development.
.DESCRIPTION
    Provides deterministic Publish/Remove/Get operations that log correlation IDs and return stubbed payloads. Intended as placeholders until execution-plane connectors are implemented.
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/planning/phase-3-connectors-prompt.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$commonPath = Join-Path $PSScriptRoot '..\..\utilities\common\Get-CorrelationId.ps1'
$logPath = Join-Path $PSScriptRoot '..\..\utilities\logging\Write-StructuredLog.ps1'
. (Resolve-Path $commonPath).Path
. (Resolve-Path $logPath).Path
$connectorStatuses = @{
    Intune = 'Ready'
    Jamf = 'Ready'
    SCCM = 'Online'
    Landscape = 'Ready'
    Ansible = 'Ready'
}
function Publish-Application {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )
    Write-StructuredLog -Level 'Info' -Message 'Publish-Application stub invoked' -CorrelationId $CorrelationId `
        -Metadata @{ deployment_intent = $DeploymentIntent; connector = 'stub' }
    return @{
        status = 'published'
        correlation_id = $CorrelationId
        intent = $DeploymentIntent
        timestamp = (Get-Date).ToString('o')
    }
}
function Remove-Application {
    [CmdletBinding(SupportsShouldProcess)]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'Stub function for development, does not perform actual removal')]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSShouldProcess', '', Justification = 'Stub function, ShouldProcess declared for interface compatibility')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )
    Write-StructuredLog -Level 'Warning' -Message 'Remove-Application stub invoked' -CorrelationId $CorrelationId `
        -Metadata @{ application_id = $ApplicationId }
    return @{
        status = 'removed'
        application_id = $ApplicationId
        correlation_id = $CorrelationId
        timestamp = (Get-Date).ToString('o')
    }
}
function Get-DeploymentStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )
    Write-StructuredLog -Level 'Info' -Message 'Get-DeploymentStatus stub invoked' -CorrelationId $CorrelationId
    return @{
        status = 'in-progress'
        correlation_id = $CorrelationId
        completed = $false
        managed_devices = 42
    }
}
function Test-ConnectorConnection {
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidOverwritingBuiltInCmdlets', '', Justification = 'Stub function for connector testing, renamed to avoid conflict')]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Parameter required for interface compatibility')]
    param(
        [Parameter(Mandatory = $false)]
        [string]$AuthToken
    )
    $statusReport = $connectorStatuses.Keys | ForEach-Object {
        [ordered]@{
            connector = $_
            status = $connectorStatuses[$_]
            correlation_id = Get-CorrelationId -Type uuid
            checked_at = (Get-Date).ToString('o')
        }
    }
    Write-StructuredLog -Level 'Info' -Message 'Test-ConnectorConnection stub executed' -CorrelationId (Get-CorrelationId -Type deployment) `
        -Metadata @{ connectors = $connectorStatuses.Keys }
    return $statusReport
}
function Get-TargetDevice {
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of devices, plural noun is appropriate')]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring
    )
    $devices = 1..5 | ForEach-Object {
        [ordered]@{
            device_id = "device-${Ring}-${_}"
            ring = $Ring
            last_seen = (Get-Date).AddMinutes(-$_).ToString('o')
        }
    }
    Write-StructuredLog -Level 'Debug' -Message 'Get-TargetDevice stub invoked' -CorrelationId (Get-CorrelationId -Type uuid) `
        -Metadata @{ ring = $Ring; count = $devices.Count }
    return $devices
}
function Get-ConnectorStatus {
    [CmdletBinding()]
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of connector statuses, plural noun is appropriate')]
    param()
    return $connectorStatuses.GetEnumerator() | ForEach-Object {
        [ordered]@{
            connector = $_.Key
            status = $_.Value
            last_checked = (Get-Date).ToString('o')
        }
    }
}
