# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Lists ring definitions and thresholds.
.DESCRIPTION
    Reads promotion-gate configuration to expose success rate, time-to-compliance, and CAB requirements per ring.
.PARAMETER AuthToken
    Entra ID token.
.EXAMPLE
    Invoke-rings.ps1 -AuthToken $token
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/ring-model.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

try {
    $promotionsPath = (Join-Path $PSScriptRoot '..\..\config\promotion-gates.json')
    if (-not (Test-Path -Path $promotionsPath)) {
        throw "Promotion gate definition missing: $promotionsPath"
    }
    $gateConfig = Get-Content -Path $promotionsPath -Raw | ConvertFrom-Json

    $correlationId = Get-CorrelationId -Type uuid
    Write-StructuredLog -Level 'Info' -Message 'Rings command executed' -CorrelationId $correlationId
    return $gateConfig.rings
    exit 0
} catch {
    Write-StructuredLog -Level 'Error' -Message "Rings command failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type uuid) `
        -Metadata @{ error = $_.Exception.Message; stack_trace = $_.ScriptStackTrace }
    exit 1
}
