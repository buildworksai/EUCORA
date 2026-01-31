# E9: PowerShell Production Audit — Script Hardening & Endpoint Validation

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P1-Critical
**Dependencies**: None

---

## Overview

Comprehensive review and hardening of all PowerShell scripts and API endpoints to ensure production readiness. This includes:
- Script review for hardcoded values
- Error handling standardization
- Logging consistency
- Endpoint validation
- Security hardening
- Production configuration management

---

## Current Script Inventory

### CLI Commands (`scripts/cli/commands/`)

| Script | Purpose | Status | Issues |
|--------|---------|--------|--------|
| `Invoke-approve.ps1` | CAB approval operations | Review | Hardcoded endpoints |
| `Invoke-config.ps1` | Configuration management | Review | Settings file paths |
| `Invoke-connectors.ps1` | Connector operations | Review | Credential handling |
| `Invoke-deploy.ps1` | Deployment initiation | Review | API endpoints |
| `Invoke-evidence.ps1` | Evidence pack operations | Review | Storage paths |
| `Invoke-Health.ps1` | Health check | Review | Timeout values |
| `Invoke-logs.ps1` | Log retrieval | Review | Log paths |
| `Invoke-rings.ps1` | Ring operations | Review | Ring definitions |
| `Invoke-risk-score.ps1` | Risk calculation | Review | Model version |
| `Invoke-rollback.ps1` | Rollback operations | Review | Safety checks |
| `Invoke-status.ps1` | Status queries | Review | API endpoints |
| `Invoke-test-connection.ps1` | Connection testing | Review | Timeout values |
| `Invoke-version.ps1` | Version info | Review | Version sources |

### Connectors (`scripts/connectors/`)

| Script | Purpose | Status | Issues |
|--------|---------|--------|--------|
| `IntuneConnector.ps1` | Intune Graph API | Critical | Auth, throttling |
| `JamfConnector.ps1` | Jamf Pro API | Critical | Auth, pagination |
| `SccmConnector.ps1` | SCCM WMI/REST | Critical | Auth, delegation |
| `LandscapeConnector.ps1` | Landscape API | Critical | Auth handling |
| `AnsibleConnector.ps1` | AWX/Tower API | Critical | Token management |
| `ConnectorManager.ps1` | Connector orchestration | Review | Error handling |
| `ConnectorBase.ps1` | Base connector class | Review | Retry logic |

### Utilities (`scripts/utilities/`)

| Script | Purpose | Status | Issues |
|--------|---------|--------|--------|
| `Export-AuditTrail.ps1` | Audit export | Review | Date handling |
| `Send-SIEMEvent.ps1` | SIEM integration | Critical | Credentials |
| `Write-StructuredLog.ps1` | Logging | Review | Log format |
| `Invoke-RetryWithBackoff.ps1` | Retry logic | Review | Backoff params |
| `Get-ConfigValue.ps1` | Config retrieval | Review | Env vars |
| `Get-CorrelationId.ps1` | Correlation ID | Review | UUID format |
| `Test-IdempotencyKey.ps1` | Idempotency | Review | Key storage |

### Validation (`scripts/utilities/validation/`)

| Script | Purpose | Status | Issues |
|--------|---------|--------|--------|
| `Test-CABApproval.ps1` | CAB validation | Review | Rule definitions |
| `Test-EvidencePackCompleteness.ps1` | Evidence validation | Review | Schema version |
| `Test-PromotionGates.ps1` | Gate validation | Review | Threshold sources |
| `Test-ScopeValidity.ps1` | Scope validation | Review | Scope definitions |

---

## Audit Checklist

### 1. Configuration Management

**Issues to Address**:
- [ ] Replace hardcoded API endpoints with configuration
- [ ] Replace hardcoded file paths with environment variables
- [ ] Replace hardcoded timeouts with configurable values
- [ ] Replace hardcoded thresholds with config file references

**Standard Pattern**:
```powershell
# BAD: Hardcoded values
$ApiEndpoint = "https://api.eucora.com/v1"
$Timeout = 30

# GOOD: Configuration-driven
$Config = Get-EUCORAConfig
$ApiEndpoint = $Config.ApiEndpoint
$Timeout = $Config.DefaultTimeout ?? 30
```

