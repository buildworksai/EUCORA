# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    AWX/Tower connector implementation for Ansible-based deployments.
.DESCRIPTION
    Launches idempotent AWX job templates to install or remove artifacts, inspects job status, retrieves job logs, and surfaces target hosts while tagging every operation with the control plane correlation id for audit.
.NOTES
Version: 2.0
Author: Platform Engineering
Related Docs: docs/modules/ansible/connector-spec.md, .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../common/ConnectorBase.ps1"

function Get-AnsibleHeaders {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    $headers = @{
        Authorization = "Bearer $($config.token)"
        Accept = 'application/json'
        'Content-Type' = 'application/json'
        'X-Correlation-Id' = $CorrelationId
    }
    return $headers
}

function Build-AnsibleLaunchPayload {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $extraVars = @{
        correlation_id    = $CorrelationId
        artifact_id       = $DeploymentIntent.ArtifactId
        ring              = $DeploymentIntent.Ring
        target_inventory  = $DeploymentIntent.Inventory
        manifest_hash     = $DeploymentIntent.ManifestHash
        deployment_intent = $DeploymentIntent
    }
    if ($DeploymentIntent.ContainsKey('Scopes')) {
        $extraVars.scope = $DeploymentIntent.Scopes
    }

    # Support for job template surveys (additional variables)
    if ($DeploymentIntent.ContainsKey('SurveyAnswers')) {
        foreach ($key in $DeploymentIntent.SurveyAnswers.Keys) {
            $extraVars[$key] = $DeploymentIntent.SurveyAnswers[$key]
        }
    }

    return @{
        extra_vars = $extraVars
    }
}

function Get-AnsibleJobResults {
    <#
    .SYNOPSIS
        Parse job results from AWX job events.
    .PARAMETER JobId
        AWX job ID.
    .PARAMETER AccessToken
        AWX API token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $results = Get-AnsibleJobResults -JobId 123 -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$JobId,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    $baseUri = $config.tower_api_url.TrimEnd('/')
    $eventsUri = "$baseUri/jobs/$JobId/job_events/"

    $headers = Get-AnsibleHeaders -CorrelationId $CorrelationId

    $response = Invoke-ConnectorRequest -Uri $eventsUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    if ($response.status -eq 'failed') {
        return @{
            success_count = 0
            failure_count = 0
            total_hosts = 0
        }
    }

    $events = $response.results

    # Parse events for success/failure counts
    $successEvents = $events | Where-Object { $_.event -eq 'runner_on_ok' }
    $failureEvents = $events | Where-Object { $_.event -in @('runner_on_failed', 'runner_on_unreachable') }

    # Get unique hosts
    $allHosts = $events | Where-Object { $_.host } | Select-Object -ExpandProperty host -Unique

    return @{
        success_count = $successEvents.Count
        failure_count = $failureEvents.Count
        total_hosts = $allHosts.Count
        success_rate = if ($allHosts.Count -gt 0) { ($successEvents.Count / $allHosts.Count) * 100 } else { 0 }
    }
}

function Get-AnsibleJobLog {
    <#
    .SYNOPSIS
        Retrieve job log (stdout) for debugging.
    .PARAMETER JobId
        AWX job ID.
    .PARAMETER AccessToken
        AWX API token.
    .PARAMETER CorrelationId
        Correlation ID for audit trail.
    .EXAMPLE
        $log = Get-AnsibleJobLog -JobId 123 -AccessToken $token -CorrelationId $cid
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$JobId,

        [Parameter(Mandatory = $true)]
        [string]$AccessToken,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    $baseUri = $config.tower_api_url.TrimEnd('/')
    $logUri = "$baseUri/jobs/$JobId/stdout/?format=txt"

    $headers = Get-AnsibleHeaders -CorrelationId $CorrelationId

    try {
        $logContent = Invoke-RestMethod -Uri $logUri -Method 'GET' -Headers $headers -TimeoutSec 60

        Write-StructuredLog -Level 'Debug' -Message 'Ansible job log retrieved' -CorrelationId $CorrelationId -Metadata @{
            job_id = $JobId
            log_size = $logContent.Length
        }

        return $logContent
    }
    catch {
        Write-StructuredLog -Level 'Warning' -Message "Failed to retrieve Ansible job log: $($_.Exception.Message)" -CorrelationId $CorrelationId
        return $null
    }
}

