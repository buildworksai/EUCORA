# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Pester suite for Test-IdempotencyKey.
.DESCRIPTION
Ensures idempotency checking honors cache, validation, and event store data.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/control-plane-design.md, .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Test-IdempotencyKey' {
    BeforeAll {
        . "$PSScriptRoot/Get-CorrelationId.ps1"
        . "$PSScriptRoot/Test-IdempotencyKey.ps1"
        $script:EventStoreDir = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\config\tests\event-store'))
        New-Item -ItemType Directory -Path $script:EventStoreDir -Force | Out-Null
    }
    BeforeEach {
        $script:TestEventStorePath = Join-Path $script:EventStoreDir ("eventstore-$([guid]::NewGuid()).json")
        $json = @{ events = @() } | ConvertTo-Json -Depth 3
        Set-Content -Path $script:TestEventStorePath -Value $json
    }
    AfterEach {
        Remove-Item -Path $script:TestEventStorePath -Force
    }
    It 'Returns false for new correlation ID' {
        $result = Test-IdempotencyKey -CorrelationId (Get-CorrelationId -Type uuid -Seed 1) -EventStoreConnectionString $script:TestEventStorePath
        $result | Should -BeFalse
    }
    It 'Returns true for existing correlation ID' {
        $id = 'dp-20260104-abcd'
        $json = @{ events = @(@{ correlation_id = $id }) } | ConvertTo-Json -Depth 3
        Set-Content -Path $script:TestEventStorePath -Value $json
        $result = Test-IdempotencyKey -CorrelationId $id -EventStoreConnectionString $script:TestEventStorePath
        $result | Should -BeTrue
    }
    It 'Caches results when UseCache is present' {
        $id = 'dp-20260104-cache'
        $json = @{ events = @(@{ correlation_id = $id }) } | ConvertTo-Json -Depth 3
        Set-Content -Path $script:TestEventStorePath -Value $json
        Mock -CommandName Get-Content -MockWith { Set-Content -Path $script:TestEventStorePath -Value $json; $json } -Verifiable
        Test-IdempotencyKey -CorrelationId $id -EventStoreConnectionString $script:TestEventStorePath -UseCache | Out-Null
        Test-IdempotencyKey -CorrelationId $id -EventStoreConnectionString $script:TestEventStorePath -UseCache | Out-Null
        Assert-MockCalled Get-Content -Times 1
    }
    It 'Rejects invalid correlation ID format' {
        { Test-IdempotencyKey -CorrelationId 'invalid!' -EventStoreConnectionString $script:TestEventStorePath } | Should -Throw
    }
}
