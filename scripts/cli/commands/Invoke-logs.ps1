# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Returns structured log samples for recent deployments.
.DESCRIPTION
    This helper surfaces the last few structured log entries per ring for fast triage (mocked data until log store integration exists).
.PARAMETER AuthToken
    Entra ID token for API access.
.PARAMETER Ring
    Optional ring filter (ring-0-lab .. ring-4-global).
.EXAMPLE
    Invoke-logs.ps1 -AuthToken $token -Ring 'ring-1-canary'
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/control-plane-design.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $false)]
    [ValidateSet('ring-0-lab','ring-1-canary','ring-2-pilot','ring-3-department','ring-4-global')]
    [string]$Ring
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

try {
    $ringFilter = if ($Ring) { $Ring } else { 'ring-1-canary' }
    $entries = 1..3 | ForEach-Object {
        [ordered]@{
            timestamp = (Get-Date).AddMinutes(-($_ * 5)).ToString('o')
            level = 'Info'
            message = "Ring log entry #$_"
            ring = $ringFilter
            correlation_id = Get-CorrelationId -Type deployment
        }
    }

    $correlationId = Get-CorrelationId -Type evidence
    Write-StructuredLog -Level 'Info' -Message 'Logs command executed' -CorrelationId $correlationId `
        -Metadata @{ ring = $ringFilter; entries = $entries.Count }

    return $entries
    exit 0
} catch {
    Write-StructuredLog -Level 'Error' -Message "Logs command failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type evidence) `
        -Metadata @{ error = $_.Exception.Message; stack_trace = $_.ScriptStackTrace; ring = $Ring }
    exit 1
}
