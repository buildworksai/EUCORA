# PowerShell Patterns Reference

Enterprise PowerShell patterns for automation, connectors, and deployment scripts.

---

## Script Structure

### Complete Script Template

```powershell
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Brief description of script purpose.

.DESCRIPTION
    Detailed description of what the script does,
    including any prerequisites and dependencies.

.PARAMETER CorrelationId
    Unique identifier for audit trail and tracing.

.PARAMETER PackagePath
    Path to the package file to process.

.PARAMETER TargetRing
    Deployment ring (0-4).

.EXAMPLE
    .\Deploy-Package.ps1 -PackagePath "C:\packages\app.intunewin" -TargetRing 1 -CorrelationId "abc-123"

.NOTES
    Version: 1.0
    Author: Platform Engineering
    Related Docs: docs/modules/intune/connector-spec.md
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$PackagePath,

    [Parameter(Mandatory = $true)]
    [ValidateRange(0, 4)]
    [int]$TargetRing,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9-]{36}$')]
    [string]$CorrelationId,

    [Parameter()]
    [switch]$DryRun
)

# Strict mode for better error detection
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Import common utilities
. "$PSScriptRoot/../utilities/Logging.ps1"
. "$PSScriptRoot/../utilities/RetryLogic.ps1"

#region Main Logic

try {
    Write-StructuredLog -Message "Starting deployment" -Level Info -CorrelationId $CorrelationId -Metadata @{
        package_path = $PackagePath
        target_ring = $TargetRing
    }

    # Main script logic here
    if ($DryRun) {
        Write-StructuredLog -Message "Dry run mode - no changes made" -Level Info -CorrelationId $CorrelationId
        return @{
            status = 'dry_run'
            correlation_id = $CorrelationId
        }
    }

    # Process package
    $result = Invoke-PackageDeployment -Path $PackagePath -Ring $TargetRing -CorrelationId $CorrelationId

    Write-StructuredLog -Message "Deployment complete" -Level Info -CorrelationId $CorrelationId -Metadata @{
        result = $result.status
    }

    return @{
        status = 'success'
        correlation_id = $CorrelationId
        deployment_id = $result.id
    }
}
catch {
    $errorClass = Get-ErrorClassification -Exception $_.Exception

    Write-StructuredLog -Message "Deployment failed" -Level Error -CorrelationId $CorrelationId -Metadata @{
        error_class = $errorClass
        error_message = $_.Exception.Message
        stack_trace = $_.ScriptStackTrace
    }

    throw
}

#endregion
```

---

## Parameter Patterns

### Parameter Validation

```powershell
[CmdletBinding()]
param(
    # Required with validation
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$ApplicationName,

    # Constrained values
    [Parameter(Mandatory = $true)]
    [ValidateSet('Windows', 'macOS', 'Linux', 'iOS', 'Android')]
    [string]$Platform,

    # Pattern validation (UUID)
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')]
    [string]$CorrelationId,

    # Range validation
    [Parameter()]
    [ValidateRange(0, 100)]
    [int]$RiskScore = 0,

    # File must exist
    [Parameter()]
    [ValidateScript({ Test-Path $_ -PathType Leaf })]
    [string]$ConfigPath,

    # Directory must exist
    [Parameter()]
    [ValidateScript({ Test-Path $_ -PathType Container })]
    [string]$OutputDirectory = (Get-Location).Path,

    # Count validation
    [Parameter()]
    [ValidateCount(1, 10)]
    [string[]]$Tags,

    # Script block validation
    [Parameter()]
    [ValidateScript({
        if ($_ -gt (Get-Date)) { $true }
        else { throw "ScheduleTime must be in the future" }
    })]
    [datetime]$ScheduleTime
)
```

### Parameter Sets

```powershell
[CmdletBinding(DefaultParameterSetName = 'ByPath')]
param(
    [Parameter(Mandatory, ParameterSetName = 'ByPath')]
    [string]$PackagePath,

    [Parameter(Mandatory, ParameterSetName = 'ById')]
    [string]$PackageId,

    # Common to all sets
    [Parameter(Mandatory)]
    [string]$CorrelationId
)

# Check which set was used
if ($PSCmdlet.ParameterSetName -eq 'ByPath') {
    $package = Get-Package -Path $PackagePath
}
else {
    $package = Get-Package -Id $PackageId
}
```

---

## Structured Logging

### Logging Function

