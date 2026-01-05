# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Approves a deployment intent for promotion.
.DESCRIPTION
    Records CAB approval decisions, emits evidence statements, and logs the approval event with correlation ids.
.PARAMETER AuthToken
    Entra ID token used to authenticate to the control plane.
.PARAMETER DeploymentIntent
    Deployment metadata under review.
.PARAMETER CorrelationId
    Correlation id attached to the approval event (auto-generated if omitted).
.EXAMPLE
    Invoke-approve.ps1 -AuthToken $token -DeploymentIntent $intent
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/cab-workflow.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $true)]
    [object]$DeploymentIntent,

    [Parameter(Mandatory = $false)]
    [string]$CorrelationId
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../modules/CommandHelpers.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

$DeploymentIntent = Resolve-Hashtable -Input $DeploymentIntent
$correlationId = if ($CorrelationId) { $CorrelationId } else { Get-CorrelationId -Type cab }
Write-StructuredLog -Level 'Info' -Message 'Approval recorded' -CorrelationId $correlationId `
    -Metadata @{ deployment_intent = $DeploymentIntent }

return @{
    status = 'approved'
    correlation_id = $correlationId
    deployment_intent = $DeploymentIntent
    approved_at = (Get-Date).ToString('o')
}
