# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Lightweight health command for dapctl.
.DESCRIPTION
    Returns a simple status object and records a structured log entry; used to verify CLI plumbing.
.PARAMETER AuthToken
    Bearer token obtained from Initialize-Auth.
.NOTES
Version: 1.0
Author: Platform Engineering
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$AuthToken,

    [Parameter(Mandatory = $false)]
    [string[]]$Arguments
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../utilities/common/Get-CorrelationId.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"

Write-StructuredLog -Level 'Info' -Message 'Health command executed' -CorrelationId (Get-CorrelationId -Type uuid) -Metadata @{component = 'cli.health'}
return @{ status = 'healthy'; timestamp = (Get-Date).ToString('o') }
