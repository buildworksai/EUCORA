# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Write-ErrorMessage' {
    BeforeAll {
        $upOne = Join-Path $PSScriptRoot '..'
        $upTwo = Join-Path $upOne '..'
        $loggingHelperPath = Join-Path (Join-Path (Join-Path $upTwo 'utilities') 'logging') 'Write-StructuredLog.ps1'
        . (Resolve-Path $loggingHelperPath).Path
        $modulePath = Join-Path $PSScriptRoot 'Write-ErrorMessage.ps1'
        . (Resolve-Path $modulePath).Path
        Mock -CommandName Write-StructuredLog -MockWith {
            param($Message, $Level, $CorrelationId, $Component, $Metadata, $LogFilePath)
        } -Verifiable
    }
    It 'writes error message and logs' {
        { Write-ErrorMessage -Message 'boom' -CorrelationId 'dp-1' } | Should -Not -Throw
        Assert-MockCalled Write-StructuredLog -Times 1 -Exactly
    }
}
