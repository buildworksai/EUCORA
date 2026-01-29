# Phase 4: Packaging Factory - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 3 weeks
**Dependencies**: Phase 1 (Foundation)

---

## Task Overview

Implement the packaging pipeline that transforms source packages into signed, scanned, SBOM-enriched artifacts ready for deployment. The Packaging Factory enforces supply chain security controls: SBOM generation, vulnerability scanning, code signing, and provenance tracking.

**Success Criteria**:
- All 6 packaging factory components implemented (Build, Signing, SBOM, Scanning, Testing, Provenance)
- SBOM mandatory for all packages (SPDX or CycloneDX format)
- Vulnerability scanning with configurable severity thresholds
- Code signing with HSM-backed certificates
- Provenance attestations (SLSA framework alignment)
- ≥90% test coverage across all components

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **Supply Chain Security**: SBOM + Scan + Sign mandatory for ALL packages
- ✅ **Separation of Duties**: Packaging ≠ Publishing ≠ Signing
- ✅ **Deterministic Builds**: Reproducible builds where possible
- ✅ **Evidence-First**: All pipeline outputs recorded in Evidence Pack
- ✅ **No Publishing**: Packaging Factory creates artifacts, NEVER publishes to execution planes

### Quality Standards
- ✅ **PSScriptAnalyzer**: ZERO errors, ZERO warnings
- ✅ **Pester Tests**: ≥90% coverage per component
- ✅ **SBOM Required**: Pipeline fails if SBOM generation fails
- ✅ **Scan Gates**: CRITICAL/HIGH vulnerabilities block pipeline (configurable threshold)
- ✅ **Signature Validation**: All artifacts signed, signature verified post-signing

### Security Requirements
- ✅ **HSM Signing**: Code signing keys stored in Azure Key Vault with HSM backing (FIPS 140-2 Level 2)
- ✅ **Least Privilege**: Packaging service principal scoped to Key Vault signing operations only
- ✅ **Immutable Artifacts**: Signed packages stored in immutable blob storage (WORM policy)
- ✅ **Audit Trail**: Every pipeline step logged with correlation ID

---

## Pipeline Architecture

```
Source Package → Build → SBOM Generation → Vulnerability Scanning → Code Signing → Testing → Provenance → Evidence Pack
```

Each stage MUST:
1. Validate inputs (check previous stage success)
2. Execute stage logic
3. Generate stage artifacts
4. Log stage result to Event Store
5. Append stage data to Evidence Pack
6. Return success/failure exit code

---

## Scope: Build Pipeline (scripts/packaging-factory/build/)

### 1. Invoke-BuildPipeline.ps1

