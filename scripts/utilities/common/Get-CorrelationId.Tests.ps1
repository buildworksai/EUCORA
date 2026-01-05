# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Pester tests for Get-CorrelationId and Test-CorrelationId.
.DESCRIPTION
Validates formats, determinism, and validation logic for correlation IDs.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/control-plane-design.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Get-CorrelationId' {
    BeforeAll {
        . "$PSScriptRoot/Get-CorrelationId.ps1"
    }
    It 'Generates valid UUIDv4' {
        $uuid = Get-CorrelationId -Type uuid
        $uuid | Should -Match '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    }
    It 'Generates deployment prefix with date and hex' {
        $value = Get-CorrelationId -Type deployment -Seed 1001
        $value | Should -Match '^dp-[0-9]{8}-[0-9a-f]{4}$'
    }
    It 'Generates evidence prefix with hex' {
        $value = Get-CorrelationId -Type evidence -Seed 1002
        $value | Should -Match '^ep-[0-9a-f]{8}$'
    }
    It 'Generates CAB prefix with date' {
        $value = Get-CorrelationId -Type cab -Seed 1003
        $value | Should -Match '^cab-[0-9]{8}-[0-9a-f]{3}$'
    }
    It 'Deterministic output with seed' {
        $first = Get-CorrelationId -Type uuid -Seed 500
        $second = Get-CorrelationId -Type uuid -Seed 500
        $first | Should -Be $second
    }
}
Describe 'Test-CorrelationId' {
    BeforeAll {
        . "$PSScriptRoot/Get-CorrelationId.ps1"
    }
    It 'Validates deployment format' {
        Test-CorrelationId -CorrelationId 'dp-20260104-abcd' -Type deployment | Should -BeTrue
    }
    It 'Rejects invalid deployment prefix' {
        Test-CorrelationId -CorrelationId 'dp-202601-aa' -Type deployment | Should -BeFalse
    }
    It 'Validates CAB prefix' {
        Test-CorrelationId -CorrelationId 'cab-20260104-abc' -Type cab | Should -BeTrue
    }
    It 'Rejects random string for UUID' {
        Test-CorrelationId -CorrelationId 'invalid' -Type uuid | Should -BeFalse
    }
    It 'Accepts any string when Type any matches pattern' {
        Test-CorrelationId -CorrelationId 'abc-123' -Type any | Should -BeTrue
    }
}
