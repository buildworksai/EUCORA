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
        Write-Host "✓ Already has SPDX: $FilePath" -ForegroundColor Green
        return $false
    }

    $content = Get-Content $FilePath -Raw
    $newContent = $spdxHeader + $content

    if ($DryRun) {
        Write-Host "Would add SPDX to: $FilePath" -ForegroundColor Yellow
        return $true
    }

    Set-Content -Path $FilePath -Value $newContent -NoNewline
    Write-Host "✓ Added SPDX to: $FilePath" -ForegroundColor Cyan
    return $true
}

# Find all PowerShell files
$ps1Files = Get-ChildItem -Path $Path -Filter "*.ps1" -Recurse -File | 
    Where-Object { $_.FullName -notmatch 'node_modules|\.venv|\.git' }

Write-Host "`nScanning $($ps1Files.Count) PowerShell files..." -ForegroundColor White
Write-Host "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'APPLY CHANGES' })`n" -ForegroundColor $(if ($DryRun) { 'Yellow' } else { 'Green' })

$modified = 0
$skipped = 0

foreach ($file in $ps1Files) {
    if (Add-SPDXHeader -FilePath $file.FullName) {
        $modified++
    } else {
        $skipped++
    }
}

Write-Host "`n=== Summary ===" -ForegroundColor White
Write-Host "Total files: $($ps1Files.Count)"
Write-Host "Modified: $modified" -ForegroundColor Cyan
Write-Host "Skipped (already compliant): $skipped" -ForegroundColor Green

if ($DryRun) {
    Write-Host "`nRun without -DryRun to apply changes." -ForegroundColor Yellow
}