```powershell
<#
.SYNOPSIS
    Execute packaging pipeline for application.
.DESCRIPTION
    Orchestrates all packaging stages: build → SBOM → scan → sign → test → provenance.
.PARAMETER SourcePackagePath
    Path to source package (MSI, PKG, DEB, RPM, APK).
.PARAMETER Platform
    Target platform (Windows, macOS, Linux, Mobile).
.PARAMETER CorrelationId
    Correlation ID for pipeline run.
.EXAMPLE
    Invoke-BuildPipeline -SourcePackagePath "./notepadpp.msi" -Platform "Windows" -CorrelationId "build-123"
#>
function Invoke-BuildPipeline {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$SourcePackagePath,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Windows", "macOS", "Linux", "Mobile")]
        [string]$Platform,

        [Parameter(Mandatory = $false)]
        [string]$CorrelationId = (Get-CorrelationId -Prefix "build")
    )

    Write-StructuredLog -Level "Info" -Message "Starting packaging pipeline" -CorrelationId $CorrelationId

    # Initialize evidence pack
    $evidencePack = @{
        correlationId = $CorrelationId
        sourcePackage = (Get-Item $SourcePackagePath).Name
        platform = $Platform
        pipelineStages = @()
        timestamp = (Get-Date -Format "o")
    }

    try {
        # Stage 1: Repackage (if needed)
        $repackagedPath = Invoke-Repackaging -SourcePath $SourcePackagePath -Platform $Platform -CorrelationId $CorrelationId
        $evidencePack.pipelineStages += @{ Stage = "Repackage"; Status = "Success"; Output = $repackagedPath }

        # Stage 2: SBOM Generation
        $sbomPath = New-SBOM -PackagePath $repackagedPath -Format "SPDX" -CorrelationId $CorrelationId
        $evidencePack.sbom = (Get-Content $sbomPath | ConvertFrom-Json)
        $evidencePack.pipelineStages += @{ Stage = "SBOM"; Status = "Success"; Output = $sbomPath }

        # Stage 3: Vulnerability Scanning
        $scanResult = Invoke-VulnerabilityScan -PackagePath $repackagedPath -SBOMPath $sbomPath -CorrelationId $CorrelationId
        $evidencePack.scanResults = $scanResult
        $evidencePack.pipelineStages += @{ Stage = "Scan"; Status = "Success"; CriticalCount = $scanResult.CriticalCount }

        # Gate: Block if CRITICAL vulnerabilities found
        if ($scanResult.CriticalCount -gt 0) {
            throw "Pipeline blocked: $($scanResult.CriticalCount) CRITICAL vulnerabilities found"
        }

        # Stage 4: Code Signing
        $signedPath = Invoke-CodeSigning -PackagePath $repackagedPath -Platform $Platform -CorrelationId $CorrelationId
        $evidencePack.signedPackage = (Get-Item $signedPath).Name
        $evidencePack.pipelineStages += @{ Stage = "Signing"; Status = "Success"; Output = $signedPath }

        # Stage 5: Post-Build Testing
        $testResult = Invoke-PackageTesting -PackagePath $signedPath -Platform $Platform -CorrelationId $CorrelationId
        $evidencePack.testResults = $testResult
        $evidencePack.pipelineStages += @{ Stage = "Testing"; Status = "Success"; TestsPassed = $testResult.PassedCount }

        # Gate: Block if any tests failed
        if ($testResult.FailedCount -gt 0) {
            throw "Pipeline blocked: $($testResult.FailedCount) tests failed"
        }

        # Stage 6: Provenance Attestation
        $provenancePath = New-ProvenanceAttestation -PackagePath $signedPath -EvidencePack $evidencePack -CorrelationId $CorrelationId
        $evidencePack.provenance = (Get-Content $provenancePath | ConvertFrom-Json)
        $evidencePack.pipelineStages += @{ Stage = "Provenance"; Status = "Success"; Output = $provenancePath }

        # Save evidence pack
        $evidencePackPath = "$($env:TEMP)/evidence-pack-$CorrelationId.json"
        $evidencePack | ConvertTo-Json -Depth 10 | Out-File $evidencePackPath
        Save-EvidencePack -EvidencePack $evidencePack -CorrelationId $CorrelationId

        Write-StructuredLog -Level "Info" -Message "Packaging pipeline completed successfully" -CorrelationId $CorrelationId
        return @{
            Status = "Success"
            SignedPackagePath = $signedPath
            EvidencePackPath = $evidencePackPath
            CorrelationId = $CorrelationId
        }
    } catch {
        Write-StructuredLog -Level "Error" -Message "Packaging pipeline failed: $($_.Exception.Message)" -CorrelationId $CorrelationId
        $evidencePack.pipelineStages += @{ Stage = "Pipeline"; Status = "Failed"; Error = $_.Exception.Message }
        throw
    }
}
```

**Pester Tests Required**:
- Valid package completes all stages
- CRITICAL vulnerability blocks pipeline
- Test failure blocks pipeline
- Evidence pack saved correctly

---

### 2. Invoke-Repackaging.ps1

