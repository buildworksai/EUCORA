# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Evaluate promotion gates per ring definitions.
.DESCRIPTION
Loads gate thresholds from JSON, compares telemetry, incidents, CAB approvals, rollback validation. Returns gate results.
.PARAMETER CurrentRing
Current ring identifier.
.PARAMETER Telemetry
Hashtable with success_rate, time_to_compliance_hours, incident_count.
.PARAMETER DeploymentIntent
Hashtable with risk_score (int), rollback_plan (hashtable), cab_approval_id (string).
.PARAMETER ConfigPath
Path to promotion-gates.json.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/ring-model.md, .agents/rules/06-ring-rollout-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Load-PromotionConfig {
    param([string]$ConfigPath)
    if (-not (Test-Path -Path $ConfigPath)) { throw "Config missing: $ConfigPath" }
    return Get-Content -Path $ConfigPath -Raw | ConvertFrom-Json
}
function Get-IntentProperty {
    param($Intent, $PropertyName, $Default)
    if ($Intent -is [System.Collections.IDictionary] -and $Intent.ContainsKey($PropertyName)) {
        return $Intent[$PropertyName]
    }
    $prop = $Intent.PSObject.Properties[$PropertyName]
    if ($prop) {
        return $prop.Value
    }
    return $Default
}

function Test-PromotionGates {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet('ring-0-lab','ring-1-canary','ring-2-pilot','ring-3-department','ring-4-global')]
        [string]$CurrentRing,
        [Parameter(Mandatory=$true)]
        [hashtable]$Telemetry,
        [Parameter(Mandatory=$true)]
        [hashtable]$DeploymentIntent,
        [string]$ConfigPath = (Join-Path $PSScriptRoot '..\..\config\promotion-gates.json')
    )
    $config = Load-PromotionConfig -ConfigPath $ConfigPath
    $ringConfig = $config.rings.$CurrentRing
    $gatesPassed = @()
    $gatesFailed = @()
    $gateResults = @{}
    $successRate = [double]$Telemetry.success_rate
    $gateResults.success_rate = @{ threshold = $ringConfig.success_rate_threshold; actual = $successRate; passed = ($successRate -ge $ringConfig.success_rate_threshold) }
    if ($gateResults.success_rate.passed) { $gatesPassed += 'success_rate' } else { $gatesFailed += 'success_rate' }
    $thresholdHours = $ringConfig.time_to_compliance.online_hours
    $gateResults.time_to_compliance = @{ threshold_hours = $thresholdHours; actual_hours = $Telemetry.time_to_compliance_hours; passed = ($Telemetry.time_to_compliance_hours -le $thresholdHours) }
    if ($gateResults.time_to_compliance.passed) { $gatesPassed += 'time_to_compliance' } else { $gatesFailed += 'time_to_compliance' }
    $gateResults.incident_count = @{ max_allowed = $ringConfig.max_incidents; actual = $Telemetry.incident_count; passed = ($Telemetry.incident_count -le $ringConfig.max_incidents) }
    if ($gateResults.incident_count.passed) { $gatesPassed += 'incident_count' } else { $gatesFailed += 'incident_count' }
    $cabRequired = $false
    $riskScore = [int](Get-IntentProperty -Intent $DeploymentIntent -PropertyName 'risk_score' -Default 0)
    $cabApprovalId = Get-IntentProperty -Intent $DeploymentIntent -PropertyName 'cab_approval_id' -Default $null
    $cabThreshold = $ringConfig.cab_approval_required_if_risk_gt
    if (-not $cabThreshold) { $cabThreshold = 100 }
    if ($CurrentRing -eq 'ring-2-pilot' -or $CurrentRing -eq 'ring-1-canary') {
        $cabRequired = ($riskScore -gt $cabThreshold)
    }
    $cabApproved = $false
    if ($cabApprovalId) { $cabApproved = $true }
    $gateResults.cab_approval = @{ required = $cabRequired; approved = $cabApproved; passed = (-not $cabRequired) -or $cabApproved }
    if ($gateResults.cab_approval.passed) { $gatesPassed += 'cab_approval' } else { $gatesFailed += 'cab_approval' }
    $rollbackPlan = Get-IntentProperty -Intent $DeploymentIntent -PropertyName 'rollback_plan' -Default @{ validated = $false }
    if ($CurrentRing -eq 'ring-0-lab' -and -not $rollbackPlan.validated) {
        $gatesFailed += 'rollback_validation'
        $gateResults.rollback_validation = @{ required = $true; validated = $false; passed = $false }
    }
    else {
        $gateResults.rollback_validation = @{ required = $true; validated = $true; passed = $rollbackPlan.validated }
        if ($gateResults.rollback_validation.passed) { $gatesPassed += 'rollback_validation' } else { $gatesFailed += 'rollback_validation' }
    }
    return [pscustomobject]@{
        AllowPromotion = ($gatesFailed.Count -eq 0)
        GatesPassed = $gatesPassed
        GatesFailed = $gatesFailed
        GateResults = $gateResults
    }
}
