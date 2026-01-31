# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Execute operation with circuit breaker pattern.

.DESCRIPTION
    Implements circuit breaker pattern to prevent cascading failures.
    States: Closed (normal), Open (failing), Half-Open (testing recovery).

.PARAMETER Operation
    ScriptBlock to execute.

.PARAMETER CircuitName
    Unique name for this circuit breaker instance.

.PARAMETER FailureThreshold
    Number of failures before opening circuit (default: 5).

.PARAMETER ResetTimeoutSeconds
    Seconds to wait before attempting half-open state (default: 60).

.PARAMETER HalfOpenMaxCalls
    Maximum calls in half-open state before closing (default: 3).

.EXAMPLE
    Invoke-CircuitBreaker -Operation { Invoke-RestMethod -Uri $Url } -CircuitName "IntuneAPI"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [scriptblock]$Operation,

    [Parameter(Mandatory = $true)]
    [string]$CircuitName,

    [Parameter(Mandatory = $false)]
    [int]$FailureThreshold = 5,

    [Parameter(Mandatory = $false)]
    [int]$ResetTimeoutSeconds = 60,

    [Parameter(Mandatory = $false)]
    [int]$HalfOpenMaxCalls = 3
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Circuit breaker state storage (in-memory, per circuit)
if (-not $script:CircuitBreakers) {
    $script:CircuitBreakers = @{}
}

# Initialize circuit if needed
if (-not $script:CircuitBreakers.ContainsKey($CircuitName)) {
    $script:CircuitBreakers[$CircuitName] = @{
        State = "Closed"  # Closed, Open, HalfOpen
        FailureCount = 0
        SuccessCount = 0
        LastFailureTime = $null
        HalfOpenCallCount = 0
    }
}

$Circuit = $script:CircuitBreakers[$CircuitName]

# Check circuit state
if ($Circuit.State -eq "Open") {
    $TimeSinceFailure = (Get-Date) - $Circuit.LastFailureTime

    if ($TimeSinceFailure.TotalSeconds -ge $ResetTimeoutSeconds) {
        # Transition to half-open
        $Circuit.State = "HalfOpen"
        $Circuit.HalfOpenCallCount = 0
        $Circuit.SuccessCount = 0
        Write-Verbose "Circuit breaker '$CircuitName' transitioning to Half-Open state"
    } else {
        $RemainingSeconds = $ResetTimeoutSeconds - $TimeSinceFailure.TotalSeconds
        throw "Circuit breaker '$CircuitName' is OPEN. Retry after $([math]::Round($RemainingSeconds)) seconds."
    }
}

# Execute operation
try {
    $Result = & $Operation

    # Success - reset counters
    if ($Circuit.State -eq "HalfOpen") {
        $Circuit.HalfOpenCallCount++
        $Circuit.SuccessCount++

        if ($Circuit.SuccessCount -ge $HalfOpenMaxCalls) {
            # Transition to closed
            $Circuit.State = "Closed"
            $Circuit.FailureCount = 0
            $Circuit.SuccessCount = 0
            $Circuit.HalfOpenCallCount = 0
            Write-Verbose "Circuit breaker '$CircuitName' transitioning to Closed state"
        }
    } else {
        # Closed state - reset failure count on success
        $Circuit.FailureCount = 0
    }

    return $Result

} catch {
    # Failure - increment counter
    $Circuit.FailureCount++
    $Circuit.LastFailureTime = Get-Date

    if ($Circuit.State -eq "HalfOpen") {
        # Half-open failure - immediately open
        $Circuit.State = "Open"
        $Circuit.HalfOpenCallCount = 0
        $Circuit.SuccessCount = 0
        Write-Verbose "Circuit breaker '$CircuitName' transitioning to Open state (half-open failure)"
    } elseif ($Circuit.FailureCount -ge $FailureThreshold) {
        # Closed failure threshold reached - open circuit
        $Circuit.State = "Open"
        Write-Verbose "Circuit breaker '$CircuitName' transitioning to Open state (threshold reached)"
    }

    throw
}