function Publish-AnsibleApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [hashtable]$DeploymentIntent,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    if (-not $config.tower_api_url -or -not $config.token) {
        Write-StructuredLog -Level 'Warning' -Message 'Ansible connector missing configuration, returning stub' -CorrelationId $CorrelationId -Metadata @{ connector = 'ansible' }
        return @{
            status = 'stubbed'
            correlation_id = $CorrelationId
            connector = 'ansible'
        }
    }

    $templateId = if ($DeploymentIntent.ContainsKey('JobTemplateId') -and $DeploymentIntent.JobTemplateId) { $DeploymentIntent.JobTemplateId } else { $config.job_template_id }
    if (-not $templateId) {
        throw "Missing job template id for Ansible publish"
    }

    $headers = Get-AnsibleHeaders -CorrelationId $CorrelationId
    $baseUri = $config.tower_api_url.TrimEnd('/')
    $idempotencyUri = "$baseUri/jobs/?search=correlation_id:$CorrelationId"
    try {
        $existing = Invoke-ConnectorRequest -Uri $idempotencyUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId
        if ($existing -and $existing.ContainsKey('results') -and $existing.results.Count -gt 0) {
            $job = $existing.results[0]
            Write-StructuredLog -Level 'Info' -Message 'Idempotent launch detected' -CorrelationId $CorrelationId -Metadata @{ job_id = $job.id; connector = 'ansible' }
            return @{
                status = 'already_launched'
                correlation_id = $CorrelationId
                job = $job
                connector = 'ansible'
            }
        }
    }
    catch {
        Write-StructuredLog -Level 'Debug' -Message "Ansible idempotency probe failed: $($_.Exception.Message)" -CorrelationId $CorrelationId -Metadata @{ connector = 'ansible' }
    }

    $payload = Build-AnsibleLaunchPayload -DeploymentIntent $DeploymentIntent -CorrelationId $CorrelationId
    $launchUri = "$baseUri/job_templates/$templateId/launch/"
    $response = Invoke-ConnectorRequest -Uri $launchUri -Method 'POST' -Body $payload -Headers $headers -CorrelationId $CorrelationId

    return @{
        status = 'launched'
        correlation_id = $CorrelationId
        connector = 'ansible'
        awx_response = $response
    }
}

function Remove-AnsibleApplication {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ApplicationId,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    if (-not $config.tower_api_url -or -not $config.token) {
        Write-StructuredLog -Level 'Warning' -Message 'Ansible connector missing configuration, returning stub for remove' -CorrelationId $CorrelationId -Metadata @{ connector = 'ansible' }
        return @{
            status = 'stubbed'
            correlation_id = $CorrelationId
            connector = 'ansible'
        }
    }

    $rollbackTemplateId = $config.rollback_job_template_id
    if (-not $rollbackTemplateId) {
        throw 'Rollback job template id is required for Ansible removals'
    }

    $headers = Get-AnsibleHeaders -CorrelationId $CorrelationId
    $baseUri = $config.tower_api_url.TrimEnd('/')
    $payload = @{
        extra_vars = @{
            correlation_id = $CorrelationId
            application_id = $ApplicationId
            action = 'rollback'
        }
    }

    $removeUri = "$baseUri/job_templates/$rollbackTemplateId/launch/"
    $response = Invoke-ConnectorRequest -Uri $removeUri -Method 'POST' -Body $payload -Headers $headers -CorrelationId $CorrelationId

    return @{
        status = 'rollback_launched'
        correlation_id = $CorrelationId
        connector = 'ansible'
        awx_response = $response
    }
}