```powershell
# utilities/Logging.ps1

function Write-StructuredLog {
    <#
    .SYNOPSIS
        Write structured JSON log entry.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [Parameter()]
        [ValidateSet('Debug', 'Info', 'Warning', 'Error', 'Critical')]
        [string]$Level = 'Info',

        [Parameter()]
        [string]$CorrelationId,

        [Parameter()]
        [hashtable]$Metadata = @{}
    )

    $logEntry = [ordered]@{
        timestamp = (Get-Date -Format "o")
        level = $Level.ToUpper()
        message = $Message
    }

    if ($CorrelationId) {
        $logEntry.correlation_id = $CorrelationId
    }

    if ($Metadata.Count -gt 0) {
        $logEntry.metadata = $Metadata
    }

    $json = $logEntry | ConvertTo-Json -Compress -Depth 10

    # Color-coded console output
    $color = switch ($Level) {
        'Debug' { 'Gray' }
        'Info' { 'White' }
        'Warning' { 'Yellow' }
        'Error' { 'Red' }
        'Critical' { 'Magenta' }
        default { 'White' }
    }

    Write-Host $json -ForegroundColor $color

    # Also write to file if configured
    $logFile = $env:EUCORA_LOG_FILE
    if ($logFile) {
        Add-Content -Path $logFile -Value $json -Encoding UTF8
    }
}
```

### Usage Examples

```powershell
# Simple log
Write-StructuredLog -Message "Processing started" -Level Info -CorrelationId $CorrelationId

# With metadata
Write-StructuredLog -Message "Package uploaded" -Level Info -CorrelationId $CorrelationId -Metadata @{
    package_id = $package.Id
    size_bytes = $package.Size
    upload_time_ms = $stopwatch.ElapsedMilliseconds
}

# Error log
Write-StructuredLog -Message "Upload failed" -Level Error -CorrelationId $CorrelationId -Metadata @{
    error_class = 'TRANSIENT'
    error_message = $_.Exception.Message
    retry_count = $retryCount
}
```

---

## Error Handling

### Error Classification

```powershell
# utilities/ErrorHandling.ps1

function Get-ErrorClassification {
    <#
    .SYNOPSIS
        Classify error for retry logic.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.Exception]$Exception
    )

    $message = $Exception.Message
    $type = $Exception.GetType().Name

    # Transient errors (retry)
    if ($message -match '429|503|504|timeout|temporarily unavailable') {
        return 'TRANSIENT'
    }

    if ($type -match 'TimeoutException|TaskCanceledException') {
        return 'TRANSIENT'
    }

    # Policy violations (do not retry)
    if ($message -match '401|403|unauthorized|forbidden|access denied') {
        return 'POLICY_VIOLATION'
    }

    # Permanent errors (do not retry)
    return 'PERMANENT'
}

function Test-TransientError {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [System.Exception]$Exception
    )

    return (Get-ErrorClassification -Exception $Exception) -eq 'TRANSIENT'
}
```

### Try-Catch Pattern

```powershell
try {
    $result = Invoke-ConnectorRequest -Uri $uri -Method POST -Body $body -CorrelationId $CorrelationId
    return $result
}
catch {
    $errorClass = Get-ErrorClassification -Exception $_.Exception

    Write-StructuredLog -Message "Request failed" -Level Error -CorrelationId $CorrelationId -Metadata @{
        error_class = $errorClass
        error_message = $_.Exception.Message
        uri = $uri
    }

    switch ($errorClass) {
        'TRANSIENT' {
            # Retry logic handled by caller or retry wrapper
            throw [TransientException]::new($_.Exception.Message, $_.Exception)
        }
        'POLICY_VIOLATION' {
            throw [PolicyViolationException]::new("Access denied: $($_.Exception.Message)")
        }
        default {
            throw [PermanentException]::new($_.Exception.Message, $_.Exception)
        }
    }
}
```

---

## Retry Logic

### Exponential Backoff

