# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Removes or rolls back an application via connectors.
.DESCRIPTION
    Delegates rollback operations to execution-plane connectors while logging correlation ids and maintaining SoD.
.PARAMETER AuthToken
    Entra ID bearer token.
.PARAMETER ApplicationId
    Application identifier to rollback.
.PARAMETER CorrelationId
    Optional rollback correlation identifier.
.PARAMETER Connector
    Optional connector hint for rollback (default Intune).
.EXAMPLE
    Invoke-rollback.ps1 -AuthToken $token -ApplicationId 'app-123'
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/planning/phase-3-connectors-prompt.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $true)]
    [string]$ApplicationId,

    [Parameter(Mandatory = $false)]
    [string]$CorrelationId,

    [Parameter(Mandatory = $false)]
    [ValidateSet('intune','jamf','sccm','landscape','ansible')]
    [string]$Connector = 'intune'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../connectors/ConnectorManager.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

$correlationId = if ($CorrelationId) { $CorrelationId } else { Get-CorrelationId -Type deployment }
$result = Remove-Application -ApplicationId $ApplicationId -CorrelationId $correlationId -ConnectorName $Connector

Write-StructuredLog -Level 'Warning' -Message 'Rollback command executed' -CorrelationId $correlationId `
    -Metadata @{ application_id = $ApplicationId; connector = $Connector }

return $result
