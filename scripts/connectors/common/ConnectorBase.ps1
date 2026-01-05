# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Shared helpers for execution plane connectors.
.DESCRIPTION
    Loads connector-specific settings, builds authorization headers, executes HTTP calls via exponential backoff, and enforces idempotency. Ensures every call logs the correlation id and conforms to control plane guardrails.
.NOTES
Version: 1.1
Author: Platform Engineering
Related Docs: .agents/rules/08-connector-rules.md, docs/architecture/execution-plane-connectors.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../utilities/common/Get-ConfigValue.ps1"
. "$PSScriptRoot/../../utilities/logging/Write-StructuredLog.ps1"
. "$PSScriptRoot/../../utilities/common/Invoke-RetryWithBackoff.ps1"
. "$PSScriptRoot/../../utilities/common/Test-IdempotencyKey.ps1"

function Get-ConnectorConfig {
    <#
    .SYNOPSIS
        Retrieve connector-specific configuration.
    .PARAMETER Name
        Connector name (intune, jamf, sccm, landscape, ansible).
    .EXAMPLE
        $config = Get-ConnectorConfig -Name 'intune'
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('intune','jamf','sccm','landscape','ansible')]
        [string]$Name
    )

    $settings = Get-ConfigValue -Key "connectors.$Name"
    if (-not $settings) {
        throw "Connector configuration missing for $Name"
    }
    return $settings
}

function Get-ConnectorAuthToken {
    <#
    .SYNOPSIS
        Acquire OAuth2 bearer token for connector authentication.
    .DESCRIPTION
        Supports client credentials flow for Intune (Microsoft Graph), Jamf, and Ansible (AWX/Tower).
    .PARAMETER ConnectorName
        Connector name (intune, jamf, ansible).
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $token = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet('intune','jamf','ansible')]
        [string]$ConnectorName,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name $ConnectorName

    switch ($ConnectorName) {
        'intune' {
            # Microsoft Graph OAuth2 client credentials flow
            $tenantId = $config.tenant_id
            $clientId = $config.client_id
            $clientSecret = $config.client_secret

            if (-not $tenantId -or -not $clientId -or -not $clientSecret) {
                throw "Intune connector missing OAuth2 credentials (tenant_id, client_id, client_secret)"
            }

            $tokenUri = "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token"
            $body = @{
                client_id     = $clientId
                client_secret = $clientSecret
                scope         = "https://graph.microsoft.com/.default"
                grant_type    = "client_credentials"
            }

            try {
                $response = Invoke-RestMethod -Uri $tokenUri -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
                Write-StructuredLog -Level 'Debug' -Message 'Intune OAuth2 token acquired' -CorrelationId $CorrelationId
                return $response.access_token
            }
            catch {
                Write-StructuredLog -Level 'Error' -Message "Intune OAuth2 token acquisition failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
                throw
            }
        }

        'jamf' {
            # Jamf Pro OAuth2 or API token
            $apiUrl = $config.api_url
            $clientId = $config.client_id
            $clientSecret = $config.client_secret

            if (-not $apiUrl -or -not $clientId -or -not $clientSecret) {
                throw "Jamf connector missing OAuth2 credentials (api_url, client_id, client_secret)"
            }

            $tokenUri = "$($apiUrl.TrimEnd('/'))/api/oauth/token"
            $body = @{
                client_id     = $clientId
                client_secret = $clientSecret
                grant_type    = "client_credentials"
            }

            try {
                $response = Invoke-RestMethod -Uri $tokenUri -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
                Write-StructuredLog -Level 'Debug' -Message 'Jamf OAuth2 token acquired' -CorrelationId $CorrelationId
                return $response.access_token
            }
            catch {
                Write-StructuredLog -Level 'Error' -Message "Jamf OAuth2 token acquisition failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
                throw
            }
        }

        'ansible' {
            # AWX/Tower uses static API token (configured in settings)
            $token = $config.token
            if (-not $token) {
                throw "Ansible connector missing API token"
            }
            Write-StructuredLog -Level 'Debug' -Message 'Ansible API token loaded from config' -CorrelationId $CorrelationId
            return $token
        }

        default {
            throw "Unsupported connector for token acquisition: $ConnectorName"
        }
    }
}

