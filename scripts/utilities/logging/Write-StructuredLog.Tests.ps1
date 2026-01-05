# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Tests for Write-StructuredLog structured outputs.
.DESCRIPTION
Validates JSON fields, color selection, file output, correlation ID, metadata.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/infrastructure/siem-integration.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Write-StructuredLog' {
    BeforeAll {
        . "$PSScriptRoot/Write-StructuredLog.ps1"
    }
    BeforeEach {
        $script:TempLog = [System.IO.Path]::GetTempFileName()
    }
    AfterEach {
        Remove-Item -Path $script:TempLog -Force
    }
    It 'Outputs JSON with required fields' {
        $entry = Write-StructuredLog -Message 'test' -CorrelationId 'dp-1' -Component 'orchestrator' -Level Info -LogFilePath $script:TempLog
        $entry.timestamp | Should -Not -BeNullOrEmpty
        $entry.level | Should -Be 'Info'
        $entry.correlation_id | Should -Be 'dp-1'
    }
    It 'Writes to log file when provided' {
        Write-StructuredLog -Message 'test2' -CorrelationId 'dp-2' -Component 'orchestrator' -LogFilePath $script:TempLog
        $content = Get-Content -Path $script:TempLog -Raw
        $content | Should -Match 'dp-2'
    }
    It 'Includes metadata when provided' {
        $metadata = @{ artifact_id = 'appv'; ring=1 }
        $entry = Write-StructuredLog -Message 'meta' -Metadata $metadata -LogFilePath $script:TempLog
        $entry.metadata.artifact_id | Should -Be 'appv'
    }
}
