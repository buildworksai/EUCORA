# Phase 6: Testing & Quality - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 2 weeks
**Dependencies**: All previous phases (1-5)

---

## Task Overview

Implement comprehensive testing infrastructure: unit tests, integration tests, end-to-end tests, pre-commit hooks, and quality gates. This phase ensures ≥90% code coverage, enforces PSScriptAnalyzer standards, and prevents regressions before code reaches production.

**Success Criteria**:
- ≥90% code coverage across all modules
- All unit tests pass (PSScriptAnalyzer, Pester)
- Integration tests validate end-to-end workflows
- Pre-commit hooks block commits with quality violations
- CI/CD pipeline enforces quality gates
- Test reports generated for CAB submission

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Thin Control Plane**: Tests validate orchestration only, never direct endpoint management
- ✅ **Separation of Duties**: Tests validate RBAC enforcement
- ✅ **Deterministic**: Tests produce consistent results (no flaky tests)
- ✅ **Evidence-First**: Test results included in evidence packs

### Quality Standards
- ✅ **Code Coverage**: ≥90% per module (measured with Pester CodeCoverage)
- ✅ **PSScriptAnalyzer**: ZERO errors, ZERO warnings across all scripts
- ✅ **Test Isolation**: Each test independent, no shared state
- ✅ **Fast Tests**: Unit tests complete in <5 seconds, integration tests <30 seconds
- ✅ **Mocking**: External dependencies (APIs, databases) mocked in unit tests

### Security Requirements
- ✅ **No Real Credentials**: Tests use mock credentials only
- ✅ **Sandbox Environments**: Integration tests run in isolated test environments
- ✅ **Audit Trail**: Test runs logged with correlation IDs

---

## Scope: Unit Tests (scripts/testing/unit/)

### 1. Test-UtilityFunctions.Tests.ps1

```powershell
<#
.SYNOPSIS
    Unit tests for utility functions (Phase 1).
.DESCRIPTION
    Tests all functions in scripts/utilities/ with ≥90% coverage.
#>

Describe "Get-CorrelationId" {
    It "Generates valid UUIDv4 format" {
        $cid = Get-CorrelationId
        $cid | Should -Match '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    }

    It "Includes prefix when provided" {
        $cid = Get-CorrelationId -Prefix "deploy"
        $cid | Should -Match '^deploy-[0-9a-f]{8}-'
    }

    It "Generates unique IDs across 1000 calls" {
        $ids = 1..1000 | ForEach-Object { Get-CorrelationId }
        $uniqueIds = $ids | Select-Object -Unique
        $uniqueIds.Count | Should -Be 1000
    }

    It "Rejects invalid prefix characters" {
        { Get-CorrelationId -Prefix "INVALID_PREFIX!" } | Should -Throw
    }
}

Describe "Invoke-RetryWithBackoff" {
    It "Succeeds on first try if script block succeeds" {
        $result = Invoke-RetryWithBackoff -ScriptBlock { return "Success" }
        $result | Should -Be "Success"
    }

    It "Retries exactly MaxRetries times on retryable exception" {
        $attempt = 0
        $scriptBlock = {
            $script:attempt++
            if ($script:attempt -lt 3) {
                throw [System.Net.WebException]::new("Transient error")
            }
            return "Success"
        }
        $result = Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -MaxRetries 5
        $result | Should -Be "Success"
        $attempt | Should -Be 3
    }

    It "Does not retry on non-retryable exception" {
        $attempt = 0
        $scriptBlock = {
            $script:attempt++
            throw [System.ArgumentException]::new("Permanent error")
        }
        { Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -MaxRetries 5 } | Should -Throw
        $attempt | Should -Be 1
    }

    It "Backoff delay matches 2^retry formula" {
        Mock Start-Sleep { }
        $attempt = 0
        $scriptBlock = {
            $script:attempt++
            if ($script:attempt -lt 4) {
                throw [System.Net.WebException]::new("Transient")
            }
            return "Success"
        }
        Invoke-RetryWithBackoff -ScriptBlock $scriptBlock -MaxRetries 5 -BaseDelaySeconds 1

        # Verify Start-Sleep called with correct delays: 2, 4, 8
        Assert-MockCalled Start-Sleep -Times 1 -ParameterFilter { $Seconds -eq 2 }
        Assert-MockCalled Start-Sleep -Times 1 -ParameterFilter { $Seconds -eq 4 }
        Assert-MockCalled Start-Sleep -Times 1 -ParameterFilter { $Seconds -eq 8 }
    }
}

Describe "Test-IdempotencyKey" {
    BeforeAll {
        Mock Invoke-RestMethod {
            param($Uri)
            if ($Uri -like "*correlationId=exists*") {
                return @{ value = @(@{ id = "event-123" }) }
            } else {
                return @{ value = @() }
            }
        }
    }

    It "Returns true if event exists" {
        $result = Test-IdempotencyKey -CorrelationId "exists"
        $result | Should -Be $true
    }

    It "Returns false if event does not exist" {
        $result = Test-IdempotencyKey -CorrelationId "new"
        $result | Should -Be $false
    }
}

Describe "Get-ConfigValue" {
    BeforeAll {
        $testConfig = @{ VaultUri = "https://vault.test.com"; EventStoreUri = '${EVENT_STORE_URI}' } | ConvertTo-Json
        Set-Content -Path "$TestDrive/settings.json" -Value $testConfig
        $env:EVENT_STORE_URI = "https://eventstore.test.com"
    }

    It "Reads value from settings.json" {
        Mock Get-ConfigValue { "https://vault.test.com" } -ParameterFilter { $Key -eq "VaultUri" }
        $result = Get-ConfigValue -Key "VaultUri"
        $result | Should -Be "https://vault.test.com"
    }

    It "Substitutes environment variables" {
        Mock Get-ConfigValue { "https://eventstore.test.com" } -ParameterFilter { $Key -eq "EventStoreUri" }
        $result = Get-ConfigValue -Key "EventStoreUri"
        $result | Should -Be "https://eventstore.test.com"
    }

    It "Returns default value if key missing" {
        Mock Get-ConfigValue { "default-value" } -ParameterFilter { $Key -eq "MissingKey" }
        $result = Get-ConfigValue -Key "MissingKey" -DefaultValue "default-value"
        $result | Should -Be "default-value"
    }
}

# Additional tests for all Phase 1 utilities...
```

