# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
Validate deployment scope against publisher/app boundaries and CAB requirements.
.DESCRIPTION
Ensures target scope is subset of publisher and app scopes, and cross-boundary publishing requires CAB approval.
.PARAMETER TargetScope
Hashtable containing acquisition/business_unit/site.
.PARAMETER PublisherScope
Publisher scope hashtable.
.PARAMETER AppScope
App scope hashtable.
.PARAMETER CABApprovalId
Optional CAB approval ID for cross-boundary deployments.
.NOTES
Version: 1.0
Author: Control Plane Engineering
Related Docs: .agents/rules/09-rbac-enforcement-rules.md
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Test-ScopeValidity {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$TargetScope,
        [Parameter(Mandatory=$true)]
        [hashtable]$PublisherScope,
        [Parameter(Mandatory=$true)]
        [hashtable]$AppScope,
        [string]$CABApprovalId
    )
    $errors = @()
    $crossBoundary = $TargetScope.acquisition -ne $PublisherScope.acquisition -or $TargetScope.business_unit -ne $PublisherScope.business_unit
    foreach ($key in @('acquisition','business_unit','site')) {
        if ($TargetScope[$key] -and $PublisherScope[$key] -and $TargetScope[$key] -ne $PublisherScope[$key]) {
            if (-not ($crossBoundary -and $CABApprovalId)) {
            $errors += "Target scope exceeds publisher for $key"
            }
        }
        if ($TargetScope[$key] -and $AppScope[$key] -and $TargetScope[$key] -ne $AppScope[$key]) {
            $errors += "Target scope exceeds app for $key"
        }
    }
    $crossBoundary = $TargetScope.acquisition -ne $PublisherScope.acquisition -or $TargetScope.business_unit -ne $PublisherScope.business_unit
    if ($crossBoundary -and -not $CABApprovalId) {
        $errors += 'Cross-boundary deployment requires CAB approval'
    }
    return [pscustomobject]@{
        IsValid = ($errors.Count -eq 0)
        Errors = $errors
    }
}