function Get-AnsibleDeploymentStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    if (-not $config.tower_api_url -or -not $config.token) {
        return @{
            status = 'disabled'
            correlation_id = $CorrelationId
            connector = 'ansible'
        }
    }

    $headers = Get-AnsibleHeaders -CorrelationId $CorrelationId
    $baseUri = $config.tower_api_url.TrimEnd('/')
    $statusUri = "$baseUri/jobs/?search=correlation_id:$CorrelationId"
    $response = Invoke-ConnectorRequest -Uri $statusUri -Method 'GET' -Headers $headers -CorrelationId $CorrelationId

    if ($response.status -eq 'failed') {
        return $response
    }

    $jobs = $response.results
    if ($jobs.Count -eq 0) {
        return @{
            status = 'not_found'
            correlation_id = $CorrelationId
            connector = 'ansible'
        }
    }

    # Get job results for first matching job
    $job = $jobs[0]
    $jobResults = Get-AnsibleJobResults -JobId $job.id -AccessToken $config.token -CorrelationId $CorrelationId

    return @{
        status = 'queried'
        correlation_id = $CorrelationId
        connector = 'ansible'
        job_id = $job.id
        job_status = $job.status
        success_count = $jobResults.success_count
        failure_count = $jobResults.failure_count
        total_hosts = $jobResults.total_hosts
        success_rate = $jobResults.success_rate
    }
}

function Test-AnsibleConnection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$AuthToken
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    if (-not $config.tower_api_url -or -not $config.token) {
        Write-StructuredLog -Level 'Warning' -Message 'Ansible connector disabled (missing config)' -CorrelationId (Get-CorrelationId -Type uuid)
        return @{
            connector = 'ansible'
            status = 'disabled'
            checked_at = (Get-Date).ToString('o')
        }
    }

    try {
        $statusUri = "$($config.tower_api_url.TrimEnd('/'))/ping/"
        $response = Invoke-ConnectorRequest -Uri $statusUri -Method 'GET' -Headers (Get-AnsibleHeaders -CorrelationId (Get-CorrelationId -Type uuid)) -CorrelationId (Get-CorrelationId -Type uuid)
        return @{
            connector = 'ansible'
            status = if ($response.status -eq 'failed') { 'degraded' } else { 'ready' }
            target = $config.tower_api_url
            checked_at = (Get-Date).ToString('o')
        }
    }
    catch {
        Write-StructuredLog -Level 'Warning' -Message "Ansible ping failed: $($_.Exception.Message)" -CorrelationId (Get-CorrelationId -Type uuid)
        return @{
            connector = 'ansible'
            status = 'error'
            error = $_.Exception.Message
            checked_at = (Get-Date).ToString('o')
        }
    }
}

function Get-AnsibleTargetDevices {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Ring
    )

    $config = Get-ConnectorConfig -Name 'ansible'
    if (-not $config.tower_api_url -or -not $config.token -or -not $config.inventory_id) {
        return @()
    }

    $headers = Get-AnsibleHeaders -CorrelationId (Get-CorrelationId -Type uuid)
    $inventoryId = $config.inventory_id
    $hostsUri = "$($config.tower_api_url.TrimEnd('/'))/inventories/$inventoryId/hosts/"
    $response = Invoke-ConnectorRequest -Uri $hostsUri -Method 'GET' -Headers $headers -CorrelationId (Get-CorrelationId -Type uuid)
    $hosts = if ($response.ContainsKey('results')) { $response.results } else { @() }

    return $hosts | ForEach-Object {
        [ordered]@{
            device_id = $_.name
            host_id = $_.id
            ring = $Ring
            inventory = $inventoryId
            last_seen = $_.last_modified
        }
    }
}
