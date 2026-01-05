# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Describe 'Initialize-Auth' {
    BeforeAll {
        $path = Join-Path $PSScriptRoot 'Initialize-Auth.ps1'
        . (Resolve-Path $path).Path
    }
    It 'returns token from environment' {
        $env:DAPCTL_AUTH_TOKEN = 'env-token'
        try {
            $token = Initialize-Auth
            $token | Should -Be 'env-token'
        }
        finally {
            Remove-Item Env:DAPCTL_AUTH_TOKEN -ErrorAction SilentlyContinue
        }
    }
}
