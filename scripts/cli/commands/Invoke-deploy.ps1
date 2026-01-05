# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Deploys an application via the control plane connectors.
.DESCRIPTION
    Orchestrates Publish-Application with idempotent correlation ids and logs the intent before handing the request to execution-plane adapters.
.PARAMETER AuthToken
    Entra ID bearer token issued to dapctl.
.PARAMETER DeploymentIntent
    Hashtable representing the deployment metadata (app name, ring, package path, detection rules, etc.).
.PARAMETER CorrelationId
    Optional correlation id override (default: generated deployment id).
.EXAMPLE
    Invoke-deploy.ps1 -AuthToken $token -DeploymentIntent $intent
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/planning/phase-3-connectors-prompt.md
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
. "$PSScriptRoot/../modules/RiskModel.ps1"
. "$PSScriptRoot/../../connectors/ConnectorManager.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

$DeploymentIntent = Resolve-Hashtable -Input $DeploymentIntent
$correlationId = if ($CorrelationId) { $CorrelationId } else { Get-CorrelationId -Type deployment }
$result = Publish-Application -DeploymentIntent $DeploymentIntent -CorrelationId $correlationId

Write-StructuredLog -Level 'Info' -Message 'Deploy command executed' -CorrelationId $correlationId `
    -Metadata @{ deployment_intent = $DeploymentIntent; command = 'deploy' }

return $result
