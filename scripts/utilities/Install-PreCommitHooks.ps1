# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#
<#
.SYNOPSIS
    Installs and configures pre-commit hooks for EUCORA development.
.DESCRIPTION
    Sets up pre-commit hooks including SPDX compliance checks, PSScriptAnalyzer,
    and file quality checks. Requires Python and pre-commit to be installed.
.EXAMPLE
    .\Install-PreCommitHooks.ps1
    # Installs pre-commit hooks
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "`n🔧 EUCORA Pre-Commit Hook Installation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Python is installed
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "❌ Python not found. Please install Python 3.8+ from https://www.python.org/"
    exit 1
}

# Check if pre-commit is installed
Write-Host "`nChecking for pre-commit..." -ForegroundColor Yellow

try {
    $precommitVersion = pre-commit --version 2>&1
    Write-Host "✓ pre-commit found: $precommitVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠ pre-commit not found. Installing..." -ForegroundColor Yellow
    pip install pre-commit

    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to install pre-commit"
        exit 1
    }
    Write-Host "✓ pre-commit installed successfully" -ForegroundColor Green
}

# Check if PSScriptAnalyzer is installed
Write-Host "`nChecking for PSScriptAnalyzer..." -ForegroundColor Yellow

$psaInstalled = Get-Module -ListAvailable -Name PSScriptAnalyzer

if (-not $psaInstalled) {
    Write-Host "⚠ PSScriptAnalyzer not found. Installing..." -ForegroundColor Yellow
    Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser
    Write-Host "✓ PSScriptAnalyzer installed successfully" -ForegroundColor Green
} else {
    Write-Host "✓ PSScriptAnalyzer found: $($psaInstalled.Version)" -ForegroundColor Green
}

# Install pre-commit hooks
Write-Host "`nInstalling pre-commit hooks..." -ForegroundColor Yellow

try {
    pre-commit install

    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to install pre-commit hooks"
        exit 1
    }

    Write-Host "✓ Pre-commit hooks installed successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Failed to install pre-commit hooks: $($_.Exception.Message)"
    exit 1
}

# Run pre-commit on all files to verify
Write-Host "`nRunning initial pre-commit check..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes on first run)`n" -ForegroundColor Gray

pre-commit run --all-files

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All checks passed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠ Some checks failed. Review the output above." -ForegroundColor Yellow
    Write-Host "You can fix issues and run 'pre-commit run --all-files' again." -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Pre-commit hooks installation complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Pre-commit hooks will run automatically on 'git commit'" -ForegroundColor White
Write-Host "  2. To run manually: pre-commit run --all-files" -ForegroundColor White
Write-Host "  3. To update hooks: pre-commit autoupdate" -ForegroundColor White
Write-Host "`nFor more info: https://pre-commit.com`n" -ForegroundColor Gray
