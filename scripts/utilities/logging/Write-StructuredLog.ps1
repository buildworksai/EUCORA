# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Write structured JSON logs to console and optional log file.
.DESCRIPTION
Outputs timestamped JSON entries with level, message, correlation_id, component, and metadata. Writes to console (colored) and optionally to a log file. Thread-safe via semaphore.
.PARAMETER Message
Log message text (mandatory).
.PARAMETER Level
Log level (Debug/Info/Warning/Error/Critical).
.PARAMETER CorrelationId
Correlation ID for audit tracing.
.PARAMETER Component
Component emitting log.
.PARAMETER Metadata
Additional context as hashtable.
.PARAMETER LogFilePath
Optional file path for log archival.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/infrastructure/siem-integration.md, .agents/rules/10-evidence-pack-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:LogLock = New-Object System.Threading.SemaphoreSlim(1,1)
function Write-StructuredLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [ValidateSet('Debug','Info','Warning','Error','Critical')]
        [string]$Level = 'Info',
        [string]$CorrelationId,
        [string]$Component,
        [hashtable]$Metadata,
        [string]$LogFilePath
    )
    $timestamp = (Get-Date).ToUniversalTime().ToString('o')
    $entry = [ordered]@{
        timestamp = $timestamp
        level = $Level
        message = $Message
        correlation_id = $CorrelationId
        component = $Component
        metadata = $Metadata
    }
    $json = $entry | ConvertTo-Json -Depth 5
    $color = 'Cyan'
    switch ($Level) {
        'Warning' { $color = 'Yellow' }
        'Error' { $color = 'Red' }
        'Critical' { $color = 'Magenta' }
        'Debug' { $color = 'DarkGray' }
    }
    $script:LogLock.Wait()
    try {
        Write-Host $json -ForegroundColor $color
        if ($LogFilePath) {
            $safePath = [System.IO.Path]::GetFullPath($LogFilePath)
            $dir = [System.IO.Path]::GetDirectoryName($safePath)
            if (-not (Test-Path -Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
            Add-Content -Path $safePath -Value $json
        }
    }
    finally {
        $script:LogLock.Release() | Out-Null
    }
    return $entry
}
