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
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

$results = Test-ConnectorConnection -AuthToken $AuthToken
Write-StructuredLog -Level 'Info' -Message 'Test-ConnectorConnection command executed' -CorrelationId (Get-CorrelationId -Type uuid)
return $results
