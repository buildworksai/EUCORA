# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Pester tests for Invoke-RetryWithBackoff.
.DESCRIPTION
Covers retry behavior, transient vs permanent errors, and correlation ID logging.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Invoke-RetryWithBackoff' {
    BeforeAll {
        . "$PSScriptRoot/Invoke-RetryWithBackoff.ps1"
    }
    BeforeEach {
        $scriptBlockCalls = 0
        Mock -CommandName Start-Sleep {
            param($Seconds)
            # Use Seconds parameter to avoid unused parameter warning
            $null = $Seconds
            $scriptBlockCalls++
        } -Verifiable
    }
    It 'Returns result on first attempt without sleep' {
        $result = Invoke-RetryWithBackoff -ScriptBlock { return 'ok' }
        $result | Should -Be 'ok'
        Assert-MockCalled Start-Sleep -Times 0
    }
    It 'Retries on transient error and succeeds' {
        $attempt = 0
        $scriptBlock = {
            $attempt++
            if ($attempt -lt 2) {
                throw [System.Net.WebException]::new('Rate limit', [System.Net.WebExceptionStatus]::Timeout)
            }
            return 'done'
        }
        $result = Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -TransientErrorCodes @('WebException') -BaseSeconds 1 -MaxBackoffSeconds 1 -MaxAttempts 3
        $result | Should -Be 'done'
    }
    It 'Throws after max attempts' {
        $scriptBlock = { throw [System.Net.WebException]::new('Timeout', [System.Net.WebExceptionStatus]::Timeout) }
        { Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -MaxAttempts 2 -TransientErrorCodes @('TimeoutException') -BaseSeconds 0 } | Should -Throw
    }
    It 'Does not retry on permanent error' {
        $scriptBlock = { throw [System.Exception]::new('Bad request') }
        { Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -TransientErrorCodes @('TimeoutException') } | Should -Throw
        Assert-MockCalled Start-Sleep -Times 0
    }
    It 'Logs correlation ID in output' {
        $scriptBlock = { return 'ok' }
        $output = Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -CorrelationId 'dp-20260104-0001' | Out-String
        $output | Should -Match 'correlation_id=dp-20260104-0001'
    }
}
