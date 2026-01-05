# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Reports connector health and capabilities.
.DESCRIPTION
    Queries each connector to report readiness, idempotency status, and audit-worthy metadata.
.PARAMETER AuthToken
    Authentication token.
.EXAMPLE
    Invoke-connectors.ps1 -AuthToken $token
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

$statuses = Test-ConnectorConnection -AuthToken $AuthToken
Write-StructuredLog -Level 'Info' -Message 'Connectors command executed' -CorrelationId (Get-CorrelationId -Type uuid) `
    -Metadata @{ count = $statuses.Count }

return $statuses
