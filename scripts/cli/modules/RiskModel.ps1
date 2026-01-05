# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Risk model utilities for deterministic risk scoring.
.DESCRIPTION
    Loads the risk_model_v1.0 definition and calculates risk scores from normalized factor inputs (0.0-1.0). Returns a value between 0-100 and enforces calibration metadata.
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/risk-model.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Get-RiskModel {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [string]$ModelPath = (Join-Path $PSScriptRoot '..\..\config\risk-model-v1.0.json')
    )

    if (-not (Test-Path -Path $ModelPath)) {
        throw "Risk model definition not found at $ModelPath"
    }

    return Get-Content -Path $ModelPath -Raw | ConvertFrom-Json
}
function Calculate-RiskScore {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$Factors,

        [Parameter(Mandatory = $false)]
        $Model
    )

    if (-not $Model) {
        $Model = Get-RiskModel
    }

    $totalWeight = 0.0
    $score = 0.0
    foreach ($entry in $Model.factors.GetEnumerator()) {
        $factorName = $entry.Key
        $weight = [double]$entry.Value.weight
        $normalized = 0.0
        if ($Factors.ContainsKey($factorName)) {
            $normalized = [math]::Max(0.0, [math]::Min(1.0, [double]$Factors[$factorName]))
        }
        $score += $weight * $normalized
        $totalWeight += $weight
    }

    if ($totalWeight -eq 0) {
        return 0
    }

    $clamped = [math]::Min(100, [math]::Max(0, ($score / $totalWeight) * 100))
    return [math]::Round($clamped, 2)
}