**Coverage Target**: ≥90% for all Phase 1 utility functions

---

### 2. Test-ControlPlane.Tests.ps1

```powershell
<#
.SYNOPSIS
    Unit tests for control plane components (Phase 2).
.DESCRIPTION
    Tests Policy Engine, Orchestrator, CAB Workflow, etc.
#>

Describe "Invoke-RiskAssessment" {
    BeforeAll {
        $evidencePack = @{
            privilegeElevation = 100  # SYSTEM/root
            blastRadius = 50          # 1000 devices
            internetAccess = 0        # No internet
            kernelMode = 0            # User-mode
            cryptoUsage = 0           # No crypto
            dataAccess = 50           # PII access
            changeFrequency = 25      # Monthly updates
            vendorTrust = 75          # Known vendor
        }
    }

    It "Calculates risk score correctly" {
        $score = Invoke-RiskAssessment -EvidencePack $evidencePack
        # Expected: 0.25*100 + 0.20*50 + 0.15*0 + 0.10*0 + 0.10*0 + 0.08*50 + 0.07*25 + 0.05*75
        # = 25 + 10 + 0 + 0 + 0 + 4 + 1.75 + 3.75 = 44.5
        $score | Should -BeGreaterOrEqual 44
        $score | Should -BeLessOrEqual 45
    }

    It "Returns score ≤100 for maximum risk" {
        $maxRiskPack = @{
            privilegeElevation = 100
            blastRadius = 100
            internetAccess = 100
            kernelMode = 100
            cryptoUsage = 100
            dataAccess = 100
            changeFrequency = 100
            vendorTrust = 100
        }
        $score = Invoke-RiskAssessment -EvidencePack $maxRiskPack
        $score | Should -BeLessOrEqual 100
    }

    It "Throws error if factor missing" {
        $incompletePack = @{ privilegeElevation = 50 }
        { Invoke-RiskAssessment -EvidencePack $incompletePack } | Should -Throw
    }
}

Describe "Invoke-PolicyEvaluation" {
    BeforeAll {
        Mock Test-CABApproval { return $true }
        Mock Test-PromotionGates { return $true }
        Mock Test-ScopeValidity { return $true }
    }

    It "Approves low-risk intent with valid policy" {
        $intent = @{ riskScore = 30; ring = "Canary" }
        $result = Invoke-PolicyEvaluation -DeploymentIntent $intent
        $result.Decision | Should -Be "Approve"
    }

    It "Rejects high-risk intent without CAB approval" {
        Mock Test-CABApproval { return $false }
        $intent = @{ riskScore = 80; ring = "Canary" }
        $result = Invoke-PolicyEvaluation -DeploymentIntent $intent
        $result.Decision | Should -Be "Reject"
    }
}

# Additional tests for all Phase 2 control plane components...
```

