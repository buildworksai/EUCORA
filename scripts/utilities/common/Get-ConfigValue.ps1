# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Retrieves configuration values from settings or environment with caching and validation.
.DESCRIPTION
`Get-ConfigValue` loads JSON from the config directory, caches it, supports nested keys (dot notation), and falls back to environment variables when a key is missing.
.PARAMETER Key
Dot-delimited path (e.g., control_plane.api_url).
.PARAMETER ConfigPath
Path to configuration JSON (defaults to scripts/config/settings.json).
.PARAMETER DefaultValue
Value returned when key is missing and not required.
.PARAMETER Required
Switch to throw if the key cannot be resolved.
.EXAMPLE
$apiUrl = Get-ConfigValue -Key 'control_plane.api_url' -Required
Write-Output "API URL: $apiUrl"
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: documentation-rules.md, control-plane-design.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:ConfigCache = $null
function Normalize-ConfigPath {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '', Justification = 'Normalize is an acceptable verb for path operations')]
    param([string]$InputPath)
    $full = [System.IO.Path]::GetFullPath($InputPath)
    $base = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\config'))
    if (-not $full.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Config path traversal not allowed: $InputPath"
    }
    return $full
}
function Load-Config {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '', Justification = 'Load is an acceptable verb for configuration operations')]
    param([string]$ConfigPath)
    $safePath = Normalize-ConfigPath -InputPath $ConfigPath
    if (-not (Test-Path -Path $safePath)) {
        throw "Configuration file missing: $safePath"
    }
    return Get-Content -Path $safePath -Raw | ConvertFrom-Json -Depth 5 -AsHashtable
}
function Clear-ConfigCache {
    $script:ConfigCache = $null
}
function Resolve-Key {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseDeclaredVarsMoreThanAssignments', '', Justification = 'Variable is used recursively in function')]
    param([object]$Node, [string[]]$Segments)
    if (-not $Segments) { return $Node }
    $property = $Segments[0]
    if ($Node -is [System.Collections.IDictionary] -and $Node.ContainsKey($property)) {
        if ($Segments.Count -gt 1) {
            $remainingSegments = $Segments[1..($Segments.Count - 1)]
        }
        else {
            $remainingSegments = @()
        }
        return Resolve-Key -Node $Node[$property] -Segments $remainingSegments
    }
    return $null
}
function Get-ConfigValue {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Key,
        [string]$ConfigPath = (Join-Path $PSScriptRoot '..\..\config\settings.json'),
        [object]$DefaultValue,
        [switch]$Required
    )
    if (-not $script:ConfigCache) {
        $script:ConfigCache = Load-Config -ConfigPath $ConfigPath
    }
    $segments = $Key.Split('.')
    $value = Resolve-Key -Node $script:ConfigCache -Segments $segments
    if ($null -eq $value) {
        $envKey = ($Key -replace '\.', '_').ToUpper()
        try {
            $envValue = [System.Environment]::GetEnvironmentVariable($envKey, 'Process')
        }
        catch { $envValue = $null }
        if ($envValue) {
            return $envValue
        }
        if ($PSBoundParameters.ContainsKey('DefaultValue')) {
            return $DefaultValue
        }
        if ($Required) {
            throw \"Missing configuration key: $Key\"
        }
        return $null
    }
    return $value
}
