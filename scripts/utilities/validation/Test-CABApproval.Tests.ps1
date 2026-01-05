# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Tests for CAB approval validator.
.DESCRIPTION
Ensures approvals, expiry, conditions handling.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/05-cab-approval-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Test-CABApproval' {
    BeforeAll {
        . "$PSScriptRoot/Test-CABApproval.ps1"
    }
    BeforeEach {
        $script:TempPath = [System.IO.Path]::GetTempFileName()
    }
    AfterEach {
        Remove-Item -Path $script:TempPath -Force -ErrorAction SilentlyContinue
    }
    It 'Returns true for approved and not expired' {
        $record = @{ cab = @(@{ approval_id = 'cab-001'; status = 'approved'; expiry = (Get-Date).AddDays(5); conditions = @('test') }) }
        $record | ConvertTo-Json -Depth 5 | Set-Content -Path $script:TempPath
        $result = Test-CABApproval -ApprovalId 'cab-001' -EventStoreConnectionString $script:TempPath -CurrentTime (Get-Date)
        $result.IsApproved | Should -BeTrue
    }
    It 'Returns false for denied' {
        $record = @{ cab = @(@{ approval_id = 'cab-002'; status = 'denied'; expiry = (Get-Date).AddDays(5); conditions = @() }) }
        $record | ConvertTo-Json -Depth 5 | Set-Content -Path $script:TempPath
        $result = Test-CABApproval -ApprovalId 'cab-002' -EventStoreConnectionString $script:TempPath -CurrentTime (Get-Date)
        $result.IsApproved | Should -BeFalse
    }
    It 'Returns false for expired approval' {
        $record = @{ cab = @(@{ approval_id = 'cab-003'; status = 'approved'; expiry = (Get-Date).AddDays(-1); conditions = @() }) }
        $record | ConvertTo-Json -Depth 5 | Set-Content -Path $script:TempPath
        $result = Test-CABApproval -ApprovalId 'cab-003' -EventStoreConnectionString $script:TempPath -CurrentTime (Get-Date)
        $result.IsApproved | Should -BeFalse
    }
    It 'Returns false when missing' {
        $empty = @{ cab = @() } | ConvertTo-Json -Depth 5
        Set-Content -Path $script:TempPath -Value $empty
        $result = Test-CABApproval -ApprovalId 'cab-xxx' -EventStoreConnectionString $script:TempPath -CurrentTime (Get-Date)
        $result.Status | Should -Be 'missing'
    }
}