```powershell
<#
.SYNOPSIS
    Repackage application to platform-specific format.
.DESCRIPTION
    Converts source packages to MSIX (Windows), PKG (macOS), DEB (Linux), etc.
.PARAMETER SourcePath
    Source package path.
.PARAMETER Platform
    Target platform.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Invoke-Repackaging -SourcePath "./setup.exe" -Platform "Windows" -CorrelationId "build-123"
#>
function Invoke-Repackaging {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourcePath,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Windows", "macOS", "Linux", "Mobile")]
        [string]$Platform,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $outputDir = "$($env:TEMP)/repackaged-$CorrelationId"
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

    switch ($Platform) {
        "Windows" {
            # Convert to MSIX or .intunewin
            $outputPath = "$outputDir/app.intunewin"
            # Use IntuneWinAppUtil.exe to create .intunewin package
            & "$PSScriptRoot/../tools/IntuneWinAppUtil.exe" -c (Split-Path $SourcePath) `
                -s (Get-Item $SourcePath).Name -o $outputDir -q
        }
        "macOS" {
            # Convert to signed PKG
            $outputPath = "$outputDir/app.pkg"
            # Use pkgbuild or existing PKG
            Copy-Item $SourcePath $outputPath
        }
        "Linux" {
            # Convert to DEB or RPM
            $outputPath = "$outputDir/app.deb"
            Copy-Item $SourcePath $outputPath
        }
        "Mobile" {
            # iOS IPA or Android APK
            $outputPath = "$outputDir/app.apk"
            Copy-Item $SourcePath $outputPath
        }
    }

    Write-StructuredLog -Level "Info" -Message "Repackaging completed" -CorrelationId $CorrelationId -Metadata @{OutputPath = $outputPath}
    return $outputPath
}
```

**Pester Tests Required**:
- Windows source creates .intunewin
- macOS source creates .pkg
- Linux source creates .deb
- Mobile source creates .apk/.ipa

---

## Scope: SBOM Generation (scripts/packaging-factory/sbom/)

### 1. New-SBOM.ps1

```powershell
<#
.SYNOPSIS
    Generate Software Bill of Materials (SBOM).
.DESCRIPTION
    Uses Syft to generate SBOM in SPDX or CycloneDX format.
.PARAMETER PackagePath
    Package to analyze.
.PARAMETER Format
    SBOM format (SPDX or CycloneDX).
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    New-SBOM -PackagePath "./app.intunewin" -Format "SPDX" -CorrelationId "build-123"
#>
function New-SBOM {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$PackagePath,

        [Parameter(Mandatory = $false)]
        [ValidateSet("SPDX", "CycloneDX")]
        [string]$Format = "SPDX",

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $sbomPath = "$($env:TEMP)/sbom-$CorrelationId.json"

    # Use Syft (https://github.com/anchore/syft)
    $syftFormat = if ($Format -eq "SPDX") { "spdx-json" } else { "cyclonedx-json" }
    & syft packages $PackagePath -o $syftFormat --file $sbomPath

    if (-not (Test-Path $sbomPath)) {
        throw "SBOM generation failed for $PackagePath"
    }

    Write-StructuredLog -Level "Info" -Message "SBOM generated" -CorrelationId $CorrelationId -Metadata @{Format = $Format; Path = $sbomPath}
    return $sbomPath
}
```

**Pester Tests Required**:
- SPDX format generates valid JSON
- CycloneDX format generates valid JSON
- Invalid package throws error
- SBOM contains expected components

---

## Scope: Vulnerability Scanning (scripts/packaging-factory/scanning/)

### 1. Invoke-VulnerabilityScan.ps1

```powershell
<#
.SYNOPSIS
    Scan package for vulnerabilities.
.DESCRIPTION
    Uses Grype to scan SBOM for known CVEs.
.PARAMETER PackagePath
    Package to scan.
.PARAMETER SBOMPath
    SBOM file path.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Invoke-VulnerabilityScan -PackagePath "./app.intunewin" -SBOMPath "./sbom.json" -CorrelationId "build-123"
