# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Checks if a correlation ID already exists in the event store (idempotency guard).
.DESCRIPTION
`Test-IdempotencyKey` validates the correlation ID, queries the configured event store, caches results when requested, and returns true if the ID already exists.
.PARAMETER CorrelationId
The correlation ID to check (validated via Test-CorrelationId).
.PARAMETER EventStoreConnectionString
Optional path/connection string pointing to event store data.
.PARAMETER UseCache
Switch to cache previous results and avoid repeated queries.
.EXAMPLE
Test-IdempotencyKey -CorrelationId dp-20260104-0001 -EventStoreConnectionString './config/event-store.json'
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/control-plane-design.md, .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:IdempotencyCache = @{}
. "$PSScriptRoot/Get-CorrelationId.ps1"
. "$PSScriptRoot/Get-ConfigValue.ps1"
function Get-EventStoreRecords {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of records, plural noun is semantically correct')]
    param(
        [string]$Path
    )
    if (-not (Test-Path -Path $Path)) {
        return @()
    }
    $content = Get-Content -Path $Path -Raw
    $json = $content | ConvertFrom-Json
    return @($json.events)
}
function Normalize-Path {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '', Justification = 'Normalize is an acceptable verb for path operations')]
    param([string]$InputPath)
    $full = [System.IO.Path]::GetFullPath($InputPath)
    $base = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\config'))
    if (-not $full.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path traversal detected: $InputPath"
    }
    return $full
}
function Test-IdempotencyKey {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [ValidateScript({ Test-CorrelationId -CorrelationId $_ })]
        [string]$CorrelationId,
        [string]$EventStoreConnectionString,
        [switch]$UseCache
    )
    if ($UseCache -and $script:IdempotencyCache.ContainsKey($CorrelationId)) {
        return $script:IdempotencyCache[$CorrelationId]
    }
    $path = $EventStoreConnectionString
    if (-not $path) {
        $path = Get-ConfigValue -Key 'event_store.connection_string' -Required
    }
    $safePath = Normalize-Path -InputPath $path
    $records = Get-EventStoreRecords -Path $safePath
    $exists = $false
    foreach ($record in $records) {
        if ($record.correlation_id -eq $CorrelationId) {
            $exists = $true
            break
        }
    }
    if ($UseCache) {
        $script:IdempotencyCache[$CorrelationId] = $exists
    }
    return $exists
}
