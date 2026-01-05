# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Invoke-Dapctl' {
    BeforeAll {
        . (Join-Path $PSScriptRoot 'dapctl.ps1')
    }
    BeforeEach {
        $env:DAPCTL_AUTH_TOKEN = 'test-token'
    }
    AfterEach {
        Remove-Item Env:DAPCTL_AUTH_TOKEN -ErrorAction SilentlyContinue
    }
    It 'returns 0 when health command exists' {
        $result = Invoke-Dapctl -Command 'health' -Arguments @()
        $result | Should -Be 0
    }
    It 'returns 1 for unknown command' {
        $result = Invoke-Dapctl -Command 'missing' -Arguments @()
        $result | Should -Be 1
    }
    It 'executes deploy command' {
        $intent = @{
            AppName = 'TestApp'
            Ring = 'ring-1-canary'
            PackagePath = '/tmp/test.intunewin'
            InstallCommand = 'install.exe /qn'
            DetectionPath = 'C:\Program Files\TestApp'
            DetectionFile = 'app.exe'
        }
        $result = Invoke-Dapctl -Command 'deploy' -Arguments @('-DeploymentIntent', $intent)
        $result | Should -Be 0
    }
    It 'executes status command' {
        $result = Invoke-Dapctl -Command 'status' -Arguments @()
        $result | Should -Be 0
    }
    It 'executes test-connection command' {
        $result = Invoke-Dapctl -Command 'test-connection' -Arguments @()
        $result | Should -Be 0
    }
}