### 2. Credential Handling

**Issues to Address**:
- [ ] Remove any hardcoded credentials
- [ ] Use secure credential retrieval (vault, env vars)
- [ ] Implement credential rotation support
- [ ] Add credential validation before use

**Standard Pattern**:
```powershell
# BAD: Hardcoded credentials
$ApiKey = "sk-abc123..."

# GOOD: Secure credential retrieval
function Get-SecureCredential {
    param([string]$CredentialName)

    # Try vault first
    $Credential = Get-VaultSecret -Name $CredentialName -ErrorAction SilentlyContinue
    if ($Credential) { return $Credential }

    # Fall back to environment variable
    $EnvVarName = "EUCORA_$($CredentialName.ToUpper())"
    $Credential = [System.Environment]::GetEnvironmentVariable($EnvVarName)
    if ($Credential) { return $Credential }

    throw "Credential '$CredentialName' not found in vault or environment"
}
```

### 3. Error Handling

**Issues to Address**:
- [ ] Standardize error handling across all scripts
- [ ] Add proper error classification
- [ ] Implement structured error responses
- [ ] Add correlation ID to all errors

**Standard Pattern**:
```powershell
# Standard error handling
try {
    $Result = Invoke-EUCORAOperation @params
}
catch [System.Net.WebException] {
    $ErrorType = "TransientError"
    $ShouldRetry = $true
}
catch [Microsoft.PowerShell.Commands.HttpResponseException] {
    $StatusCode = $_.Exception.Response.StatusCode
    switch ($StatusCode) {
        401 { $ErrorType = "AuthenticationError"; $ShouldRetry = $false }
        403 { $ErrorType = "AuthorizationError"; $ShouldRetry = $false }
        429 { $ErrorType = "RateLimitError"; $ShouldRetry = $true }
        default { $ErrorType = "ServerError"; $ShouldRetry = $true }
    }
}
catch {
    $ErrorType = "UnknownError"
    $ShouldRetry = $false
}

# Log error with correlation
Write-StructuredLog -Level Error -CorrelationId $CorrelationId -Message $_.Exception.Message -ErrorType $ErrorType
```

### 4. Logging Standardization

**Issues to Address**:
- [ ] Use structured logging format (JSON)
- [ ] Include correlation ID in all log entries
- [ ] Add appropriate log levels
- [ ] Ensure sensitive data is not logged

**Standard Pattern**:
```powershell
function Write-StructuredLog {
    param(
        [ValidateSet('Debug', 'Info', 'Warning', 'Error', 'Critical')]
        [string]$Level = 'Info',
        [string]$Message,
        [string]$CorrelationId,
        [hashtable]$Properties = @{}
    )

    $LogEntry = @{
        timestamp = (Get-Date -Format 'o')
        level = $Level
        message = $Message
        correlationId = $CorrelationId
        source = $MyInvocation.ScriptName
        properties = $Properties
    } | ConvertTo-Json -Compress

    # Output to appropriate sink
    switch ($Level) {
        'Error' { Write-Error $LogEntry }
        'Warning' { Write-Warning $LogEntry }
        default { Write-Output $LogEntry }
    }
}
```

### 5. API Endpoint Validation

**Issues to Address**:
- [ ] Validate all API endpoints are reachable
- [ ] Check authentication before operations
- [ ] Validate response schemas
- [ ] Handle version mismatches

**Standard Pattern**:
```powershell
function Test-EUCORAEndpoint {
    param(
        [string]$Endpoint,
        [string]$Method = 'GET',
        [int]$TimeoutSeconds = 10
    )

    try {
        $Response = Invoke-RestMethod -Uri "$Endpoint/health" -Method GET -TimeoutSec $TimeoutSeconds

        if ($Response.status -ne 'healthy') {
            return @{
                IsHealthy = $false
                Reason = "Endpoint unhealthy: $($Response.status)"
            }
        }

        # Validate API version compatibility
        if ($Response.version -lt $MinimumApiVersion) {
            return @{
                IsHealthy = $false
                Reason = "API version $($Response.version) below minimum $MinimumApiVersion"
            }
        }

        return @{
            IsHealthy = $true
            Version = $Response.version
        }
    }
    catch {
        return @{
            IsHealthy = $false
            Reason = $_.Exception.Message
        }
    }
}
```

