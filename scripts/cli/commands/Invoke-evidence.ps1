# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Validates and records evidence packs for CAB submissions.
.DESCRIPTION
    Ensures all mandatory evidence pack sections are present, logs validation outcomes, and surfaces missing fields.
.PARAMETER AuthToken
    Entra ID token for the control plane.
.PARAMETER EvidencePack
    Hashtable matching the evidence pack schema.
.EXAMPLE
    Invoke-evidence.ps1 -AuthToken $token -EvidencePack $pack
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: .agents/rules/10-evidence-pack-rules.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $true)]
    [object]$EvidencePack
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../modules/CommandHelpers.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

$EvidencePack = Resolve-Hashtable -Input $EvidencePack

$requiredFields = @(
    'evidence_pack_id',
    'deployment_intent_id',
    'artifact',
    'sbom',
    'vulnerability_scan',
    'rollout_plan',
    'rollback_plan',
    'test_evidence',
    'risk_assessment'
)

$missing = $requiredFields | Where-Object { -not $EvidencePack.ContainsKey($_) -or (-not $EvidencePack[$_]) }

if ($missing) {
    $message = "Evidence pack missing required fields: $($missing -join ', ')"
    Write-StructuredLog -Level 'Error' -Message $message -CorrelationId (Get-CorrelationId -Type evidence)
    throw $message
}

Write-StructuredLog -Level 'Info' -Message 'Evidence pack validation passed' -CorrelationId (Get-CorrelationId -Type evidence)
return @{
    status = 'evidence_validated'
    evidence_pack_id = $EvidencePack.evidence_pack_id
}
