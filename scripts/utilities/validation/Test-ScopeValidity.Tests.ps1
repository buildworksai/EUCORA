# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Tests for scope validation helper.
.DESCRIPTION
Ensures subset checks and CAB gating behavior.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/09-rbac-enforcement-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Test-ScopeValidity' {
    BeforeAll {
        . "$PSScriptRoot/Test-ScopeValidity.ps1"
    }
    It 'Validates matching scopes' {
        $res = Test-ScopeValidity -TargetScope @{ acquisition='A'; business_unit='BU'; site='S' } -PublisherScope @{ acquisition='A'; business_unit='BU'; site='S' } -AppScope @{ acquisition='A'; business_unit='BU'; site='S' }
        $res.IsValid | Should -BeTrue
    }
    It 'Rejects when target exceeds publisher' {
        $res = Test-ScopeValidity -TargetScope @{ acquisition='A2'; business_unit='BU'; site='S' } -PublisherScope @{ acquisition='A1'; business_unit='BU'; site='S' } -AppScope @{ acquisition='A2'; business_unit='BU'; site='S' }
        $res.Errors | Should -Contain 'Target scope exceeds publisher for acquisition'
    }
    It 'Rejects target exceeding app' {
        $res = Test-ScopeValidity -TargetScope @{ acquisition='A'; business_unit='BU2'; site='S' } -PublisherScope @{ acquisition='A'; business_unit='BU2'; site='S' } -AppScope @{ acquisition='A'; business_unit='BU1'; site='S' }
        $res.Errors | Should -Contain 'Target scope exceeds app for business_unit'
    }
    It 'Requires CAB approval for cross-boundary' {
        $res = Test-ScopeValidity -TargetScope @{ acquisition='A2'; business_unit='BU2'; site='S' } -PublisherScope @{ acquisition='A1'; business_unit='BU1'; site='S' } -AppScope @{ acquisition='A2'; business_unit='BU2'; site='S' }
        $res.Errors | Should -Contain 'Cross-boundary deployment requires CAB approval'
    }
    It 'Accepts cross-boundary with CAB approval' {
        $res = Test-ScopeValidity -TargetScope @{ acquisition='A2'; business_unit='BU2'; site='S' } -PublisherScope @{ acquisition='A1'; business_unit='BU1'; site='S' } -AppScope @{ acquisition='A2'; business_unit='BU2'; site='S' } -CABApprovalId 'cab-001'
        $res.IsValid | Should -BeTrue
    }
}
