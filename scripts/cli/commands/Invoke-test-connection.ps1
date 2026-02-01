# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Exercises connector authentication via test credentials.
.DESCRIPTION
    Calls Test-ConnectorConnection helper to ensure each connector reports ready status and logs the outcome.
.PARAMETER AuthToken
    Authentication token to pass through to connectors.
.EXAMPLE
    Invoke-test-connection.ps1 -AuthToken $token
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
    $results = Test-ConnectorConnection -AuthToken $AuthToken
    $correlationId = Get-CorrelationId -Type uuid
    Write-StructuredLog -Level 'Info' -Message 'Test-ConnectorConnection command executed' -CorrelationId $correlationId
    return $results
    exit 0
} catch {
    Write-StructuredLog -Level 'Error' -Message "Test-connection command failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type uuid) `
        -Metadata @{ error = $_.Exception.Message; stack_trace = $_.ScriptStackTrace }
    exit 1
}
