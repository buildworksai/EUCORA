# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Dumps config values sourced from scripts/config/settings.json.
.DESCRIPTION
    Enables safe inspection of control plane configuration, honoring environment overrides via Get-ConfigValue.
.PARAMETER AuthToken
    Authentication token.
.PARAMETER Key
    Optional dotted key path (e.g., control_plane.api_url) to retrieve.
.EXAMPLE
    Invoke-config.ps1 -AuthToken $token -Key control_plane.api_url
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: .agents/rules/12-documentation-rules.md
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $false)]
    [string]$Key
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../utilities/common/Get-ConfigValue.ps1"
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

try {
    if ($Key) {
        $value = Get-ConfigValue -Key $Key -Required
    }
    else {
        $settingsPath = (Join-Path $PSScriptRoot '..\..\config\settings.json')
        $value = Get-Content -Path $settingsPath -Raw | ConvertFrom-Json
    }

    $correlationId = Get-CorrelationId -Type uuid
    Write-StructuredLog -Level 'Info' -Message 'Config command executed' -CorrelationId $correlationId
    return $value
    exit 0
} catch {
    Write-StructuredLog -Level 'Error' -Message "Config command failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type uuid) `
        -Metadata @{ error = $_.Exception.Message; stack_trace = $_.ScriptStackTrace; key = $Key }
    exit 1
}