---

### 3. Test-Connectors.Tests.ps1

```powershell
<#
.SYNOPSIS
    Unit tests for execution plane connectors (Phase 3).
.DESCRIPTION
    Tests Intune, Jamf, SCCM, Landscape, Ansible connectors with mocked APIs.
#>

Describe "Publish-IntuneApplication" {
    BeforeAll {
        Mock Invoke-MgGraphRequest {
            param($Method, $Uri, $Body)
            if ($Method -eq "POST" -and $Uri -like "*mobileApps*") {
                return @{ id = "app-123"; displayName = "Test App" }
            }
        }
        Mock Get-IntuneAppByCorrelationId { return $null }  # No existing app
        Mock Get-IntuneRingGroup { return @{ id = "group-123" } }
    }

    It "Creates app successfully" {
        $intent = @{
            AppName = "Test App"
            Description = "Test"
            Publisher = "Test Publisher"
            InstallCommand = "install.exe"
            UninstallCommand = "uninstall.exe"
            DetectionPath = "C:\Program Files\TestApp"
            DetectionFile = "app.exe"
            Ring = "Canary"
        }
        $result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId "test-123"
        $result.id | Should -Be "app-123"
    }

    It "Returns existing app on idempotent call" {
        Mock Get-IntuneAppByCorrelationId { return @{ id = "existing-app"; displayName = "Existing" } }
        $intent = @{ AppName = "Test"; Ring = "Canary" }
        $result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId "duplicate"
        $result.id | Should -Be "existing-app"
    }

    It "Retries on transient error (429)" {
        $attempt = 0
        Mock Invoke-MgGraphRequest {
            $script:attempt++
            if ($script:attempt -lt 3) {
                $exception = [Microsoft.Graph.PowerShell.Runtime.RestException]::new("Too Many Requests")
                $exception.StatusCode = 429
                throw $exception
            }
            return @{ id = "app-retry" }
        }
        $intent = @{ AppName = "Retry Test"; Ring = "Canary" }
        $result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId "retry-123"
        $result.id | Should -Be "app-retry"
        $attempt | Should -BeGreaterOrEqual 3
    }
}

# Additional tests for Jamf, SCCM, Landscape, Ansible connectors...
```

---

## Scope: Integration Tests (scripts/testing/integration/)

### 1. Test-EndToEndDeployment.Tests.ps1

```powershell
<#
.SYNOPSIS
    Integration test for end-to-end deployment workflow.
.DESCRIPTION
    Tests: CLI deploy → Control Plane → Connector → Evidence Pack.
#>

Describe "End-to-End Deployment Workflow" -Tag "Integration" {
    BeforeAll {
        # Set up test environment
        $testEnv = Initialize-TestEnvironment
        $testPackage = "$TestDrive/test-app.msi"
        Copy-Item "$PSScriptRoot/../fixtures/sample-app.msi" $testPackage
    }

    AfterAll {
        # Clean up test environment
        Remove-TestEnvironment -Environment $testEnv
    }

    It "Completes full deployment pipeline" {
        # 1. Package application
        $packageResult = Invoke-BuildPipeline -SourcePackagePath $testPackage -Platform "Windows" -CorrelationId "e2e-test"
        $packageResult.Status | Should -Be "Success"

        # 2. Submit deployment intent
        $deployResult = Invoke-Deploy -AppName "Test App" -Version "1.0" -Ring "Lab" -EvidencePackPath $packageResult.EvidencePackPath
        $deployResult.Status | Should -Be "Success"

        # 3. Verify deployment in connector (mocked)
        $status = Get-IntuneDeploymentStatus -CorrelationId "e2e-test"
        $status.TotalDevices | Should -BeGreaterThan 0

        # 4. Verify evidence pack saved
        $evidencePack = Get-EvidencePack -CorrelationId "e2e-test"
        $evidencePack | Should -Not -BeNullOrEmpty
        $evidencePack.sbom | Should -Not -BeNullOrEmpty
    }

    It "Blocks deployment with CRITICAL vulnerabilities" {
        Mock Invoke-VulnerabilityScan {
            return @{ CriticalCount = 1; HighCount = 0; MediumCount = 0; LowCount = 0 }
        }

        { Invoke-BuildPipeline -SourcePackagePath $testPackage -Platform "Windows" -CorrelationId "blocked-test" } | Should -Throw "*CRITICAL vulnerabilities*"
    }

    It "Routes high-risk deployment to CAB" {
        Mock Invoke-RiskAssessment { return 75 }  # High risk
        Mock Invoke-CABSubmission { return @{ id = "cab-123" } }

        $deployResult = Invoke-Deploy -AppName "High Risk App" -Version "1.0" -Ring "Canary" -EvidencePackPath $packageResult.EvidencePackPath
        Assert-MockCalled Invoke-CABSubmission -Times 1
    }
}
```

