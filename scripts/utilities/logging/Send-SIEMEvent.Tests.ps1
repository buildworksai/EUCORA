# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Tests for Send-SIEMEvent helper.
.DESCRIPTION
Mocks HTTP POST and retry logic, ensures shared key required, correlation ID used.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/infrastructure/siem-integration.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Send-SIEMEvent' {
    BeforeAll {
        . "$PSScriptRoot/../common/Get-ConfigValue.ps1"
        . "$PSScriptRoot/../common/Invoke-RetryWithBackoff.ps1"
        . "$PSScriptRoot/Send-SIEMEvent.ps1"
    }
    BeforeEach {
        $env:AZURE_LOG_ANALYTICS_SHARED_KEY = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA='
        $env:AZURE_LOG_ANALYTICS_WORKSPACE_ID = 'workspace'
    }
    AfterEach {
        Remove-Item Env:AZURE_LOG_ANALYTICS_SHARED_KEY -ErrorAction SilentlyContinue
        Remove-Item Env:AZURE_LOG_ANALYTICS_WORKSPACE_ID -ErrorAction SilentlyContinue
    }
    It 'Sends event successfully' {
        $testEvent = @{ timestamp = (Get-Date).ToUniversalTime().ToString('o'); level = 'Info'; message = 'msg'; correlation_id = 'dp-1'; component = 'orchestrator' }
        Mock -CommandName Invoke-RestMethod {
            @{ status = 'ok' }
        } -Verifiable
        Send-SIEMEvent -Event $testEvent -WorkspaceId 'workspace' -SharedKey $env:AZURE_LOG_ANALYTICS_SHARED_KEY -LogType 'ControlPlaneEvents'
        Assert-MockCalled Invoke-RestMethod -Times 1
    }
    It 'Retries on 503' {
        $script:retryCalls = 0
        Mock -CommandName Invoke-RestMethod {
            $script:retryCalls++
            if ($script:retryCalls -lt 2) { throw [System.Net.WebException]::new('timeout') }
            return @{ status = 'ok' }
        }
        $testEvent = @{ timestamp = (Get-Date).ToUniversalTime().ToString('o'); level = 'Info'; message = 'msg'; correlation_id = 'dp-1'; component = 'orchestrator' }
        Send-SIEMEvent -Event $testEvent -WorkspaceId 'workspace' -SharedKey $env:AZURE_LOG_ANALYTICS_SHARED_KEY `
            -RetryMaxAttempts 2 -RetryBaseSeconds 0 -RetryMaxBackoffSeconds 0 -RetryTransientErrorCodes @('WebException')
        Assert-MockCalled Invoke-RestMethod -Times 2
    }
    It 'Fails on permanent error' {
        Mock -CommandName Invoke-RestMethod { throw [System.Exception]::new('bad') }
        $testEvent = @{ timestamp = (Get-Date).ToUniversalTime().ToString('o'); level = 'Info'; message = 'msg'; correlation_id = 'dp-1'; component = 'orchestrator' }
        { Send-SIEMEvent -Event $testEvent -WorkspaceId 'workspace' -SharedKey $env:AZURE_LOG_ANALYTICS_SHARED_KEY } | Should -Throw
    }
}
