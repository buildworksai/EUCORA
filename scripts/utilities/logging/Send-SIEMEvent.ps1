# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Send structured events to Azure Log Analytics using retry logic.
.DESCRIPTION
Wraps HTTP POST to Log Analytics, maps severity, includes correlation_id, retries transient errors via Invoke-RetryWithBackoff.
.PARAMETER Event
Hash table containing timestamp, level, message, correlation_id, component.
.PARAMETER WorkspaceId
Log Analytics workspace ID (from config/vault).
.PARAMETER SharedKey
Shared key for workspace authentication.
.PARAMETER LogType
Log type name (default ControlPlaneEvents).
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/infrastructure/siem-integration.md, .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/Get-ConfigValue.ps1"
. "$PSScriptRoot/../common/Invoke-RetryWithBackoff.ps1"
function Send-SIEMEvent {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$Event,
        [string]$WorkspaceId,
        [string]$SharedKey,
        [string]$LogType = 'ControlPlaneEvents',
        [int]$RetryMaxAttempts,
        [int]$RetryBaseSeconds,
        [int]$RetryMaxBackoffSeconds,
        [string[]]$RetryTransientErrorCodes
    )
    # Get retry configuration from config file if not provided
    if (-not $PSBoundParameters.ContainsKey('RetryMaxAttempts')) {
        $RetryMaxAttempts = Get-ConfigValue -Key 'retry.max_retries' -DefaultValue 3
    }
    if (-not $PSBoundParameters.ContainsKey('RetryBaseSeconds')) {
        $initialDelayMs = Get-ConfigValue -Key 'retry.initial_delay_ms' -DefaultValue 1000
        $RetryBaseSeconds = [math]::Round($initialDelayMs / 1000, 0)
    }
    if (-not $PSBoundParameters.ContainsKey('RetryMaxBackoffSeconds')) {
        $maxDelayMs = Get-ConfigValue -Key 'retry.max_delay_ms' -DefaultValue 30000
        $RetryMaxBackoffSeconds = [math]::Round($maxDelayMs / 1000, 0)
    }

    $workspace = if ($WorkspaceId) { $WorkspaceId } else { Get-ConfigValue -Key 'azure.log_analytics_workspace_id' -Required }

    # Try vault first, then config fallback
    if ($SharedKey) {
        $shared = $SharedKey
    } else {
        try {
            . "$PSScriptRoot/../Get-VaultSecret.ps1"
            $shared = Get-VaultSecret -SecretName 'AZURE_LOG_ANALYTICS_SHARED_KEY' -ErrorAction SilentlyContinue
        } catch {
            # Fall back to config if vault not available
            $shared = Get-ConfigValue -Key 'azure.log_analytics_shared_key' -ErrorAction SilentlyContinue
        }
    }

    if (-not $shared) { throw 'Missing SIEM shared key in config/vault.' }
    $body = $Event | ConvertTo-Json -Depth 5
    $date = (Get-Date).ToUniversalTime().ToString('r')
    $contentLength = ([System.Text.Encoding]::UTF8.GetByteCount($body))
    $signature = 'POST' + "`n" + $contentLength + "`napplication/json`n" + $date + "`n/api/logs"
    $encodingKey = [Convert]::FromBase64String($shared)
    $hashAlgorithm = [System.Security.Cryptography.HMACSHA256]::new($encodingKey)
    try {
        $hash = $hashAlgorithm.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($signature))
    }
    finally {
        $hashAlgorithm.Dispose()
    }
    $auth = "SharedKey ${workspace}:" + [Convert]::ToBase64String($hash)
    $headers = @{ Authorization = $auth; 'x-ms-date' = $date; 'Log-Type' = $LogType; 'time-generated-field' = $Event.timestamp }
    # Use centralized endpoint configuration
    . "$PSScriptRoot/../common/Get-EndpointConfig.ps1"
    $uri = Get-EndpointConfig -Service "siem" -Endpoint "azure_log_analytics" -Parameters @{workspace = $workspace}
    $retryArgs = @{
        ScriptBlock = {
            Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body -ContentType 'application/json'
        }
        CorrelationId = $Event.correlation_id
        MaxAttempts = $RetryMaxAttempts
        BaseSeconds = $RetryBaseSeconds
        MaxBackoffSeconds = $RetryMaxBackoffSeconds
    }
    if ($RetryTransientErrorCodes) {
        $retryArgs.TransientErrorCodes = $RetryTransientErrorCodes
    }
    $null = Invoke-RetryWithBackoff @retryArgs
    return $true
}
