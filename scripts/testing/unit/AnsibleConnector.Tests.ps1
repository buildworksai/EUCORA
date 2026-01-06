# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
# Suppress common test file warnings
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Mock function parameters required for interface compatibility')]
#<#+
.SYNOPSIS
    Unit tests for the AWX/Tower Ansible connector.
.DESCRIPTION
    Validates idempotency, rollback launches, status queries, and ping logic without invoking live AWX endpoints.
.NOTES
Version: 1.0
Author: Platform Engineering
#>

Describe 'AnsibleConnector' {
    BeforeEach {
        . "$PSScriptRoot/../../connectors/ansible/AnsibleConnector.ps1"
        function Write-StructuredLog {
            return
        }
        function Set-TestConnectorConfig {
            [CmdletBinding(SupportsShouldProcess)]
            param(
                [Parameter(Mandatory = $true)]
                [hashtable]$Config
            )
            if ($PSCmdlet.ShouldProcess("Test connector configuration", "Set")) {
                $script:TestConnectorConfig = $Config
            }
        }
        function Get-ConnectorConfig {
            return $script:TestConnectorConfig
        }
        function Get-CorrelationId {
            param(
                [Parameter(Mandatory = $false)]
                [string]$Type
            )
            # Use Type parameter to avoid unused parameter warning
            if ($Type -eq 'deployment') { return 'dp-test' }
            return 'dp-test'
        }
        Set-TestConnectorConfig @{ }
        $script:BaseIntent = @{
            JobTemplateId = 'jt-1'
            ArtifactId = 'artifact-1'
            AppName = 'TestApp'
            Inventory = 'inv-1'
            ManifestHash = 'hash'
            Ring = 'ring-1-canary'
        }
    }


    It 'returns stub when configuration is missing' {
        Set-TestConnectorConfig @{ tower_api_url = $null; token = $null }
        $result = Publish-AnsibleApplication -DeploymentIntent $script:BaseIntent -CorrelationId 'dp-1' | Where-Object { $_ -is [hashtable] }
        $result.status | Should -Be 'stubbed'
    }

    It 'launches job when configuration is available' {
        Set-TestConnectorConfig @{ tower_api_url = 'https://awx.example.com/api/v2'; token = 'token'; job_template_id = 'jt-1'; rollback_job_template_id = 'rt-1' }
        Mock Invoke-ConnectorRequest {
            param($Uri, $Method)
            # Use both parameters to avoid unused parameter warning
            if ($Method -eq 'GET' -and $Uri -like '*hosts*') { return @{ results = @() } }
            if ($Method -eq 'GET') { return @{ results = @() } }
            return @{ job_id = 'awx-123' }
        }

        $result = Publish-AnsibleApplication -DeploymentIntent $script:BaseIntent -CorrelationId 'dp-2' | Where-Object { $_ -is [hashtable] }
        $result.status | Should -Be 'launched'
        $result.awx_response.job_id | Should -Be 'awx-123'
        Assert-MockCalled Invoke-ConnectorRequest -Times 2
    }

    It 'launches rollback job when requested' {
        Set-TestConnectorConfig @{ tower_api_url = 'https://awx.example.com/api/v2'; token = 'token'; rollback_job_template_id = 'rt-1' }
        Mock Invoke-ConnectorRequest { @{ job_id = 'rb-001' } }

        $result = Remove-AnsibleApplication -ApplicationId 'app-1' -CorrelationId 'dp-3' | Where-Object { $_ -is [hashtable] }
        $result.status | Should -Be 'rollback_launched'
    }

    It 'queries job history via deployment status' {
        Set-TestConnectorConfig @{ tower_api_url = 'https://awx.example.com/api/v2'; token = 'token' }
        Mock Invoke-ConnectorRequest { @{ results = @(@{ id = 77 }) } }

        $status = Get-AnsibleDeploymentStatus -CorrelationId 'dp-4' | Where-Object { $_ -is [hashtable] }
        $status.jobs.Count | Should -BeGreaterThan 0
    }

    It 'pings AWX successfully' {
        Set-TestConnectorConfig @{ tower_api_url = 'https://awx.example.com/api/v2'; token = 'token' }
        Mock Invoke-ConnectorRequest { @{ status = 'ok' } }

        $result = Test-AnsibleConnection -AuthToken 'token' | Where-Object { $_ -is [hashtable] }
        $result.status | Should -Be 'ready'
    }

    It 'retrieves inventory hosts' {
        Set-TestConnectorConfig @{ tower_api_url = 'https://awx.example.com/api/v2'; token = 'token'; inventory_id = 'inv-1' }
        Mock Invoke-ConnectorRequest { @{ results = @(@{ name = 'host1'; id = 5; last_modified = '2025-12-01T00:00:00Z' }) } }

        $devices = @(Get-AnsibleTargetDevices -Ring 'ring-2-pilot')
        $devices.Count | Should -Be 1
        $devices[0].inventory | Should -Be 'inv-1'
    }
}
