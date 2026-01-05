# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Shared helpers for CLI command scripts.
.DESCRIPTION
    Provides utilities that normalize parameter payloads and enforce guardrails for connectors.
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/architecture/control-plane-design.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Resolve-Hashtable {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [object]$Input
    )

    if ($Input -is [hashtable]) {
        return $Input
    }

    $payload = if ($Input -is [string]) {
        $Input | ConvertFrom-Json
    }
    else {
        $Input
    }

    if (-not $payload) {
        return @{}
    }

    $table = @{}
    foreach ($prop in $payload.psobject.properties) {
        $table[$prop.Name] = $prop.Value
    }
    return $table
}