#>
function Invoke-VulnerabilityScan {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackagePath,

        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$SBOMPath,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $scanOutputPath = "$($env:TEMP)/scan-$CorrelationId.json"

    # Use Grype (https://github.com/anchore/grype)
    & grype sbom:$SBOMPath -o json --file $scanOutputPath

    if (-not (Test-Path $scanOutputPath)) {
        throw "Vulnerability scan failed for $SBOMPath"
    }

    # Parse results
    $scanResults = Get-Content $scanOutputPath | ConvertFrom-Json
    $vulnerabilities = $scanResults.matches

    $summary = @{
        TotalVulnerabilities = $vulnerabilities.Count
        CriticalCount = ($vulnerabilities | Where-Object { $_.vulnerability.severity -eq "Critical" }).Count
        HighCount = ($vulnerabilities | Where-Object { $_.vulnerability.severity -eq "High" }).Count
        MediumCount = ($vulnerabilities | Where-Object { $_.vulnerability.severity -eq "Medium" }).Count
        LowCount = ($vulnerabilities | Where-Object { $_.vulnerability.severity -eq "Low" }).Count
        Vulnerabilities = $vulnerabilities | Select-Object -First 10  # Include top 10 for evidence pack
    }

    Write-StructuredLog -Level "Info" -Message "Vulnerability scan completed" -CorrelationId $CorrelationId -Metadata $summary
    return $summary
}
```

**Pester Tests Required**:
- Package with vulnerabilities returns correct counts
- Clean package returns zero vulnerabilities
- CRITICAL vulnerability detected correctly
- Scan output JSON valid

---

## Scope: Code Signing (scripts/packaging-factory/signing/)

### 1. Invoke-CodeSigning.ps1

```powershell
<#
.SYNOPSIS
    Sign package with platform-specific code signing certificate.
.DESCRIPTION
    Signs packages using Azure Key Vault HSM-backed certificates.
.PARAMETER PackagePath
    Package to sign.
.PARAMETER Platform
    Platform (Windows, macOS, Linux, Mobile).
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Invoke-CodeSigning -PackagePath "./app.intunewin" -Platform "Windows" -CorrelationId "build-123"
#>
function Invoke-CodeSigning {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateScript({ Test-Path $_ })]
        [string]$PackagePath,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Windows", "macOS", "Linux", "Mobile")]
        [string]$Platform,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $signedPath = $PackagePath.Replace((Get-Item $PackagePath).Extension, ".signed$((Get-Item $PackagePath).Extension)")

    switch ($Platform) {
        "Windows" {
            # Use AzureSignTool (https://github.com/vcsjones/AzureSignTool)
            $vaultUri = Get-ConfigValue -Key "VaultUri"
            $certName = Get-ConfigValue -Key "WindowsSigningCertName"

            & AzureSignTool sign -kvu $vaultUri -kvc $certName -kvt $azureToken `
                -tr "http://timestamp.digicert.com" -td sha256 -fd sha256 $PackagePath

            # Verify signature
            & signtool verify /pa /v $PackagePath
            if ($LASTEXITCODE -ne 0) {
                throw "Signature verification failed for $PackagePath"
            }

            $signedPath = $PackagePath  # Signed in-place
        }
        "macOS" {
            # Use productsign with certificate from Key Vault
            $certPath = Get-KeyVaultCertificate -CertName "macOS-Developer-ID"
            & productsign --sign "Developer ID Installer" --timestamp $PackagePath $signedPath

            # Verify signature
            & pkgutil --check-signature $signedPath
            if ($LASTEXITCODE -ne 0) {
                throw "Signature verification failed for $signedPath"
            }
        }
        "Linux" {
            # Use dpkg-sig for DEB or rpm --addsign for RPM
            if ($PackagePath -like "*.deb") {
                $gpgKey = Get-KeyVaultSecret -SecretName "Linux-GPG-Key"
                & dpkg-sig --sign builder -k $gpgKey $PackagePath
                $signedPath = $PackagePath
            } elseif ($PackagePath -like "*.rpm") {
                & rpm --addsign $PackagePath
                $signedPath = $PackagePath
            }
        }
        "Mobile" {
            # iOS: Use codesign with provisioning profile
            # Android: Use jarsigner with keystore from Key Vault
            if ($PackagePath -like "*.apk") {
                $keystorePath = Get-KeyVaultCertificate -CertName "Android-Keystore"
                & jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 `
                    -keystore $keystorePath -storepass $keystorePassword $PackagePath "key-alias"
                $signedPath = $PackagePath
            }
        }
    }

    Write-StructuredLog -Level "Info" -Message "Package signed successfully" -CorrelationId $CorrelationId -Metadata @{SignedPath = $signedPath}
    return $signedPath
}
```

**Helper Functions**:
- `Get-KeyVaultCertificate`: Download certificate from Azure Key Vault
- `Get-KeyVaultSecret`: Download secret from Azure Key Vault

**Pester Tests Required**:
- Windows package signed and verified
- macOS package signed and verified
- Linux DEB signed and verified
- Android APK signed and verified
- Signing failure throws error

---

## Scope: Package Testing (scripts/packaging-factory/testing/)

### 1. Invoke-PackageTesting.ps1

```powershell
<#
.SYNOPSIS
    Execute post-build package tests.
