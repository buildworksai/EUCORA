# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Export audit trail events for a correlation ID.
.DESCRIPTION
Queries event store JSON, filters by correlation ID/date range, formats output in JSON/CSV/HTML.
.PARAMETER CorrelationId
Correlation ID to export.
.PARAMETER Format
Output format: JSON, CSV, HTML.
.PARAMETER OutputPath
Optional file path; defaults to stdout object.
.PARAMETER StartDate
Filter start date.
.PARAMETER EndDate
Filter end date.
.PARAMETER EventStoreConnectionString
Path to event store file.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/control-plane-design.md, docs/infrastructure/siem-integration.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/Get-ConfigValue.ps1"
function Get-Events {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseSingularNouns', '', Justification = 'Function returns collection of events, plural noun is semantically correct')]
    param([string]$Path)
    $safe = [System.IO.Path]::GetFullPath($Path)
    $base = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\config'))
    if (-not $safe.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Path traversal not allowed: $Path" }
    if (-not (Test-Path -Path $safe)) { return @() }
    return (Get-Content -Path $safe -Raw | ConvertFrom-Json).events
}
function Export-AuditTrail {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$CorrelationId,
        [ValidateSet('JSON','CSV','HTML')]
        [string]$Format = 'JSON',
        [string]$OutputPath,
        [datetime]$StartDate,
        [datetime]$EndDate,
        [string]$EventStoreConnectionString
    )
    if ($EventStoreConnectionString) {
        $path = $EventStoreConnectionString
    }
    else {
        $path = Get-ConfigValue -Key 'event_store.connection_string' -Required
    }
    $events = Get-Events -Path $path | Where-Object { $_.correlation_id -eq $CorrelationId }
    if ($StartDate) { $events = $events | Where-Object { [datetime]$_.timestamp -ge $StartDate } }
    if ($EndDate) { $events = $events | Where-Object { [datetime]$_.timestamp -le $EndDate } }
    $events = $events | Sort-Object {[datetime]$_.timestamp}
    switch ($Format) {
        'JSON' {
            $output = $events | ConvertTo-Json -Depth 5
        }
        'CSV' {
            $output = $events | ConvertTo-Csv -NoTypeInformation
        }
        'HTML' {
            $html = $events | ConvertTo-Html -Property event_id, correlation_id, event_type, timestamp, actor, outcome, details
            $output = $html
        }
    }
    if ($OutputPath) {
        $dir = [System.IO.Path]::GetDirectoryName($OutputPath)
        if (-not (Test-Path -Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Set-Content -Path $OutputPath -Value $output
        return $OutputPath
    }
    return $output
}
