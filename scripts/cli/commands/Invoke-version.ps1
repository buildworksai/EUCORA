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
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"
. "$PSScriptRoot/../../utilities/common/Get-ConfigValue.ps1"

try {
    $versionInfo = @{
        cli_version = 'v1.0'
        control_plane_api = Get-ConfigValue -Key 'control_plane.api_url'
        status = 'Design'
    }
    $correlationId = Get-CorrelationId -Type uuid
    Write-StructuredLog -Level 'Info' -Message 'Version command executed' -CorrelationId $correlationId
    return $versionInfo
    exit 0
} catch {
    Write-StructuredLog -Level 'Error' -Message "Version command failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type uuid) `
        -Metadata @{ error = $_.Exception.Message; stack_trace = $_.ScriptStackTrace }
    exit 1
}