.DESCRIPTION
    Validates package structure, installation, uninstallation in sandbox.
.PARAMETER PackagePath
    Signed package path.
.PARAMETER Platform
    Platform.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    Invoke-PackageTesting -PackagePath "./app.signed.intunewin" -Platform "Windows" -CorrelationId "build-123"
#>
function Invoke-PackageTesting {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackagePath,

        [Parameter(Mandatory = $true)]
        [ValidateSet("Windows", "macOS", "Linux", "Mobile")]
        [string]$Platform,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    $testResults = @{
        PassedCount = 0
        FailedCount = 0
        Tests = @()
    }

    # Test 1: Package signature valid
    $signatureTest = Test-PackageSignature -PackagePath $PackagePath -Platform $Platform
    $testResults.Tests += $signatureTest
    if ($signatureTest.Result -eq "Pass") { $testResults.PassedCount++ } else { $testResults.FailedCount++ }

    # Test 2: Package metadata valid
    $metadataTest = Test-PackageMetadata -PackagePath $PackagePath -Platform $Platform
    $testResults.Tests += $metadataTest
    if ($metadataTest.Result -eq "Pass") { $testResults.PassedCount++ } else { $testResults.FailedCount++ }

    # Test 3: Install/Uninstall in sandbox (Windows Sandbox, macOS VM, Docker for Linux)
    $installTest = Test-PackageInstallation -PackagePath $PackagePath -Platform $Platform
    $testResults.Tests += $installTest
    if ($installTest.Result -eq "Pass") { $testResults.PassedCount++ } else { $testResults.FailedCount++ }

    Write-StructuredLog -Level "Info" -Message "Package testing completed" -CorrelationId $CorrelationId -Metadata $testResults
    return $testResults
}
```

**Helper Functions**:
- `Test-PackageSignature`: Verify signature valid
- `Test-PackageMetadata`: Validate package structure (manifest, files, etc.)
- `Test-PackageInstallation`: Install in sandbox, verify detection, uninstall

**Pester Tests Required**:
- Valid package passes all tests
- Invalid signature fails test
- Installation failure detected

---

## Scope: Provenance Attestation (scripts/packaging-factory/provenance/)

### 1. New-ProvenanceAttestation.ps1

```powershell
<#
.SYNOPSIS
    Generate provenance attestation for package.
.DESCRIPTION
    Creates SLSA-aligned provenance document with build metadata.
.PARAMETER PackagePath
    Signed package path.
.PARAMETER EvidencePack
    Evidence pack with pipeline stages.
.PARAMETER CorrelationId
    Correlation ID.
.EXAMPLE
    New-ProvenanceAttestation -PackagePath "./app.signed.intunewin" -EvidencePack $evidence -CorrelationId "build-123"