### 6. Idempotency

**Issues to Address**:
- [ ] Ensure all write operations use idempotency keys
- [ ] Validate idempotency key format
- [ ] Implement idempotency key storage/lookup
- [ ] Handle duplicate request detection

**Standard Pattern**:
```powershell
function Invoke-IdempotentOperation {
    param(
        [string]$IdempotencyKey,
        [scriptblock]$Operation
    )

    # Validate key format
    if (-not (Test-IdempotencyKeyFormat $IdempotencyKey)) {
        throw "Invalid idempotency key format"
    }

    # Check for existing result
    $CachedResult = Get-IdempotentResult -Key $IdempotencyKey
    if ($CachedResult) {
        Write-StructuredLog -Level Info -Message "Returning cached result for idempotency key" -Properties @{ key = $IdempotencyKey }
        return $CachedResult
    }

    # Execute operation
    $Result = & $Operation

    # Cache result
    Set-IdempotentResult -Key $IdempotencyKey -Result $Result -ExpiryHours 24

    return $Result
}
```

### 7. Retry Logic

**Issues to Address**:
- [ ] Standardize retry parameters
- [ ] Implement exponential backoff
- [ ] Add jitter to prevent thundering herd
- [ ] Respect retry-after headers

**Standard Pattern**:
```powershell
function Invoke-WithRetry {
    param(
        [scriptblock]$Operation,
        [int]$MaxRetries = 3,
        [int]$InitialDelayMs = 1000,
        [double]$BackoffMultiplier = 2.0,
        [int]$MaxDelayMs = 30000,
        [switch]$AddJitter
    )

    $Attempt = 0
    $Delay = $InitialDelayMs

    while ($true) {
        $Attempt++

        try {
            return & $Operation
        }
        catch {
            if ($Attempt -ge $MaxRetries -or -not (Test-RetryableError $_)) {
                throw
            }

            # Check for Retry-After header
            if ($_.Exception.Response.Headers['Retry-After']) {
                $Delay = [int]$_.Exception.Response.Headers['Retry-After'] * 1000
            }
            else {
                # Exponential backoff with optional jitter
                $Delay = [Math]::Min($Delay * $BackoffMultiplier, $MaxDelayMs)
                if ($AddJitter) {
                    $Jitter = Get-Random -Minimum 0 -Maximum ($Delay * 0.1)
                    $Delay += $Jitter
                }
            }

            Write-StructuredLog -Level Warning -Message "Retry $Attempt of $MaxRetries after ${Delay}ms"
            Start-Sleep -Milliseconds $Delay
        }
    }
}
```

---

## Connector-Specific Hardening

### Intune Connector

```powershell
# scripts/connectors/intune/IntuneConnector.ps1

class IntuneConnector : ConnectorBase {
    [string]$TenantId
    [string]$ClientId
    [SecureString]$ClientSecret
    [string]$GraphEndpoint = "https://graph.microsoft.com/v1.0"

    # Throttling configuration
    [int]$RequestsPerSecond = 10
    [int]$ThrottleRetryAfterMs = 60000

    [hashtable] InvokeGraphApi([string]$Method, [string]$Endpoint, [hashtable]$Body = @{}) {
        $Uri = "$($this.GraphEndpoint)$Endpoint"

        # Rate limiting
        $this.ThrottleIfNeeded()

        try {
            $Headers = @{
                'Authorization' = "Bearer $($this.GetAccessToken())"
                'Content-Type' = 'application/json'
                'ConsistencyLevel' = 'eventual'
            }

            $Params = @{
                Uri = $Uri
                Method = $Method
                Headers = $Headers
            }

            if ($Body.Count -gt 0) {
                $Params.Body = $Body | ConvertTo-Json -Depth 10
            }

            $Response = Invoke-WithRetry -Operation {
                Invoke-RestMethod @Params
            } -MaxRetries 3

            return $Response
        }
        catch {
            if ($_.Exception.Response.StatusCode -eq 429) {
                # Handle throttling
                $RetryAfter = $_.Exception.Response.Headers['Retry-After'] ?? 60
                Write-StructuredLog -Level Warning -Message "Graph API throttled, waiting ${RetryAfter}s"
                Start-Sleep -Seconds $RetryAfter
                return $this.InvokeGraphApi($Method, $Endpoint, $Body)
            }
            throw
        }
    }

    # Pagination handling
    [array] GetAllPages([string]$Endpoint) {
        $Results = @()
        $NextLink = $Endpoint

        while ($NextLink) {
            $Response = $this.InvokeGraphApi('GET', $NextLink)
            $Results += $Response.value
            $NextLink = $Response.'@odata.nextLink'
        }

        return $Results
    }
}
```

