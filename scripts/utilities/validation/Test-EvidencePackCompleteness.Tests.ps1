# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Pester tests for evidence pack validation.
.DESCRIPTION
Covers schema presence, missing fields, signing, critical findings, rollback, and installs.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/evidence-pack-schema.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Test-EvidencePackCompleteness' {
    BeforeAll {
        . "$PSScriptRoot/Test-EvidencePackCompleteness.ps1"
        $script:TempSchema = [System.IO.Path]::GetTempFileName()
        $schema = @{
            required = @('artifact','rollback_plan','test_evidence')
            properties = @{ artifact = @{ signing = @{ signed = @{ } } } }
        } | ConvertTo-Json -Depth 5
        Set-Content -Path $script:TempSchema -Value $schema
    }
    AfterAll {
        Remove-Item -Path $script:TempSchema -Force
    }
    It 'Returns valid for complete pack' {
        $pack = @{
            artifact = @{ signing = @{ signed = $true } }
            vulnerability_scan = @{ policy_decision = 'pass'; findings = @{ critical = 0 } }
            rollback_plan = @{ validated = $true }
            test_evidence = @{ successes = 1 }
        }
        $result = Test-EvidencePackCompleteness -EvidencePack $pack -SchemaPath $script:TempSchema
        $result.IsValid | Should -BeTrue
    }
    It 'Reports missing required field' {
        $pack = @{}
        $result = Test-EvidencePackCompleteness -EvidencePack $pack -SchemaPath $script:TempSchema
        $result.IsValid | Should -BeFalse
    }
    It 'Errors unsigned artifact' {
        $pack = @{
            artifact = @{ signing = @{ signed = $false } }
            vulnerability_scan = @{ policy_decision = 'pass'; findings = @{ critical = 0 } }
            rollback_plan = @{ validated = $true }
            test_evidence = @{ successes = 1 }
        }
        $result = Test-EvidencePackCompleteness -EvidencePack $pack -SchemaPath $script:TempSchema
        $result.Errors | Should -Contain 'Artifact signing missing/false'
    }
    It 'Flags critical vulnerability without exception' {
        $pack = @{
            artifact = @{ signing = @{ signed = $true } }
            vulnerability_scan = @{ policy_decision = 'pass'; findings = @{ critical = 2 } }
            rollback_plan = @{ validated = $true }
            test_evidence = @{ successes = 1 }
        }
        $result = Test-EvidencePackCompleteness -EvidencePack $pack -SchemaPath $script:TempSchema
        $result.Errors | Should -Contain 'Critical vulnerabilities present without exception: 2'
    }
    It 'Requires rollback validation' {
        $pack = @{
            artifact = @{ signing = @{ signed = $true } }
            vulnerability_scan = @{ policy_decision = 'pass'; findings = @{ critical = 0 } }
            rollback_plan = @{ validated = $false }
            test_evidence = @{ successes = 1 }
        }
        $result = Test-EvidencePackCompleteness -EvidencePack $pack -SchemaPath $script:TempSchema
        $result.Errors | Should -Contain 'Rollback plan not validated'
    }
    It 'Requires test evidence successes > 0' {
        $pack = @{ artifact = @{ signing = @{ signed = $true } }; vulnerability_scan = @{ policy_decision = 'pass'; findings = @{ critical = 0 } }; rollback_plan = @{ validated = $true }; test_evidence = @{ successes = 0 } }
        $result = Test-EvidencePackCompleteness -EvidencePack $pack -SchemaPath $script:TempSchema
        $result.Errors | Should -Contain 'Ring 0 installs missing or zero success'
    }
}
