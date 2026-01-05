# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Generate or validate deterministic correlation IDs for deployment artifacts.
.DESCRIPTION
`Get-CorrelationId` produces UUIDv4 values or prefixed IDs (deployment/evidence/CAB) with optional seeding for deterministic tests; `Test-CorrelationId` validates format and optional prefix restrictions.
.PARAMETER Type
Type of correlation ID to emit: uuid, deployment, evidence, or cab.
.PARAMETER Seed
Optional integer seed to make generation deterministic (use only in tests).
.PARAMETER CorrelationId
The correlation ID to validate.
.PARAMETER Type
(Type parameter reused by Test-CorrelationId) Optional prefix constraint when validating.
.EXAMPLE
PS> Get-CorrelationId -Type deployment
Outputs: dp-20260104-a1b2
.EXAMPLE
PS> Test-CorrelationId -CorrelationId "dp-20260104-1a2b" -Type deployment
Returns: True
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: docs/architecture/control-plane-design.md, .agents/rules/08-connector-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function New-DeterministicGuid {
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'Helper function that does not change system state')]
    param([System.Random]$Random)
    $bytes = [byte[]]::new(16)
    for ($i = 0; $i -lt 16; $i++) {
        $bytes[$i] = [byte]$Random.Next(0, 256)
    }
    $bytes[6] = ($bytes[6] -band 0x0f) -bor 0x40
    $bytes[8] = ($bytes[8] -band 0x3f) -bor 0x80
    return [guid]::new(([System.BitConverter]::ToString($bytes) -replace '-', ''))
}
function Get-CorrelationId {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $false)]
        [ValidateSet('deployment','evidence','cab','uuid')]
        [string]$Type = 'uuid',
        [Parameter(Mandatory = $false)]
        [int]$Seed
    )
    $random = if ($PSBoundParameters.ContainsKey('Seed')) {
        [System.Random]::new($Seed)
    } else {
        [System.Random]::new()
    }
    $guid = New-DeterministicGuid -Random $random
    switch ($Type) {
        'uuid' {
            return $guid.ToString()
        }
        'deployment' {
            $date = (Get-Date).ToString('yyyyMMdd')
            $shortGuid = $guid.ToString().Substring(0, 4)
            return "dp-$date-$shortGuid"
        }
        'evidence' {
            $shortGuid = ($guid.ToString() -replace '-', '')[0..7] -join ''
            return "ep-$shortGuid"
        }
        'cab' {
            $date = (Get-Date).ToString('yyyyMMdd')
            $shortGuid = $guid.ToString().Substring(0, 3)
            return "cab-$date-$shortGuid"
        }
    }
}
function Test-CorrelationId {
    [CmdletBinding()]
    param (
        [Parameter(Mandatory = $true)]
        [string]$CorrelationId,
        [Parameter(Mandatory = $false)]
        [ValidateSet('deployment','evidence','cab','uuid','any')]
        [string]$Type = 'any'
    )
    $patterns = @{
        uuid = '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        deployment = '^dp-[0-9]{8}-[0-9a-f]{4}$'
        evidence = '^ep-[0-9a-f]{8}$'
        cab = '^cab-[0-9]{8}-[0-9a-f]{3}$'
        any = '^[0-9a-z-]+$'
    }
    if ($Type -eq 'any') {
        return $CorrelationId -match $patterns.any
    }
    return $CorrelationId -match $patterns[$Type]
}
