# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Validate evidence pack schema and completeness per governance rules.
.DESCRIPTION
Checks required fields, scan policy, rollback plan, test evidence, and installs. Logs errors via structured log helper when available.
.PARAMETER EvidencePack
Hashtable representation of evidence pack.
.PARAMETER SchemaPath
Path to JSON schema for validation.
.EXAMPLE
$result = Test-EvidencePackCompleteness -EvidencePack $pack
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/10-evidence-pack-rules.md, docs/architecture/evidence-pack-schema.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Load-Schema {
    param([string]$SchemaPath)
    if (-not (Test-Path -Path $SchemaPath)) {
        throw "Schema missing: $SchemaPath"
    }
    return Get-Content -Path $SchemaPath -Raw | ConvertFrom-Json
}
function Validate-RequiredField {
    param($pack, $path)
    $segments = $path -split '\.'
    $node = $pack
    foreach ($segment in $segments) {
        if ($node -is [System.Collections.IDictionary] -and $node.ContainsKey($segment)) {
            $node = $node[$segment]
        }
        else {
            return $null
        }
    }
    return $node
}
function Test-EvidencePackCompleteness {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$EvidencePack,
        [string]$SchemaPath = (Join-Path $PSScriptRoot '..\..\config\evidence-pack-schema.json')
    )
    $schema = Load-Schema -SchemaPath $SchemaPath
    $errors = @()
    foreach ($field in $schema.required) {
        $value = Validate-RequiredField -pack $EvidencePack -path $field
        if ($null -eq $value -or ($value -is [string] -and $value -eq '')) {
            $errors += "Missing required field: $field"
        }
    }
    $artifactSigned = Validate-RequiredField -pack $EvidencePack -path 'artifact.signing.signed'
    if ($null -ne $artifactSigned -and -not $artifactSigned) {
        $errors += 'Artifact signing missing/false'
    }
    $criticalCount = 0
    $criticalValue = Validate-RequiredField -pack $EvidencePack -path 'vulnerability_scan.findings.critical'
    if ($null -ne $criticalValue) {
        $criticalCount = [int]$criticalValue
    }
    $policyDecision = Validate-RequiredField -pack $EvidencePack -path 'vulnerability_scan.policy_decision'
    if ($criticalCount -gt 0 -and $policyDecision -ne 'exception_granted') {
        $errors += "Critical vulnerabilities present without exception: $criticalCount"
    }
    $rollbackValidated = Validate-RequiredField -pack $EvidencePack -path 'rollback_plan.validated'
    if (-not $rollbackValidated) {
        $errors += 'Rollback plan not validated'
    }
    $testSuccesses = Validate-RequiredField -pack $EvidencePack -path 'test_evidence.successes'
    if (-not ($testSuccesses -gt 0)) {
        $errors += 'Ring 0 installs missing or zero success'
    }
    return [pscustomobject]@{
        IsValid = ($errors.Count -eq 0)
        Errors = $errors
    }
}
