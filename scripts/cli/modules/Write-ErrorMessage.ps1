# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Emit structured error messages for dapctl.
.DESCRIPTION
    Writes a red console message and forwards the event to the structured log helper so every
    failure carries the correlation_id for audit purposes.
.PARAMETER Message
    Error message to display.
.NOTES
Version: 1.0
Author: Platform Engineering
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$logHelper = Join-Path $PSScriptRoot '..\..\utilities\logging\Write-StructuredLog.ps1'
. $logHelper
function Write-ErrorMessage {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [Parameter(Mandatory = $false)]
        [string]$CorrelationId
    )

    Write-Host "ERROR: $Message" -ForegroundColor Red
    Write-StructuredLog -Level 'Error' -Message $Message -CorrelationId $CorrelationId | Out-Null
}