#>
function New-ProvenanceAttestation {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$PackagePath,

        [Parameter(Mandatory = $true)]
        [hashtable]$EvidencePack,

        [Parameter(Mandatory = $true)]
        [string]$CorrelationId
    )

    # Calculate package hash
    $packageHash = (Get-FileHash $PackagePath -Algorithm SHA256).Hash

    # Create provenance document (SLSA v0.2 format)
    $provenance = @{
        _type = "https://in-toto.io/Statement/v0.1"
        subject = @(
            @{
                name = (Get-Item $PackagePath).Name
                digest = @{
                    sha256 = $packageHash
                }
            }
        )
        predicateType = "https://slsa.dev/provenance/v0.2"
        predicate = @{
            builder = @{
                id = "https://packaging-factory.example.com/builder/v1"
            }
            buildType = "https://packaging-factory.example.com/buildType/v1"
            invocation = @{
                configSource = @{
                    uri = "https://github.com/org/repo"
                    digest = @{ sha256 = "source-commit-hash" }
                }
                parameters = @{
                    correlationId = $CorrelationId
                    platform = $EvidencePack.platform
                }
            }
            metadata = @{
                buildStartedOn = $EvidencePack.timestamp
                buildFinishedOn = (Get-Date -Format "o")
                completeness = @{
                    parameters = $true
                    environment = $true
                    materials = $true
                }
                reproducible = $false
            }
            materials = @(
                @{
                    uri = $EvidencePack.sourcePackage
                    digest = @{ sha256 = (Get-FileHash $EvidencePack.sourcePackage -Algorithm SHA256).Hash }
                }
            )
        }
    }

    $provenancePath = "$($env:TEMP)/provenance-$CorrelationId.json"
    $provenance | ConvertTo-Json -Depth 10 | Out-File $provenancePath

    Write-StructuredLog -Level "Info" -Message "Provenance attestation generated" -CorrelationId $CorrelationId -Metadata @{Path = $provenancePath}
    return $provenancePath
}
```

**Pester Tests Required**:
- Provenance JSON valid
- Package hash matches
- SLSA format compliant

---

## Quality Checklist

### Per Component
- [ ] PSScriptAnalyzer ZERO errors/warnings
- [ ] Pester tests ≥90% coverage
- [ ] All stages logged to Event Store
- [ ] Evidence pack includes all stage outputs
- [ ] SBOM mandatory (pipeline fails without it)
- [ ] Scan gates enforced (CRITICAL blocks by default)
- [ ] Signatures verified post-signing

### Integration Tests
- [ ] End-to-end: Source package → Signed package with evidence pack
- [ ] SBOM generation for all platforms (Windows, macOS, Linux, Mobile)
- [ ] Vulnerability scan detects known CVEs
- [ ] Code signing with HSM certificates
- [ ] Package testing in sandbox environments

---

## Emergency Stop Conditions

**STOP IMMEDIATELY if**:
1. Any package proceeds without SBOM
2. Any package proceeds without vulnerability scan
3. CRITICAL vulnerabilities not blocking pipeline
4. Code signing using non-HSM keys
5. Unsigned packages published to execution planes

**Escalate to human if**:
- Azure Key Vault signing failing (certificate expired?)
- Syft/Grype tools unavailable (network/repository issue?)
- Sandbox environments unreachable (VM/Docker infrastructure down?)

---

## Delivery Checklist

- [ ] All 6 packaging factory components implemented
- [ ] SBOM generation with Syft (SPDX/CycloneDX)
- [ ] Vulnerability scanning with Grype
- [ ] Code signing with Azure Key Vault HSM
- [ ] Package testing in sandboxes
- [ ] Provenance attestation (SLSA-aligned)
- [ ] PSScriptAnalyzer: 0 errors, 0 warnings
- [ ] Pester tests: ≥90% coverage
- [ ] README with tool prerequisites (Syft, Grype, AzureSignTool, etc.)

---

## Related Documentation

- [.agents/rules/03-packaging-factory-rules.md](../../.agents/rules/03-packaging-factory-rules.md)
- [docs/modules/windows/packaging-standards.md](../../modules/windows/packaging-standards.md)
- [docs/modules/macos/packaging-standards.md](../../modules/macos/packaging-standards.md)
- [docs/modules/linux/packaging-standards.md](../../modules/linux/packaging-standards.md)
- [docs/modules/mobile/packaging-standards.md](../../modules/mobile/packaging-standards.md)
- [docs/infrastructure/key-management.md](../../infrastructure/key-management.md)
- [docs/infrastructure/secrets-management.md](../../infrastructure/secrets-management.md)

---

**End of Phase 4 Prompt**
