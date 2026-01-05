# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Retrieves deployment status for a correlation id.
.DESCRIPTION
    Queries connectors for the latest status of the deployment that shares the provided correlation identifier.
.PARAMETER AuthToken
    Entra ID bearer token for Graph API.
.PARAMETER CorrelationId
    Correlation id generated at deployment time.
.PARAMETER Connector
    Optional connector to target (Intune/Jamf/SCCM/Landscape/Ansible).
.EXAMPLE
    Invoke-status.ps1 -AuthToken $token -CorrelationId "dp-20260104-001"
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/planning/phase-3-connectors-prompt.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $false)]
    [string]$CorrelationId,

    [Parameter(Mandatory = $false)]
    [ValidateSet('intune','jamf','sccm','landscape','ansible')]
    [string]$Connector
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../connectors/ConnectorManager.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

if (-not $CorrelationId) {
    $CorrelationId = Get-CorrelationId -Type deployment
}

if (-not (Test-CorrelationId -CorrelationId $CorrelationId)) {
    throw "Invalid correlation id: $CorrelationId"
}

$status = Get-DeploymentStatus -CorrelationId $CorrelationId -ConnectorName $Connector
Write-StructuredLog -Level 'Info' -Message 'Status command completed' -CorrelationId $CorrelationId `
    -Metadata @{ status = $status.status_by_connector; connector = $Connector }

return $status
