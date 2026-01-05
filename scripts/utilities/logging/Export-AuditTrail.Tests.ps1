# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Tests for audit trail exports.
.DESCRIPTION
Covers JSON/CSV/HTML outputs and date filtering.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/infrastructure/siem-integration.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Export-AuditTrail' {
    BeforeAll {
        . "$PSScriptRoot/Export-AuditTrail.ps1"
        $script:TestDataDir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\config\tests\audit'))
        New-Item -ItemType Directory -Path $script:TestDataDir -Force | Out-Null
        $script:TempPath = Join-Path $script:TestDataDir ("audit-$([guid]::NewGuid()).json")
        $data = @{
            events = @(
                @{ correlation_id = 'dp-1'; event_id = 'e1'; timestamp = (Get-Date).AddMinutes(-5).ToString('o'); event_type = 'publish'; actor = 'user'; outcome = 'success'; details = 'ok' },
                @{ correlation_id = 'dp-1'; event_id = 'e2'; timestamp = (Get-Date).AddMinutes(-1).ToString('o'); event_type = 'approve'; actor = 'cab'; outcome = 'approved'; details = 'ok' }
            )
        } | ConvertTo-Json -Depth 5
        Set-Content -Path $script:TempPath -Value $data
    }
    AfterAll {
        Remove-Item -Path $script:TempPath -Force
    }
    It 'Exports JSON' {
        $output = Export-AuditTrail -CorrelationId 'dp-1' -Format JSON -EventStoreConnectionString $script:TempPath
        $entries = $output | ConvertFrom-Json
        $entries.event_id | Should -Contain 'e1'
    }
    It 'Exports CSV' {
        $output = Export-AuditTrail -CorrelationId 'dp-1' -Format CSV -EventStoreConnectionString $script:TempPath
        $rows = $output | ConvertFrom-Csv
        $rows.event_type | Should -Contain 'publish'
    }
    It 'Exports HTML' {
        $output = Export-AuditTrail -CorrelationId 'dp-1' -Format HTML -EventStoreConnectionString $script:TempPath
        ($output -join "`n") | Should -Match '(?i)<table'
    }
    It 'Filters by date range' {
        $start = (Get-Date).AddMinutes(-2)
        $output = Export-AuditTrail -CorrelationId 'dp-1' -Format JSON -StartDate $start -EventStoreConnectionString $script:TempPath
        $entries = $output | ConvertFrom-Json
        $entries.event_id | Should -BeExactly @('e2')
    }
}
