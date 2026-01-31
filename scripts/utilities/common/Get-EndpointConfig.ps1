# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Retrieves endpoint configuration from centralized config file.
.DESCRIPTION
    Loads endpoint configuration from scripts/config/endpoints.json and provides
    helper functions to construct full URLs with parameter substitution.
.PARAMETER Service
    Service name (microsoft, intune, jamf, sccm, landscape, ansible)
.PARAMETER Endpoint
    Endpoint key name (e.g., "mobile_apps", "packages")
.PARAMETER Parameters
    Hashtable of parameters to substitute in endpoint URLs (e.g., @{app_id = "123"})
.EXAMPLE
    Get-EndpointConfig -Service "intune" -Endpoint "mobile_apps"
    Returns: "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps"
.EXAMPLE
    Get-EndpointConfig -Service "intune" -Endpoint "app_assignments" -Parameters @{app_id = "abc123"}
    Returns: "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/abc123/assignments"
.NOTES
    Version: 1.0
    Author: Platform Engineering
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('microsoft', 'intune', 'jamf', 'sccm', 'landscape', 'ansible', 'siem')]
    [string]$Service,

    [Parameter(Mandatory = $true)]
    [string]$Endpoint,

    [Parameter(Mandatory = $false)]
    [hashtable]$Parameters = @{}
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Load endpoint configuration
$ConfigPath = Join-Path $PSScriptRoot "../../config/endpoints.json"
if (-not (Test-Path $ConfigPath)) {
    throw "Endpoint configuration file not found: $ConfigPath"
}

$Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

# Get base URL for service
$BaseUrl = $null
if ($Service -eq 'microsoft') {
    $BaseUrl = $Config.endpoints.microsoft.graph_api_base
} elseif ($Service -eq 'intune') {
    $BaseUrl = $Config.endpoints.microsoft.graph_api_base
} else {
    # For other services, base URL comes from connector config
    # This function only returns the path
    $BaseUrl = ""
}

# Get endpoint path
$EndpointPath = $null
if ($Service -eq 'microsoft') {
    if (-not $Config.endpoints.microsoft.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'microsoft'"
    }
    $EndpointPath = $Config.endpoints.microsoft.$Endpoint
} elseif ($Service -eq 'intune') {
    if (-not $Config.endpoints.intune.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'intune'"
    }
    $EndpointPath = $Config.endpoints.intune.$Endpoint
} elseif ($Service -eq 'jamf') {
    if (-not $Config.endpoints.jamf.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'jamf'"
    }
    $EndpointPath = $Config.endpoints.jamf.$Endpoint
} elseif ($Service -eq 'sccm') {
    if (-not $Config.endpoints.sccm.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'sccm'"
    }
    $EndpointPath = $Config.endpoints.sccm.$Endpoint
} elseif ($Service -eq 'landscape') {
    if (-not $Config.endpoints.landscape.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'landscape'"
    }
    $EndpointPath = $Config.endpoints.landscape.$Endpoint
} elseif ($Service -eq 'ansible') {
    if (-not $Config.endpoints.ansible.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'ansible'"
    }
    $EndpointPath = $Config.endpoints.ansible.$Endpoint
} elseif ($Service -eq 'siem') {
    if (-not $Config.endpoints.siem.ContainsKey($Endpoint)) {
        throw "Endpoint '$Endpoint' not found for service 'siem'"
    }
    $EndpointPath = $Config.endpoints.siem.$Endpoint
}

# Substitute parameters in path
$FinalPath = $EndpointPath
foreach ($Key in $Parameters.Keys) {
    $Placeholder = "{$Key}"
    $Value = $Parameters[$Key]
    $FinalPath = $FinalPath -replace [regex]::Escape($Placeholder), $Value
}

# Construct full URL
# For SIEM, the endpoint path is already a full URL template, so return it directly
if ($Service -eq 'siem') {
    return $FinalPath
} elseif ($BaseUrl) {
    return "$BaseUrl$FinalPath"
} else {
    return $FinalPath
}

<#
.SYNOPSIS
    Gets timeout configuration for operations.
.PARAMETER Operation
    Operation type (default, upload, health_check, test_connection)
#>
function Get-EndpointTimeout {
    param(
        [Parameter(Mandatory = $false)]
        [ValidateSet('default', 'upload', 'health_check', 'test_connection')]
        [string]$Operation = 'default'
    )

    $ConfigPath = Join-Path $PSScriptRoot "../../config/endpoints.json"
    if (-not (Test-Path $ConfigPath)) {
        return 30  # Default fallback
    }

    $Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    return $Config.timeouts.$Operation
}

<#
.SYNOPSIS
    Gets retry configuration.
#>
function Get-RetryConfig {
    $ConfigPath = Join-Path $PSScriptRoot "../../config/endpoints.json"
    if (-not (Test-Path $ConfigPath)) {
        return @{
            max_attempts = 3
            initial_delay_ms = 1000
            max_delay_ms = 10000
            backoff_multiplier = 2
        }
    }

    $Config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    return @{
        max_attempts = $Config.retry.max_attempts
        initial_delay_ms = $Config.retry.initial_delay_ms
        max_delay_ms = $Config.retry.max_delay_ms
        backoff_multiplier = $Config.retry.backoff_multiplier
    }
}