```powershell
# utilities/RetryLogic.ps1

function Invoke-RetryWithBackoff {
    <#
    .SYNOPSIS
        Execute script block with exponential backoff retry.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [scriptblock]$ScriptBlock,

        [Parameter()]
        [int]$MaxAttempts = 5,

        [Parameter()]
        [int]$BaseDelaySeconds = 4,

        [Parameter()]
        [int]$MaxDelaySeconds = 60,

        [Parameter()]
        [string]$CorrelationId,

        [Parameter()]
        [string]$OperationName = "Operation"
    )

    $attempt = 0
    $lastException = $null

    while ($attempt -lt $MaxAttempts) {
        $attempt++

        try {
            $result = & $ScriptBlock
            return $result
        }
        catch {
            $lastException = $_.Exception

            if (-not (Test-TransientError -Exception $lastException)) {
                Write-StructuredLog -Message "Non-transient error, not retrying" -Level Warning -CorrelationId $CorrelationId -Metadata @{
                    operation = $OperationName
                    error_class = (Get-ErrorClassification -Exception $lastException)
                }
                throw
            }

            if ($attempt -ge $MaxAttempts) {
                Write-StructuredLog -Message "Max retries exceeded" -Level Error -CorrelationId $CorrelationId -Metadata @{
                    operation = $OperationName
                    attempts = $attempt
                }
                throw
            }

            # Calculate delay with jitter
            $delay = [Math]::Min($BaseDelaySeconds * [Math]::Pow(2, $attempt - 1), $MaxDelaySeconds)
            $jitter = Get-Random -Minimum 0 -Maximum ($delay * 0.1)
            $delay += $jitter

            Write-StructuredLog -Message "Retrying after delay" -Level Warning -CorrelationId $CorrelationId -Metadata @{
                operation = $OperationName
                attempt = $attempt
                max_attempts = $MaxAttempts
                delay_seconds = $delay
                error_message = $lastException.Message
            }

            Start-Sleep -Seconds $delay
        }
    }
}
```

### Usage

```powershell
$result = Invoke-RetryWithBackoff -ScriptBlock {
    Invoke-GraphRequest -Uri $graphUri -Method POST -Body $body
} -MaxAttempts 5 -CorrelationId $CorrelationId -OperationName "Graph API Call"
```

---

## Idempotency

### Idempotency Key Tracking

```powershell
# utilities/Idempotency.ps1

function Test-IdempotencyKey {
    <#
    .SYNOPSIS
        Check if operation was already performed.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Key,

        [Parameter()]
        [string]$StorePath = "$env:APPDATA\EUCORA\idempotency"
    )

    $keyFile = Join-Path $StorePath "$Key.json"
    return Test-Path $keyFile
}

function Set-IdempotencyKey {
    <#
    .SYNOPSIS
        Record completed operation for idempotency.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Key,

        [Parameter()]
        [hashtable]$Result = @{},

        [Parameter()]
        [string]$StorePath = "$env:APPDATA\EUCORA\idempotency"
    )

    if (-not (Test-Path $StorePath)) {
        New-Item -Path $StorePath -ItemType Directory -Force | Out-Null
    }

    $record = @{
        key = $Key
        timestamp = (Get-Date -Format "o")
        result = $Result
    }

    $keyFile = Join-Path $StorePath "$Key.json"
    $record | ConvertTo-Json -Depth 10 | Set-Content -Path $keyFile -Encoding UTF8
}

function Get-IdempotencyResult {
    <#
    .SYNOPSIS
        Get result of previously completed operation.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Key,

        [Parameter()]
        [string]$StorePath = "$env:APPDATA\EUCORA\idempotency"
    )

    $keyFile = Join-Path $StorePath "$Key.json"
    if (Test-Path $keyFile) {
        return Get-Content $keyFile | ConvertFrom-Json
    }
    return $null
}
```

### Idempotent Operation Pattern

```powershell
function Publish-Package {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$PackageId,

        [Parameter(Mandatory)]
        [string]$CorrelationId
    )

    # Use correlation ID as idempotency key
    $idempotencyKey = "$PackageId-$CorrelationId"

    # Check if already completed
    if (Test-IdempotencyKey -Key $idempotencyKey) {
        $existing = Get-IdempotencyResult -Key $idempotencyKey
        Write-StructuredLog -Message "Operation already completed" -Level Info -CorrelationId $CorrelationId -Metadata @{
            idempotency_key = $idempotencyKey
            previous_result = $existing.result
        }
        return $existing.result
    }

    try {
        # Perform the operation
        $result = Invoke-IntunePackageUpload -PackageId $PackageId -CorrelationId $CorrelationId

        # Record completion
        Set-IdempotencyKey -Key $idempotencyKey -Result @{
            status = 'success'
            intune_id = $result.id
        }

        return $result
    }
    catch {
        # Don't record failed operations (allow retry)
        throw
    }
}
```

---

## Configuration Management

### Configuration Functions

