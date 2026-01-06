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
        [int]$RetryMaxAttempts = 5,
        [int]$RetryBaseSeconds = 4,
        [int]$RetryMaxBackoffSeconds = 60,
        [string[]]$RetryTransientErrorCodes
    )
    $workspace = if ($WorkspaceId) { $WorkspaceId } else { Get-ConfigValue -Key 'azure.log_analytics_workspace_id' -Required }
    $shared = if ($SharedKey) { $SharedKey } else { Get-ConfigValue -Key 'azure.log_analytics_shared_key' }
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
    $uri = "https://$workspace.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"
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
