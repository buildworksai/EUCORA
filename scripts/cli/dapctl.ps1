# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#<#+
.SYNOPSIS
    Desktop Application Packaging & Deployment Factory CLI entry point.
.DESCRIPTION
    Dispatches to the requested command after authenticating via Entra ID or environment token.
.PARAMETER Command
    One of the supported dapctl commands (deploy, status, rollback, health, etc.).
.PARAMETER Arguments
    Additional arguments passed to the command script.
.EXAMPLE
    .\dapctl.ps1 -Command health
.NOTES
Version: 1.0
Author: Platform Engineering
Related Docs: docs/planning/phase-2-cli-control-plane-prompt.md
#>
param(
    [Parameter(Mandatory = $false, Position = 0)]
    [ValidateSet('health','deploy','status','rollback','approve','risk-score','evidence','logs','config','rings','connectors','test-connection','version')]
    [string]$Command = 'health',

    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$Arguments = @()
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$invokedDirectly = ($MyInvocation.InvocationName -ne '.')
if ($invokedDirectly -and -not $PSBoundParameters.ContainsKey('Command')) {
    throw 'Command parameter is required.'
}

function Invoke-Dapctl {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $false)]
        [AllowEmptyCollection()]
        [object[]]$Arguments = @()
    )

    $modulesPath = Join-Path $PSScriptRoot 'modules'
    . (Join-Path $modulesPath 'Initialize-Auth.ps1')
    . (Join-Path $modulesPath 'Format-Output.ps1')
    . (Join-Path $modulesPath 'Write-ErrorMessage.ps1')

    $token = Initialize-Auth
    $commandScript = Join-Path $PSScriptRoot ("commands/Invoke-$Command.ps1")
    if (-not (Test-Path -Path $commandScript)) {
        Write-ErrorMessage -Message "Unknown command: $Command"
        return 1
    }

    try {
        & $commandScript -AuthToken $token @Arguments | Out-Null
    }
    catch {
        Write-ErrorMessage -Message $_.Exception.Message
        return 1
    }
    return 0
}

$shouldRunEntryPoint = ($MyInvocation.InvocationName -ne '.') `
    -and $PSCommandPath -and $MyInvocation.MyCommand.Path `
    -and $PSCommandPath -eq $MyInvocation.MyCommand.Path
if ($shouldRunEntryPoint) {
    exit (Invoke-Dapctl -Command $Command -Arguments $Arguments)
}
