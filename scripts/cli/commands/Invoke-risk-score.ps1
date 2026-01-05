# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Computes a deterministic risk score for a deployment intent.
.DESCRIPTION
    Applies weights and normalization defined in risk_model_v1.0 to calculate a 0-100 risk score and logs the outcome for audit.
.PARAMETER AuthToken
    Entra ID bearer token.
.PARAMETER DeploymentIntent
    Deployment metadata including `Factors` hashtable (each 0.0-1.0).
.EXAMPLE
    Invoke-risk-score.ps1 -AuthToken $token -DeploymentIntent @{ Factors = @{ privilege_impact = 1.0 } }
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/risk-model.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $true)]
    [object]$DeploymentIntent
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../modules/CommandHelpers.ps1"
. "$PSScriptRoot/../modules/RiskModel.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

$DeploymentIntent = Resolve-Hashtable -Input $DeploymentIntent
$factors = if ($DeploymentIntent.ContainsKey('Factors')) { $DeploymentIntent.Factors } else { @{} }
$riskScore = Calculate-RiskScore -Factors $factors
$model = Get-RiskModel

Write-StructuredLog -Level 'Info' -Message 'Risk score computed' -CorrelationId (Get-CorrelationId -Type uuid) `
    -Metadata @{ factors = $factors; score = $riskScore }

return @{
    risk_score = $riskScore
    version = $model.version
    source = 'risk_model_v1.0'
}