function Get-ErrorClassification {
    <#
    .SYNOPSIS
        Classify HTTP error as transient, permanent, or policy violation.
    .PARAMETER StatusCode
        HTTP status code.
    .PARAMETER ErrorMessage
        Error message from exception.
    .EXAMPLE
        $classification = Get-ErrorClassification -StatusCode 429 -ErrorMessage "Rate limit exceeded"
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [int]$StatusCode,

        [Parameter(Mandatory = $true)]
        [string]$ErrorMessage
    )

    # Transient errors (retry-able)
    $transientCodes = @(408, 429, 500, 502, 503, 504)
    if ($StatusCode -in $transientCodes) {
        return 'TRANSIENT'
    }

    # Policy violations (CAB/governance issues)
    $policyKeywords = @('forbidden', 'unauthorized', 'policy', 'compliance', 'approval required')
    foreach ($keyword in $policyKeywords) {
        if ($ErrorMessage -match $keyword) {
            return 'POLICY_VIOLATION'
        }
    }

    # Permanent errors (client-side issues)
    $permanentCodes = @(400, 401, 403, 404, 409, 422)
    if ($StatusCode -in $permanentCodes) {
        return 'PERMANENT'
    }

    # Default to permanent if unknown
    return 'PERMANENT'
}

function Invoke-ConnectorRequest {
    <#
    .SYNOPSIS
        Execute HTTP request to execution plane with retry logic and error classification.
    .DESCRIPTION
        Wraps Invoke-RestMethod with exponential backoff, idempotency key checking, and structured error handling.
    .PARAMETER Uri
        Target API endpoint.
    .PARAMETER Method
        HTTP method (GET, POST, PUT, PATCH, DELETE).
    .PARAMETER Body
        Request body (hashtable or JSON string).
    .PARAMETER Headers
        HTTP headers (hashtable).
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .PARAMETER IdempotencyKey
        Optional idempotency key (defaults to CorrelationId).
    .EXAMPLE
        $response = Invoke-ConnectorRequest -Uri $uri -Method 'POST' -Body $payload -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Uri,

        [Parameter(Mandatory = $true)]
        [ValidateSet('GET','POST','PUT','PATCH','DELETE')]
        [string]$Method,

        [Parameter(Mandatory = $false)]
        $Body,

        [Parameter(Mandatory = $false)]
        [hashtable]$Headers,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,

        [Parameter(Mandatory = $false)]
        [string]$IdempotencyKey
    )

    # Use CorrelationId as idempotency key if not provided
    $idempotencyKey = if ($IdempotencyKey) { $IdempotencyKey } else { $CorrelationId }

    # Check idempotency for non-GET requests
    if ($Method -ne 'GET') {
        $alreadyProcessed = Test-IdempotencyKey -CorrelationId $idempotencyKey
        if ($alreadyProcessed) {
            Write-StructuredLog -Level 'Info' -Message 'Idempotent request detected, skipping execution' -CorrelationId $CorrelationId -Metadata @{ idempotency_key = $idempotencyKey }
            return @{
                status = 'idempotent_skip'
                correlation_id = $CorrelationId
                idempotency_key = $idempotencyKey
            }
        }
    }

    # Prepare request body
    $payload = $null
    if ($Body) {
        $payload = if ($Body -is [string]) { $Body } else { $Body | ConvertTo-Json -Depth 10 -Compress }
    }

    # Prepare headers
    $requestHeaders = if ($Headers) { $Headers.Clone() } else { @{} }
    if (-not $requestHeaders.ContainsKey('Content-Type')) {
        $requestHeaders['Content-Type'] = 'application/json'
    }
    if (-not $requestHeaders.ContainsKey('X-Correlation-ID')) {
        $requestHeaders['X-Correlation-ID'] = $CorrelationId
    }
    if (-not $requestHeaders.ContainsKey('X-Idempotency-Key')) {
        $requestHeaders['X-Idempotency-Key'] = $idempotencyKey
    }

    # Execute request with retry logic
    $scriptBlock = {
        param($uri, $method, $body, $headers)
        return Invoke-RestMethod -Uri $uri -Method $method -Body $body -Headers $headers -TimeoutSec 60
    }

    try {
        $response = Invoke-RetryWithBackoff -ScriptBlock {
            & $scriptBlock $Uri $Method $payload $requestHeaders
        } -CorrelationId $CorrelationId -MaxRetries 3 -BaseDelaySeconds 2

        Write-StructuredLog -Level 'Debug' -Message 'Connector request succeeded' -CorrelationId $CorrelationId -Metadata @{
            uri = $Uri
            method = $Method
            idempotency_key = $idempotencyKey
        }

        return $response
    }
    catch {
        $statusCode = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        $errorMessage = $_.Exception.Message
        $errorClassification = Get-ErrorClassification -StatusCode $statusCode -ErrorMessage $errorMessage

        Write-StructuredLog -Level 'Warning' -Message "Connector request failed: $errorMessage" -CorrelationId $CorrelationId -Metadata @{
            uri = $Uri
            method = $Method
            status_code = $statusCode
            error_classification = $errorClassification
        }

        return @{
            status = 'failed'
            uri = $Uri
            method = $Method
            error = $errorMessage
            error_classification = $errorClassification
            status_code = $statusCode
            correlation_id = $CorrelationId
        }
    }
}
