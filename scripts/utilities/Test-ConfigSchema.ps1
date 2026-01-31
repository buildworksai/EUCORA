# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Validate configuration file schema.

.DESCRIPTION
    Validates required fields in configuration JSON files at load time.
    Fails fast with clear error messages if validation fails.

.PARAMETER ConfigPath
    Path to configuration JSON file.

.PARAMETER SchemaPath
    Optional path to JSON schema file. If not provided, uses built-in schema.

.EXAMPLE
    Test-ConfigSchema -ConfigPath "scripts/config/production.json"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath,

    [Parameter(Mandatory = $false)]
    [string]$SchemaPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Required fields in production.json
$RequiredFields = @{
    "api" = @("endpoint", "version", "timeout_seconds")
    "connectors" = @("intune", "jamf", "sccm")
    "logging" = @("level", "format")
    "retry" = @("max_retries", "initial_delay_ms", "max_delay_ms")
}

function Test-ConfigField {
    param(
        [hashtable]$Config,
        [string]$Path,
        [string[]]$RequiredFields
    )

    $Errors = @()

    foreach ($Field in $RequiredFields) {
        $FullPath = if ($Path) { "$Path.$Field" } else { $Field }

        if (-not $Config.ContainsKey($Field)) {
            $Errors += "Missing required field: $FullPath"
        } elseif ($null -eq $Config[$Field]) {
            $Errors += "Required field is null: $FullPath"
        }
    }

    return $Errors
}

# Load configuration
if (-not (Test-Path $ConfigPath)) {
    throw "Configuration file not found: $ConfigPath"
}

try {
    $ConfigContent = Get-Content $ConfigPath -Raw | ConvertFrom-Json -AsHashtable
} catch {
    throw "Failed to parse configuration file: $($_.Exception.Message)"
}

# Validate required fields
$AllErrors = @()

foreach ($Section in $RequiredFields.Keys) {
    if (-not $ConfigContent.ContainsKey($Section)) {
        $AllErrors += "Missing required section: $Section"
        continue
    }

    $SectionErrors = Test-ConfigField -Config $ConfigContent[$Section] -Path $Section -RequiredFields $RequiredFields[$Section]
    $AllErrors += $SectionErrors
}

# Validate nested connector configs
if ($ConfigContent.ContainsKey("connectors")) {
    $ConnectorConfigs = @{
        "intune" = @("graph_endpoint", "requests_per_second")
        "jamf" = @("api_version", "page_size")
        "sccm" = @("use_constrained_delegation", "timeout_seconds")
    }

    foreach ($ConnectorName in $ConnectorConfigs.Keys) {
        if ($ConfigContent["connectors"].ContainsKey($ConnectorName)) {
            $ConnectorErrors = Test-ConfigField `
                -Config $ConfigContent["connectors"][$ConnectorName] `
                -Path "connectors.$ConnectorName" `
                -RequiredFields $ConnectorConfigs[$ConnectorName]
            $AllErrors += $ConnectorErrors
        }
    }
}

# Report errors
if ($AllErrors.Count -gt 0) {
    $ErrorMsg = "Configuration validation failed:`n" + ($AllErrors -join "`n")
    throw $ErrorMsg
}

Write-Verbose "Configuration schema validation passed: $ConfigPath"
return $true
