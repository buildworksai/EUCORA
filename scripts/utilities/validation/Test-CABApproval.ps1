# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Validate CAB approval record exists and is current.
.DESCRIPTION
Checks event store record for approval status, expiry, and conditions; mocks event store in tests.
.PARAMETER ApprovalId
Approval identifier (string).
.PARAMETER EventStoreConnectionString
Optional path to event store file.
.PARAMETER CurrentTime
Override timestamp for testing.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/05-cab-approval-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Get-CABRecords {
    param([string]$Path)
    if (-not (Test-Path -Path $Path)) { return @() }
    $content = Get-Content -Path $Path -Raw
    return @( (ConvertFrom-Json $content).cab )
}
function Test-CABApproval {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$ApprovalId,
        [string]$EventStoreConnectionString,
        [datetime]$CurrentTime = (Get-Date).ToUniversalTime()
    )
    if (-not $EventStoreConnectionString) {
        throw 'Event store path required'
    }
    $records = Get-CABRecords -Path $EventStoreConnectionString
    $record = $records | Where-Object { $_.approval_id -eq $ApprovalId }
    if (-not $record) {
        return [pscustomobject]@{ IsApproved = $false; Status = 'missing'; ExpiryDate = $null; Conditions = @() }
    }
    $isApproved = $record.status -eq 'approved'
    $isExpired = $record.expiry -lt $CurrentTime
    return [pscustomobject]@{
        IsApproved = ($isApproved -and -not $isExpired)
        Status = $record.status
        ExpiryDate = $record.expiry
        Conditions = $record.conditions
    }
}
