# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Unit tests for ConnectorManager dispatch logic.
.DESCRIPTION
    Validates connector name resolution, function naming helpers, and core operations without hitting live execution planes.
.NOTES
Version: 1.0
Author: Platform Engineering
#>

Describe 'ConnectorManager' {
    BeforeEach {
        . "$PSScriptRoot/../../connectors/ConnectorManager.ps1"
        function GetTestConnectionReports {
            param($Token)
            Test-Connection -AuthToken $Token
        }

        function Import-ConnectorModule {
            param(
                [Parameter(Mandatory = $true)]
                [string]$Name
            )
            $script:LoadedConnectors[$Name] = $true
        }

        function Write-StructuredLog {
            return
        }

        function Publish-IntuneApplication {
            param($DeploymentIntent, $CorrelationId)
            return @{ status = 'mocked'; connector = 'intune'; intent = $DeploymentIntent; correlation_id = $CorrelationId }
        }
        function Get-IntuneDeploymentStatus {
            param($CorrelationId)
            return @{ status = 'complete'; correlation_id = $CorrelationId }
        }
        function Get-IntuneTargetDevices {
            param($Ring)
            return @([ordered]@{ device_id = "intune-${Ring}-1"; ring = $Ring })
        }
        function Test-IntuneConnection {
            param($AuthToken)
            return @{ connector = 'intune'; status = 'ready'; token = $AuthToken }
        }
        function Test-JamfConnection {
            param($AuthToken)
            return @{ connector = 'jamf'; status = 'ready' }
        }
        function Test-SccmConnection {
            param($AuthToken)
            return @{ connector = 'sccm'; status = 'ready' }
        }
        function Test-LandscapeConnection {
            param($AuthToken)
            return @{ connector = 'landscape'; status = 'ready' }
        }
        function Test-AnsibleConnection {
            param($AuthToken)
            return @{ connector = 'ansible'; status = 'ready' }
        }
    }

    It 'builds Pascal-case names' {
        (Get-ConnectorPascalName -Name 'sccm') | Should -Be 'Sccm'
    }

    It 'computes connector function names' {
        (Get-ConnectorFunctionName -Verb 'Publish' -Connector 'intune' -Suffix 'Application') | Should -Be 'Publish-IntuneApplication'
    }

    It 'prefers explicit connector hints' {
        Resolve-ConnectorName -DeploymentIntent @{ Connector = 'Ansible'; Platform = 'Intune' } | Should -Be 'ansible'
    }

    It 'routes publish to the selected connector' {
        $intent = @{ Connector = 'intune'; AppName = 'TestApp' }
        $tmp = Publish-Application -DeploymentIntent $intent -CorrelationId 'dp-test'
        $result = $tmp | Where-Object { $_ -is [hashtable] }
        $result.connector | Should -Be 'intune'
        $result.intent | Should -Be $intent
    }

    It 'aggregates deployment status per connector' {
        $status = @(Get-DeploymentStatus -CorrelationId 'dp-status' -ConnectorName 'intune')[0]
        $status.status_by_connector.Count | Should -Be 1
        $status.status_by_connector[0].result.status | Should -Be 'complete'
    }

    It 'returns connector health snapshots' {
        $reports = @( & 'Test-Connection' -AuthToken 'token' )
        $filtered = @()
        foreach ($report in $reports) {
            if ($report.connector) {
                $filtered += $report
            }
        }
        $intune = $filtered | Where-Object { $_.connector -eq 'intune' }
        if (($intune.token) -ne 'token') {
            throw 'Intune connector token mismatch'
        }
        if ($filtered.Count -lt 5) {
            throw 'Expected at least 5 connector statuses'
        }
    }

    It 'queries target devices for ring' {
        $devices = @(Get-TargetDevices 'ring-1-canary' 'intune')
        $devices.Count | Should -Be 1
        $devices[0].ring | Should -Be 'ring-1-canary'
    }
}