```powershell
# utilities/Configuration.ps1

$script:ConfigCache = @{}

function Get-ConfigValue {
    <#
    .SYNOPSIS
        Get configuration value with caching.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Key,

        [Parameter()]
        [string]$ConfigPath = "$PSScriptRoot/../config/settings.json",

        [Parameter()]
        $Default = $null
    )

    # Check cache
    if ($script:ConfigCache.ContainsKey($ConfigPath)) {
        $config = $script:ConfigCache[$ConfigPath]
    }
    else {
        if (-not (Test-Path $ConfigPath)) {
            return $Default
        }
        $config = Get-Content $ConfigPath | ConvertFrom-Json -AsHashtable
        $script:ConfigCache[$ConfigPath] = $config
    }

    # Navigate nested keys (e.g., "connectors.intune.timeout")
    $value = $config
    foreach ($part in $Key.Split('.')) {
        if ($value -is [hashtable] -and $value.ContainsKey($part)) {
            $value = $value[$part]
        }
        elseif ($value -is [PSCustomObject] -and $value.PSObject.Properties[$part]) {
            $value = $value.$part
        }
        else {
            return $Default
        }
    }

    return $value
}

function Get-ConnectorConfig {
    <#
    .SYNOPSIS
        Get connector-specific configuration.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [ValidateSet('intune', 'jamf', 'sccm', 'landscape', 'ansible')]
        [string]$Name
    )

    $configPath = "$PSScriptRoot/../config/connectors/$Name.json"

    if (-not (Test-Path $configPath)) {
        throw "Connector config not found: $configPath"
    }

    return Get-Content $configPath | ConvertFrom-Json -AsHashtable
}
```

---

## HTTP Request Wrapper

### Connector Request Function

```powershell
# utilities/HttpClient.ps1

function Invoke-ConnectorRequest {
    <#
    .SYNOPSIS
        Make HTTP request with standard error handling and logging.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Uri,

        [Parameter()]
        [ValidateSet('GET', 'POST', 'PUT', 'PATCH', 'DELETE')]
        [string]$Method = 'GET',

        [Parameter()]
        [hashtable]$Headers = @{},

        [Parameter()]
        $Body,

        [Parameter(Mandatory)]
        [string]$CorrelationId,

        [Parameter()]
        [int]$TimeoutSeconds = 30
    )

    # Add standard headers
    $Headers['X-Correlation-ID'] = $CorrelationId
    $Headers['X-Idempotency-Key'] = $CorrelationId

    $requestParams = @{
        Uri = $Uri
        Method = $Method
        Headers = $Headers
        TimeoutSec = $TimeoutSeconds
        ContentType = 'application/json'
    }

    if ($Body) {
        if ($Body -is [hashtable] -or $Body -is [PSCustomObject]) {
            $requestParams.Body = $Body | ConvertTo-Json -Depth 10
        }
        else {
            $requestParams.Body = $Body
        }
    }

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        $response = Invoke-RestMethod @requestParams

        $stopwatch.Stop()

        Write-StructuredLog -Message "HTTP request completed" -Level Debug -CorrelationId $CorrelationId -Metadata @{
            uri = $Uri
            method = $Method
            duration_ms = $stopwatch.ElapsedMilliseconds
        }

        return $response
    }
    catch {
        $stopwatch.Stop()

        Write-StructuredLog -Message "HTTP request failed" -Level Warning -CorrelationId $CorrelationId -Metadata @{
            uri = $Uri
            method = $Method
            duration_ms = $stopwatch.ElapsedMilliseconds
            error = $_.Exception.Message
        }

        throw
    }
}
```

---

## Testing Patterns

### Pester Test Structure

```powershell
# testing/unit/Logging.Tests.ps1

Describe "Write-StructuredLog" {
    BeforeAll {
        . "$PSScriptRoot/../../utilities/Logging.ps1"
    }

    Context "When logging with correlation ID" {
        It "Should include correlation_id in output" {
            $output = Write-StructuredLog -Message "Test" -CorrelationId "test-123" 6>&1

            $parsed = $output | ConvertFrom-Json
            $parsed.correlation_id | Should -Be "test-123"
        }
    }

    Context "When logging with metadata" {
        It "Should include metadata in output" {
            $output = Write-StructuredLog -Message "Test" -Metadata @{ key = "value" } 6>&1

            $parsed = $output | ConvertFrom-Json
            $parsed.metadata.key | Should -Be "value"
        }
    }

    Context "Error level logging" {
        It "Should set level to ERROR" {
            $output = Write-StructuredLog -Message "Error test" -Level Error 6>&1

            $parsed = $output | ConvertFrom-Json
            $parsed.level | Should -Be "ERROR"
        }
    }
}
```

---

## Code Suppression Annotations

When PSScriptAnalyzer flags issues that are intentional, use suppression:

```powershell
# Suppress for entire file
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '', Justification = 'Structured logging to console is intentional')]
param()

# Suppress for specific function
function Write-StructuredLog {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '', Justification = 'Console output for structured logs')]
    [CmdletBinding()]
    param(...)
}

# Suppress unused parameter (interface compatibility)
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', 'Unused', Justification = 'Required for interface compatibility')]
```
