# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Displays CLI version metadata.
.DESCRIPTION
    Returns version, status, and config location for the CLI dispatcher.
.PARAMETER AuthToken
    Required to match command signature (not used).
.EXAMPLE
    Invoke-version.ps1 -AuthToken $token
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/planning/phase-3-connectors-prompt.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"
. "$PSScriptRoot/../../utilities/common/Get-ConfigValue.ps1"

$versionInfo = @{
    cli_version = 'v1.0'
    control_plane_api = Get-ConfigValue -Key 'control_plane.api_url'
    status = 'Design'
}
Write-StructuredLog -Level 'Info' -Message 'Version command executed' -CorrelationId (Get-CorrelationId -Type uuid)
return $versionInfo