---

### 2. Test-RollbackWorkflow.Tests.ps1

```powershell
<#
.SYNOPSIS
    Integration test for rollback workflow.
.DESCRIPTION
    Tests: Invoke-RollbackExecution → Connector Remove → Validation.
#>

Describe "Rollback Workflow" -Tag "Integration" {
    It "Rolls back deployment successfully" {
        # 1. Deploy app (setup)
        $deployResult = Invoke-Deploy -AppName "Rollback Test" -Version "1.0" -Ring "Lab" -EvidencePackPath "./test-evidence.json"

        # 2. Execute rollback
        $rollbackResult = Invoke-RollbackExecution -CorrelationId $deployResult.CorrelationId
        $rollbackResult.Status | Should -Be "Success"

        # 3. Verify app removed from connector
        $status = Get-IntuneDeploymentStatus -CorrelationId $deployResult.CorrelationId
        $status.TotalDevices | Should -Be 0
    }

    It "Completes rollback within 4 hours" {
        $startTime = Get-Date
        $rollbackResult = Invoke-RollbackExecution -CorrelationId "perf-test"
        $duration = (Get-Date) - $startTime

        $duration.TotalHours | Should -BeLessOrEqual 4
    }
}
```

---

## Scope: End-to-End Tests (scripts/testing/e2e/)

### 1. Test-CABWorkflow.Tests.ps1

```powershell
<#
.SYNOPSIS
    E2E test for CAB approval workflow.
.DESCRIPTION
    Tests: High-risk intent → CAB submission → Approval → Deployment proceeds.
#>

Describe "CAB Approval Workflow" -Tag "E2E" {
    It "Requires CAB approval for high-risk deployment" {
        # 1. Submit high-risk deployment
        $intent = @{ AppName = "Critical App"; riskScore = 85; ring = "Pilot" }
        $result = Invoke-Deploy -DeploymentIntent $intent

        # 2. Verify CAB submission created
        $cabSubmission = Get-CABSubmission -IntentId $result.IntentId
        $cabSubmission.Status | Should -Be "Pending"

        # 3. Approve via CAB
        Invoke-Approve -IntentId $result.IntentId -Decision "Approve" -Comments "Evidence complete"

        # 4. Verify deployment proceeds
        $deploymentStatus = Get-DeploymentStatus -CorrelationId $result.CorrelationId
        $deploymentStatus.Status | Should -Be "InProgress"
    }

    It "Blocks deployment if CAB rejects" {
        $intent = @{ AppName = "Rejected App"; riskScore = 90; ring = "Global" }
        $result = Invoke-Deploy -DeploymentIntent $intent

        # Reject via CAB
        Invoke-Approve -IntentId $result.IntentId -Decision "Reject" -Comments "Insufficient testing"

        # Verify deployment blocked
        $deploymentStatus = Get-DeploymentStatus -CorrelationId $result.CorrelationId
        $deploymentStatus.Status | Should -Be "Rejected"
    }
}
```

---

## Scope: Pre-Commit Hooks (scripts/testing/hooks/)

### 1. pre-commit.ps1

