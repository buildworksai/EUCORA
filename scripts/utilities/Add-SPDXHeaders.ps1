# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#
<#
.SYNOPSIS
    Adds SPDX license headers to all PowerShell files in the repository.
.DESCRIPTION
    Scans all .ps1 files and adds Apache-2.0 SPDX headers if missing.
    Preserves existing comment blocks and code.
.PARAMETER DryRun
    If specified, shows what would be changed without modifying files.
.PARAMETER Path
    Root path to scan (default: repository root).
.EXAMPLE
    .\Add-SPDXHeaders.ps1 -DryRun
    # Shows what would be changed
.EXAMPLE
    .\Add-SPDXHeaders.ps1
    # Applies SPDX headers to all .ps1 files
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [string]$Path = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$spdxHeader = @"
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#
"@

function Test-HasSPDXHeader {
    param([string]$FilePath)

    $firstLine = Get-Content $FilePath -TotalCount 1 -ErrorAction SilentlyContinue
    return $firstLine -match 'SPDX-License-Identifier'
}

function Add-SPDXHeader {
    param([string]$FilePath)

    if (Test-HasSPDXHeader -FilePath $FilePath) {
        Write-Output "✓ Already has SPDX: $FilePath"
        return $false
    }

    $content = Get-Content $FilePath -Raw
    $newContent = $spdxHeader + $content

    if ($DryRun) {
        Write-Output "Would add SPDX to: $FilePath"
        return $true
    }

    Set-Content -Path $FilePath -Value $newContent -NoNewline
    Write-Output "✓ Added SPDX to: $FilePath"
    return $true
}

# Suppress Write-Host warnings for user-facing output
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '', Justification = 'User-facing script requires colored output')]

# Find all PowerShell files
$ps1Files = Get-ChildItem -Path $Path -Filter "*.ps1" -Recurse -File |
    Where-Object { $_.FullName -notmatch 'node_modules|\.venv|\.git' }

Write-Output "`nScanning $($ps1Files.Count) PowerShell files..."
Write-Output "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'APPLY CHANGES' })`n"

$modified = 0
$skipped = 0

foreach ($file in $ps1Files) {
    if (Add-SPDXHeader -FilePath $file.FullName) {
        $modified++
    } else {
        $skipped++
    }
}

Write-Output "`n=== Summary ==="
Write-Output "Total files: $($ps1Files.Count)"
Write-Output "Modified: $modified"
Write-Output "Skipped (already compliant): $skipped"

if ($DryRun) {
    Write-Output "`nRun without -DryRun to apply changes."
}
