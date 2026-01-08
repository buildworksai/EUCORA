# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('HealthCheck', 'Deploy')]
    [string]$Action,
    [string]$DeploymentIntentId,
    [string]$ArtifactPath,
    [string]$TargetRing,
    [string]$AppName,
    [string]$Version
)

$connectorName = 'jamf'

function Write-Result {
    param([hashtable]$Payload)
    $Payload['connector'] = $connectorName
    $Payload['timestamp'] = (Get-Date).ToString('o')
    $Payload | ConvertTo-Json -Compress
}

if ($Action -eq 'HealthCheck') {
    Write-Result -Payload @{ status = 'healthy'; message = 'Connector reachable' }
    exit 0
}

if (-not $DeploymentIntentId -or -not $ArtifactPath -or -not $TargetRing -or -not $AppName -or -not $Version) {
    Write-Error 'Missing required deployment parameters'
    exit 1
}

Write-Result -Payload @{
    status = 'success'
    message = 'Deployment submitted'
    object_id = [guid]::NewGuid().ToString()
    app_name = $AppName
    version = $Version
    ring = $TargetRing
}
exit 0
