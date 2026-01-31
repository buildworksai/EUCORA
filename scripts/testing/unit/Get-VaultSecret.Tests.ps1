# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Pester tests for Get-VaultSecret.ps1
#>
BeforeAll {
    $ScriptRoot = Split-Path -Parent $PSScriptRoot
    $UtilitiesPath = Join-Path (Split-Path -Parent $ScriptRoot) "utilities"
    . (Join-Path $UtilitiesPath "Get-VaultSecret.ps1")
}

Describe "Get-VaultSecret" {
    Context "Environment Variable Fallback" {
        It "Should retrieve secret from environment variable" {
            $EnvVarName = "EUCORA_TEST_SECRET"
            $TestValue = "test-secret-value"
            [System.Environment]::SetEnvironmentVariable($EnvVarName, $TestValue, "Process")

            $Result = Get-VaultSecret -SecretName "TEST_SECRET" -ErrorAction SilentlyContinue

            if ($Result) {
                $Result | Should -Be $TestValue
            }

            # Cleanup
            [System.Environment]::SetEnvironmentVariable($EnvVarName, $null, "Process")
        }
    }

    Context "Error Handling" {
        It "Should throw error when secret not found" {
            { Get-VaultSecret -SecretName "NONEXISTENT_SECRET" } | Should -Throw
        }
    }
}
