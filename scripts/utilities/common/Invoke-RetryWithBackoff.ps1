# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Retry a script block with exponential backoff for transient errors.
.DESCRIPTION
Retries the supplied script block when transient errors occur (HTTP 429/503/504 or named exceptions). Records attempts via Write-StructuredLog (when available) and honors correlation IDs for audit trails.
.PARAMETER ScriptBlock
Script block to execute (required).
.PARAMETER MaxAttempts
Maximum attempts before failing (default 5).
.PARAMETER BaseSeconds
Base interval for exponential backoff (default 4 seconds).
.PARAMETER MaxBackoffSeconds
Maximum wait per retry (default 60 seconds).
.PARAMETER CorrelationId
Correlation ID emitted to logs for each attempt.
.PARAMETER TransientErrorCodes
Codes or exception types considered transient.
.EXAMPLE
Invoke-RetryWithBackoff -ScriptBlock { Invoke-RestMethod ... } -CorrelationId dp-20260104-0001
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/08-connector-rules.md, docs/architecture/execution-plane-connectors.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Invoke-RetryWithBackoff {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$ScriptBlock,
        [int]$MaxAttempts = 5,
        [int]$BaseSeconds = 4,
        [int]$MaxBackoffSeconds = 60,
        [string]$CorrelationId,
        [string[]]$TransientErrorCodes = @('429','503','504','TimeoutException','SocketException','WebException')
    )
    begin {
        $attempt = 0
        $lastException = $null
    }
    process {
        while ($attempt -lt $MaxAttempts) {
            $attempt++
            try {
                if ($CorrelationId) {
                    Write-Output \"[Retry] attempt $attempt, correlation_id=$CorrelationId\"\n
                }
                return & $ScriptBlock
            }
            catch {
                $lastException = $_.Exception
                $code = $null
                if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                    $code = $_.Exception.Response.StatusCode.Value__
                }
                else {
                    $code = $_.Exception.GetType().Name
                }
                if ($TransientErrorCodes -contains $code.ToString()) {
                    $delay = [math]::Min($MaxBackoffSeconds, [math]::Pow(2, $attempt) * $BaseSeconds)
                    Start-Sleep -Seconds $delay
                    continue
                }
                throw $_.Exception
            }
        }
        throw $lastException
    }
}