```powershell
<#
.SYNOPSIS
    Pre-commit hook to enforce quality standards.
.DESCRIPTION
    Runs PSScriptAnalyzer and Pester tests before allowing commit.
#>

# Get staged PowerShell files
$stagedFiles = git diff --cached --name-only --diff-filter=ACM | Where-Object { $_ -like "*.ps1" }

if ($stagedFiles.Count -eq 0) {
    Write-Host "No PowerShell files staged for commit."
    exit 0
}

Write-Host "Running pre-commit quality checks..."

# 1. PSScriptAnalyzer
Write-Host "Running PSScriptAnalyzer..."
$analysisResults = @()
foreach ($file in $stagedFiles) {
    $results = Invoke-ScriptAnalyzer -Path $file -Severity Error, Warning
    $analysisResults += $results
}

if ($analysisResults.Count -gt 0) {
    Write-Host "PSScriptAnalyzer found $($analysisResults.Count) issues:" -ForegroundColor Red
    $analysisResults | Format-Table -AutoSize
    Write-Host "Commit blocked. Fix issues and try again." -ForegroundColor Red
    exit 1
}

# 2. Pester tests for changed files
Write-Host "Running Pester tests..."
$testResults = Invoke-Pester -Path "scripts/testing/" -PassThru -Show None

if ($testResults.FailedCount -gt 0) {
    Write-Host "Pester found $($testResults.FailedCount) failing tests:" -ForegroundColor Red
    $testResults.Failed | Format-Table -AutoSize
    Write-Host "Commit blocked. Fix failing tests and try again." -ForegroundColor Red
    exit 1
}

# 3. Code coverage check
$coveragePercent = ($testResults.CodeCoverage.NumberOfCommandsExecuted / $testResults.CodeCoverage.NumberOfCommandsAnalyzed) * 100
if ($coveragePercent -lt 90) {
    Write-Host "Code coverage is $([math]::Round($coveragePercent, 2))% (minimum: 90%)" -ForegroundColor Red
    Write-Host "Commit blocked. Increase test coverage." -ForegroundColor Red
    exit 1
}

Write-Host "All quality checks passed!" -ForegroundColor Green
exit 0
```

**Installation**:
```bash
# Copy to .git/hooks/pre-commit
cp scripts/testing/hooks/pre-commit.ps1 .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## Scope: CI/CD Pipeline (.github/workflows/ or Azure Pipelines)

### 1. ci-pipeline.yml (GitHub Actions)

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  quality-gate:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install PSScriptAnalyzer
        shell: pwsh
        run: Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser

      - name: Install Pester
        shell: pwsh
        run: Install-Module -Name Pester -Force -Scope CurrentUser -MinimumVersion 5.0

      - name: Run PSScriptAnalyzer
        shell: pwsh
        run: |
          $results = Invoke-ScriptAnalyzer -Path ./scripts -Recurse -Severity Error,Warning
          if ($results.Count -gt 0) {
            $results | Format-Table -AutoSize
            exit 1
          }

      - name: Run Pester Tests
        shell: pwsh
        run: |
          $config = New-PesterConfiguration
          $config.Run.Path = './scripts/testing'
          $config.CodeCoverage.Enabled = $true
          $config.CodeCoverage.Path = './scripts'
          $config.CodeCoverage.OutputFormat = 'JaCoCo'
          $config.CodeCoverage.OutputPath = './coverage.xml'
          $config.TestResult.Enabled = $true
          $config.TestResult.OutputFormat = 'NUnitXml'
          $config.TestResult.OutputPath = './test-results.xml'

          $results = Invoke-Pester -Configuration $config
          if ($results.FailedCount -gt 0) {
            exit 1
          }

      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action/composite@v2
        if: always()
        with:
          files: ./test-results.xml

      - name: Publish Code Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
```

---

## Quality Checklist

### Per Test Suite
- [ ] ≥90% code coverage
- [ ] All tests pass
- [ ] Tests isolated (no shared state)
- [ ] Fast execution (<5s unit, <30s integration)
- [ ] Mocked external dependencies

### Pre-Commit Hooks
- [ ] PSScriptAnalyzer enforced
- [ ] Pester tests enforced
- [ ] Code coverage enforced (≥90%)

### CI/CD Pipeline
- [ ] Quality gates on all branches
- [ ] Test results published
- [ ] Code coverage tracked
- [ ] Failing tests block merge

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. Code coverage drops below 90%
2. PSScriptAnalyzer errors/warnings introduced
3. Flaky tests (tests fail non-deterministically)
4. Tests use real credentials or production APIs
5. Pre-commit hooks bypassed

**Escalate to human if**:
- Test suite execution time exceeds 10 minutes
- Integration tests failing in CI but passing locally

---

## Delivery Checklist

- [ ] All unit tests implemented (≥90% coverage)
- [ ] Integration tests cover critical workflows
- [ ] E2E tests validate user scenarios
- [ ] Pre-commit hooks installed and enforced
- [ ] CI/CD pipeline configured with quality gates
- [ ] Test reports generated for CAB submission
- [ ] README with testing instructions

---

## Related Documentation

- [.agents/rules/11-testing-quality-rules.md](../../.agents/rules/11-testing-quality-rules.md)
- [docs/runbooks/cab-submission.md](../../runbooks/cab-submission.md)

---

**End of Phase 6 Prompt**
