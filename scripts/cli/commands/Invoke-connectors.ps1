# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Reports connector health and capabilities.
.DESCRIPTION
    Queries each connector to report readiness, idempotency status, and audit-worthy metadata.
.PARAMETER AuthToken
    Authentication token.
.EXAMPLE
    Invoke-connectors.ps1 -AuthToken $token
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/execution-plane-connectors.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../connectors/ConnectorManager.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

try {
    $statuses = Test-ConnectorConnection -AuthToken $AuthToken
    $correlationId = Get-CorrelationId -Type uuid
    Write-StructuredLog -Level 'Info' -Message 'Connectors command executed' -CorrelationId $correlationId `
        -Metadata @{ count = $statuses.Count }

    return $statuses
    exit 0
} catch {
    Write-StructuredLog -Level 'Error' -Message "Connectors command failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type uuid) `
        -Metadata @{ error = $_.Exception.Message; stack_trace = $_.ScriptStackTrace }
    exit 1
}
