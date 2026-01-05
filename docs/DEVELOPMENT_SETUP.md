# Development Setup Guide

**SPDX-License-Identifier: Apache-2.0**

This guide covers setting up your development environment for EUCORA with all quality gates and compliance checks.

---

## Prerequisites

### Required Software

1. **PowerShell 7+**
   ```bash
   # macOS/Linux
   brew install powershell
   
   # Windows
   winget install Microsoft.PowerShell
   ```

2. **Python 3.8+**
   ```bash
   # macOS
   brew install python
   
   # Windows
   winget install Python.Python.3.12
   ```

3. **Git**
   ```bash
   # macOS
   brew install git
   
   # Windows
   winget install Git.Git
   ```

---

## Quick Setup

### 1. Clone Repository

```bash
git clone https://github.com/buildworksai/EUCORA.git
cd EUCORA
```

### 2. Install Pre-Commit Hooks

```bash
# Automated installation (recommended)
pwsh -File scripts/utilities/Install-PreCommitHooks.ps1
```

**Or manually:**

```bash
# Install pre-commit
pip install pre-commit

# Install PSScriptAnalyzer
pwsh -Command "Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser"

# Install hooks
pre-commit install
```

### 3. Verify Setup

```bash
# Run all pre-commit checks
pre-commit run --all-files
```

---

## Pre-Commit Hooks

The following checks run automatically on every commit:

### ✅ File Quality Checks
- Trailing whitespace removal
- End-of-file fixing
- YAML/JSON syntax validation
- Merge conflict detection
- Large file detection (>5MB)
- Line ending normalization (LF)

### ✅ PowerShell Quality
- **PSScriptAnalyzer** with PSGallery settings
- Zero tolerance for errors and warnings

### ✅ SPDX Compliance
- Verifies all `.ps1` files have SPDX headers
- Blocks commits with missing headers

### ✅ Branch Protection
- Prevents direct commits to `main` or `master`

---

## Manual Commands

### Run Pre-Commit Checks

```bash
# All files
pre-commit run --all-files

# Specific hook
pre-commit run check-spdx-headers --all-files

# Staged files only
pre-commit run
```

### Add SPDX Headers

```bash
# Dry run (shows what would change)
pwsh -File scripts/utilities/Add-SPDXHeaders.ps1 -DryRun

# Apply headers
pwsh -File scripts/utilities/Add-SPDXHeaders.ps1
```

### PowerShell Linting

```bash
pwsh -Command "Invoke-ScriptAnalyzer -Path . -Recurse -Settings PSGallery"
```

---

## CI/CD Workflows

### GitHub Actions

Two workflows run automatically on push/PR:

#### 1. **Code Quality** (`.github/workflows/code-quality.yml`)
- SPDX compliance
- PowerShell linting
- File quality checks
- Branding compliance

#### 2. **SPDX Compliance** (`.github/workflows/spdx-compliance.yml`)
- Dedicated SPDX header verification
- Automatic PR comments on failures

### Workflow Triggers

```yaml
on:
  push:
    branches: [ main, develop, feature/** ]
  pull_request:
    branches: [ main, develop ]
```

---

## Troubleshooting

### Pre-Commit Hook Failures

**Issue**: SPDX compliance check fails

```bash
# Fix automatically
pwsh -File scripts/utilities/Add-SPDXHeaders.ps1

# Commit changes
git add .
git commit -m "Add SPDX headers"
```

**Issue**: PSScriptAnalyzer errors

```bash
# View detailed errors
pwsh -Command "Invoke-ScriptAnalyzer -Path . -Recurse -Settings PSGallery"

# Fix issues manually, then commit
```

**Issue**: Pre-commit hook won't run

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Update hooks to latest versions
pre-commit autoupdate
```

### Bypassing Hooks (Emergency Only)

```bash
# Skip pre-commit hooks (NOT RECOMMENDED)
git commit --no-verify -m "Emergency fix"
```

⚠️ **Warning**: Bypassing hooks will cause CI/CD failures. Only use in emergencies.

---

## Best Practices

### Before Committing

1. ✅ Run `pre-commit run --all-files`
2. ✅ Verify SPDX headers on new files
3. ✅ Check PSScriptAnalyzer passes
4. ✅ Test your changes locally

### Writing PowerShell

1. ✅ Always include SPDX header (first 3 lines)
2. ✅ Use comment-based help (`.SYNOPSIS`, `.DESCRIPTION`, etc.)
3. ✅ Follow PSScriptAnalyzer rules
4. ✅ Use `Set-StrictMode -Version Latest`
5. ✅ Set `$ErrorActionPreference = 'Stop'`

### Example PowerShell File

```powershell
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 BuildWorks.AI
#
<#
.SYNOPSIS
    Brief description
.DESCRIPTION
    Detailed description
.EXAMPLE
    .\MyScript.ps1
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Your code here
```

---

## Additional Resources

- [Pre-Commit Documentation](https://pre-commit.com)
- [PSScriptAnalyzer Rules](https://github.com/PowerShell/PSScriptAnalyzer)
- [SPDX Specification](https://spdx.dev/specifications/)
- [EUCORA Contributing Guide](../CONTRIBUTING.md)
- [EUCORA Agents Rules](../.agents/rules/)

---

## Getting Help

1. **Check Documentation**: Review `.agents/rules/` for specific guidelines
2. **Run Diagnostics**: `pre-commit run --all-files --verbose`
3. **Review Logs**: Check `.git/hooks/pre-commit` for hook details

---

*Build by BuildWorks.AI*

**SPDX-License-Identifier: Apache-2.0**
