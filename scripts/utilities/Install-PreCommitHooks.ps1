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

# Suppress Write-Host warnings for user-facing output
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingWriteHost', '', Justification = 'User-facing script requires colored output')]

Write-Output "`n🔧 EUCORA Pre-Commit Hook Installation"
Write-Output "========================================`n"

# Check if Python is installed
Write-Output "Checking prerequisites..."

try {
    $pythonVersion = python --version 2>&1
    Write-Output "✓ Python found: $pythonVersion"
} catch {
    Write-Error "❌ Python not found. Please install Python 3.8+ from https://www.python.org/"
    exit 1
}

# Check if pre-commit is installed
Write-Output "`nChecking for pre-commit..."

try {
    $precommitVersion = pre-commit --version 2>&1
    Write-Output "✓ pre-commit found: $precommitVersion"
} catch {
    Write-Output "⚠ pre-commit not found. Installing..."
    pip install pre-commit

    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to install pre-commit"
        exit 1
    }
    Write-Output "✓ pre-commit installed successfully"
}

# Check if PSScriptAnalyzer is installed
Write-Output "`nChecking for PSScriptAnalyzer..."

$psaInstalled = Get-Module -ListAvailable -Name PSScriptAnalyzer

if (-not $psaInstalled) {
    Write-Output "⚠ PSScriptAnalyzer not found. Installing..."
    Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser
    Write-Output "✓ PSScriptAnalyzer installed successfully"
} else {
    Write-Output "✓ PSScriptAnalyzer found: $($psaInstalled.Version)"
}

# Install pre-commit hooks
Write-Output "`nInstalling pre-commit hooks..."

try {
    pre-commit install

    if ($LASTEXITCODE -ne 0) {
        Write-Error "❌ Failed to install pre-commit hooks"
        exit 1
    }

    Write-Output "✓ Pre-commit hooks installed successfully"
} catch {
    Write-Error "❌ Failed to install pre-commit hooks: $($_.Exception.Message)"
    exit 1
}

# Run pre-commit on all files to verify
Write-Output "`nRunning initial pre-commit check..."
Write-Output "(This may take a few minutes on first run)`n"

pre-commit run --all-files

if ($LASTEXITCODE -eq 0) {
    Write-Output "`n✅ All checks passed!"
} else {
    Write-Output "`n⚠ Some checks failed. Review the output above."
    Write-Output "You can fix issues and run 'pre-commit run --all-files' again."
}

Write-Output "`n========================================"
Write-Output "✅ Pre-commit hooks installation complete!"
Write-Output "`nNext steps:"
Write-Output "  1. Pre-commit hooks will run automatically on 'git commit'"
Write-Output "  2. To run manually: pre-commit run --all-files"
Write-Output "  3. To update hooks: pre-commit autoupdate"
Write-Output "`nFor more info: https://pre-commit.com`n"
