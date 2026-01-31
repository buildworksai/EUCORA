# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Pester tests for Invoke-CircuitBreaker.ps1
#>
BeforeAll {
    $ScriptRoot = Split-Path -Parent $PSScriptRoot
    $UtilitiesPath = Join-Path (Split-Path -Parent $ScriptRoot) "utilities"
    . (Join-Path $UtilitiesPath "Invoke-CircuitBreaker.ps1")
}

Describe "Invoke-CircuitBreaker" {
    Context "Successful Operation" {
        It "Should execute operation successfully" {
            $Operation = { return "success" }
            $Result = Invoke-CircuitBreaker -Operation $Operation -CircuitName "TestCircuit"
            $Result | Should -Be "success"
        }
    }

    Context "Failure Threshold" {
        It "Should open circuit after failure threshold" {
            $FailureCount = 0
            $Operation = {
                $script:FailureCount++
                throw "Simulated failure"
            }

            # Execute until circuit opens
            for ($i = 0; $i -lt 6; $i++) {
                try {
                    Invoke-CircuitBreaker -Operation $Operation -CircuitName "TestCircuit2" -FailureThreshold 5 -ErrorAction Stop
                } catch {
                    # Expected
                }
            }

            # Next call should fail immediately (circuit open)
            { Invoke-CircuitBreaker -Operation { return "test" } -CircuitName "TestCircuit2" -ErrorAction Stop } | Should -Throw
        }
    }
}