### SCCM Connector

```powershell
# scripts/connectors/sccm/SccmConnector.ps1

class SccmConnector : ConnectorBase {
    [string]$SiteServer
    [string]$SiteCode
    [PSCredential]$Credential

    # Constrained delegation handling
    [bool]$UseConstrainedDelegation = $true

    [void] ValidateConnection() {
        # Test WMI connectivity
        try {
            $WmiParams = @{
                ComputerName = $this.SiteServer
                Namespace = "root\SMS\site_$($this.SiteCode)"
                Class = "SMS_Site"
            }

            if ($this.UseConstrainedDelegation) {
                $WmiParams.Credential = $this.Credential
            }

            $Site = Get-WmiObject @WmiParams

            if (-not $Site) {
                throw "Could not connect to SCCM site $($this.SiteCode)"
            }

            Write-StructuredLog -Level Info -Message "Connected to SCCM site $($this.SiteCode) on $($this.SiteServer)"
        }
        catch {
            Write-StructuredLog -Level Error -Message "SCCM connection failed: $($_.Exception.Message)"
            throw
        }
    }

    # SoD validation
    [void] ValidateSeparationOfDuties([string]$OperationType) {
        # Validate that the credential is appropriate for this operation
        $AllowedOperations = Get-SCCMRolePermissions -Credential $this.Credential

        if ($OperationType -notin $AllowedOperations) {
            throw "Credential not authorized for operation: $OperationType"
        }
    }
}
```

---

## Configuration File Structure

```json
// scripts/config/production.json
{
  "api": {
    "endpoint": "${EUCORA_API_ENDPOINT}",
    "version": "v1",
    "timeout_seconds": 30,
    "max_retries": 3
  },
  "connectors": {
    "intune": {
      "graph_endpoint": "https://graph.microsoft.com/v1.0",
      "requests_per_second": 10,
      "throttle_retry_after_ms": 60000
    },
    "jamf": {
      "api_version": "v1",
      "page_size": 100
    },
    "sccm": {
      "use_constrained_delegation": true,
      "timeout_seconds": 120
    }
  },
  "logging": {
    "level": "Info",
    "format": "json",
    "include_correlation_id": true
  },
  "retry": {
    "max_retries": 3,
    "initial_delay_ms": 1000,
    "max_delay_ms": 30000,
    "backoff_multiplier": 2.0,
    "add_jitter": true
  },
  "risk_model": {
    "version": "v1.0",
    "cab_threshold": 50
  },
  "promotion_gates": {
    "ring_1_success_rate": 0.98,
    "ring_2_success_rate": 0.97,
    "ring_3_success_rate": 0.99,
    "ring_4_success_rate": 0.99
  }
}
```

---

## Test Coverage Requirements

### Unit Tests

Each script must have corresponding `.Tests.ps1` file with:
- [ ] Function parameter validation tests
- [ ] Error handling tests
- [ ] Edge case tests
- [ ] Mock-based API tests

### Integration Tests

- [ ] Connector connectivity tests
- [ ] End-to-end workflow tests
- [ ] Authentication flow tests
- [ ] Error recovery tests

### Security Tests

- [ ] Credential exposure tests
- [ ] Input sanitization tests
- [ ] Permission boundary tests

---

## Deliverables

1. Updated scripts with hardening applied
2. Standardized configuration system
3. Comprehensive error handling
4. Production configuration files
5. Test coverage for all scripts
6. Security review documentation
7. Deployment runbook in `docs/runbooks/powershell-deployment.md`
