# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Tests promotion gate evaluation for success/fail cases.
.DESCRIPTION
Covers thresholds, incidents, CAB decisions, rollback validation.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/ring-model.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Test-PromotionGates' {
    BeforeAll {
        . "$PSScriptRoot/Test-PromotionGates.ps1"
        $script:ConfigPath = [System.IO.Path]::GetTempFileName()
        $config = @{
            rings = @{
                'ring-0-lab' = @{ success_rate_threshold = 0.95; time_to_compliance = @{ online_hours = 24 }; max_incidents = 1; cab_approval_required_if_risk_gt = 50 }
                'ring-1-canary' = @{ success_rate_threshold = 0.98; time_to_compliance = @{ online_hours = 24 }; max_incidents = 0; cab_approval_required_if_risk_gt = 50 }
            }
        } | ConvertTo-Json -Depth 5
        Set-Content -Path $script:ConfigPath -Value $config
    }
    AfterAll {
        Remove-Item -Path $script:ConfigPath -Force
    }
    It 'Passes all gates' {
        $telemetry = @{ success_rate = 0.99; time_to_compliance_hours = 12; incident_count = 0 }
        $intent = @{ risk_score = 40; rollback_plan = @{ validated = $true } }
        $result = Test-PromotionGates -CurrentRing 'ring-1-canary' -Telemetry $telemetry -DeploymentIntent $intent -ConfigPath $script:ConfigPath
        $result.AllowPromotion | Should -BeTrue
    }
    It 'Fails success rate gate' {
        $telemetry = @{ success_rate = 0.95; time_to_compliance_hours = 12; incident_count = 0 }
        $intent = @{ risk_score = 40; rollback_plan = @{ validated = $true } }
        $result = Test-PromotionGates -CurrentRing 'ring-1-canary' -Telemetry $telemetry -DeploymentIntent $intent -ConfigPath $script:ConfigPath
        $result.GatesFailed | Should -Contain 'success_rate'
    }
    It 'Fails time to compliance' {
        $telemetry = @{ success_rate = 0.99; time_to_compliance_hours = 30; incident_count = 0 }
        $intent = @{ risk_score = 40; rollback_plan = @{ validated = $true } }
        $result = Test-PromotionGates -CurrentRing 'ring-1-canary' -Telemetry $telemetry -DeploymentIntent $intent -ConfigPath $script:ConfigPath
        $result.GatesFailed | Should -Contain 'time_to_compliance'
    }
    It 'Fails incident gate' {
        $telemetry = @{ success_rate = 0.99; time_to_compliance_hours = 10; incident_count = 2 }
        $intent = @{ risk_score = 40; rollback_plan = @{ validated = $true } }
        $result = Test-PromotionGates -CurrentRing 'ring-1-canary' -Telemetry $telemetry -DeploymentIntent $intent -ConfigPath $script:ConfigPath
        $result.GatesFailed | Should -Contain 'incident_count'
    }
    It 'Requires CAB approval for risk > 50' {
        $telemetry = @{ success_rate = 0.99; time_to_compliance_hours = 10; incident_count = 0 }
        $intent = @{ risk_score = 60; rollback_plan = @{ validated = $true }; cab_approval_id = $null }
        $result = Test-PromotionGates -CurrentRing 'ring-1-canary' -Telemetry $telemetry -DeploymentIntent $intent -ConfigPath $script:ConfigPath
        $result.GatesFailed | Should -Contain 'cab_approval'
    }
    It 'Requires rollback validation for Ring 0' {
        $telemetry = @{ success_rate = 0.99; time_to_compliance_hours = 2; incident_count = 0 }
        $intent = @{ risk_score = 10; rollback_plan = @{ validated = $false } }
        $result = Test-PromotionGates -CurrentRing 'ring-0-lab' -Telemetry $telemetry -DeploymentIntent $intent -ConfigPath $script:ConfigPath
        $result.GatesFailed | Should -Contain 'rollback_validation'
    }
}
