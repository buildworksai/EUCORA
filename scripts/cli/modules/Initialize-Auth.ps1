# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Obtain Entra ID bearer token for dapctl.
.DESCRIPTION
    Preferred source: environment variable `DAPCTL_AUTH_TOKEN`. If missing, the module attempts to call
    `az account get-access-token` for the Microsoft Graph resource. Fallbacks throw a clear error.
.PARAMETER None
.EXAMPLE
    $authToken = Initialize-Auth
    Write-Output "Token: $authToken"
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: .agents/rules/02-control-plane-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Initialize-Auth {
    param()
    if ($env:DAPCTL_AUTH_TOKEN -and $env:DAPCTL_AUTH_TOKEN -ne '') {
        return $env:DAPCTL_AUTH_TOKEN
    }
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        throw 'Authentication failed: DAPCTL_AUTH_TOKEN missing and Azure CLI (az) not installed.'
    }
    try {
        $tokenJson = az account get-access-token --resource 'https://graph.microsoft.com' --output json | ConvertFrom-Json
        if (-not $tokenJson.accessToken) {
            throw 'Authentication failed: az did not return accessToken.'
        }
        return $tokenJson.accessToken
    }
    catch {
        throw "Authentication failed: $($_.Exception.Message)"
    }
}
