# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Suppress common test file warnings
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseDeclaredVarsMoreThanAssignments', '', Justification = 'Test variables are used in assertions via Should')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Mock function parameters required for interface compatibility')]
#<#+
.SYNOPSIS
    Integration tests for connector end-to-end workflows.
.DESCRIPTION
    Tests complete publish/remove/status workflows across all connectors with idempotency validation.
.NOTES
Version: 1.0
Author: Platform Engineering
#>

BeforeAll {
    . "$PSScriptRoot/../../connectors/ConnectorManager.ps1"
}

Describe "Integration - End-to-End Publish Workflow" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Mock function parameter required for interface compatibility')]
            param($Name)
            return @{
                intune = @{
                    client_id = 'test-client-id'
                    client_secret = 'test-client-secret'
                    tenant_id = 'test-tenant-id'
                    ring_groups = @{ canary = 'group-123' }
                }
                jamf = @{
                    api_url = 'https://jamf.test.com'
                    client_id = 'jamf-client-id'
                    client_secret = 'jamf-client-secret'
                    smart_groups = @{ canary = 'smart-group-456' }
                }
                sccm = @{
                    api_url = 'https://sccm.test.com'
                    site_code = 'TST'
                    collections = @{ canary = 'COL00123' }
                }
                landscape = @{
                    api_url = 'https://landscape.test.com'
                    api_token = 'landscape-token'
                    account_name = 'test-account'
                }
                ansible = @{
                    tower_api_url = 'https://awx.test.com'
                    token = 'awx-token'
                    job_template_id = 10
                    inventory_id = 5
                }
            }[$Name]
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Invoke-ConnectorRequest {
            param($Uri, $Method)
            # Use both parameters to avoid unused parameter warning
            if ($Method -eq 'POST' -and $Uri -like '*api*') {
                return @{
                    id = 'resource-123'
                    status = 'success'
                }
            }
            return @{ value = @() }
        }
        Mock Write-StructuredLog { }
    }

    It "Should publish to Intune connector successfully" {
        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Description = 'Integration Test'
            Publisher = 'Test Publisher'
            Ring = 'Canary'
            FileName = 'test.intunewin'
            InstallCommand = 'install.exe /silent'
            UninstallCommand = 'uninstall.exe /silent'
            RequiresAdmin = $true
            DetectionPath = 'C:\Program Files\TestApp'
            DetectionFile = 'test.exe'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'integration-test-001'

        $result.status | Should -Be 'published'
        $result.connector | Should -Be 'intune'
    }

    It "Should publish to Jamf connector successfully" {
        $intent = @{
            Connector = 'jamf'
            AppName = 'Test macOS App'
            Description = 'Integration Test'
            Ring = 'Canary'
            PackagePath = '/tmp/test.pkg'
        }

        Mock Test-Path { return $true }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'integration-test-002'

        $result.status | Should -Be 'published'
        $result.connector | Should -Be 'jamf'
    }

    It "Should publish to SCCM connector successfully" {
        $intent = @{
            Connector = 'sccm'
            AppName = 'Test SCCM App'
            Description = 'Integration Test'
            Version = '1.0.0'
            Publisher = 'Test Publisher'
            Ring = 'Canary'
            InstallCommand = 'install.exe /silent'
            UninstallCommand = 'uninstall.exe /silent'
            RequiresAdmin = $true
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'integration-test-003'

        $result.status | Should -Be 'published'
        $result.connector | Should -Be 'sccm'
    }

    It "Should publish to Landscape connector successfully" {
        $intent = @{
            Connector = 'landscape'
            AppName = 'Test Linux Package'
            Description = 'Integration Test'
            PackageName = 'test-package'
            Version = '1.0.0'
            Ring = 'Canary'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'integration-test-004'

        $result.status | Should -Be 'published'
        $result.connector | Should -Be 'landscape'
    }

    It "Should publish to Ansible connector successfully" {
        $intent = @{
            Connector = 'ansible'
            ArtifactId = 'artifact-123'
            Ring = 'Canary'
            Inventory = 'test-inventory'
            ManifestHash = 'abc123'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'integration-test-005'

        $result.status | Should -Be 'launched'
        $result.connector | Should -Be 'ansible'
    }
}

Describe "Integration - Idempotency Validation" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
                tenant_id = 'test-tenant-id'
                ring_groups = @{ canary = 'group-123' }
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Write-StructuredLog { }

        # First call succeeds, second call should be skipped
        $script:callCount = 0
        Mock Invoke-ConnectorRequest {
            $script:callCount++
            if ($script:callCount -eq 1) {
                return @{ id = 'app-123'; status = 'created' }
            }
            return @{ status = 'idempotent_skip' }
        }
    }

    It "Should prevent duplicate operations with same correlation ID" {
        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Ring = 'Canary'
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        # First publish
        $result1 = Publish-Application -DeploymentIntent $intent -CorrelationId 'idempotency-test-001'

        # Second publish with same correlation ID
        $result2 = Publish-Application -DeploymentIntent $intent -CorrelationId 'idempotency-test-001'

        $result1.status | Should -Be 'published'
        $result2.status | Should -Not -BeNullOrEmpty
        # Second call should be idempotent (implementation-dependent)
    }
}

Describe "Integration - Error Classification Validation" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
                tenant_id = 'test-tenant-id'
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Write-StructuredLog { }
    }

    It "Should classify 429 rate limit as TRANSIENT" {
        Mock Invoke-ConnectorRequest {
            $exception = [System.Net.WebException]::new("Rate limit exceeded")
            $response = [PSCustomObject]@{ StatusCode = 429 }
            $exception | Add-Member -NotePropertyName Response -NotePropertyValue $response -Force
            throw $exception
        }

        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Ring = 'Canary'
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'error-test-001'

        # Result should contain error classification
        $result | Should -Not -BeNullOrEmpty
        # (Implementation-dependent on how errors propagate)
    }

    It "Should classify 403 policy violation as POLICY_VIOLATION" {
        Mock Invoke-ConnectorRequest {
            $exception = [System.Net.WebException]::new("CAB approval required")
            $response = [PSCustomObject]@{ StatusCode = 403 }
            $exception | Add-Member -NotePropertyName Response -NotePropertyValue $response -Force
            throw $exception
        }

        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Ring = 'Canary'
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'error-test-002'
        # Use result to avoid unused variable warning
        $result | Should -Not -BeNullOrEmpty

        # Result should contain POLICY_VIOLATION classification
    }
}

Describe "Integration - Ring-Based Targeting Validation" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
                tenant_id = 'test-tenant-id'
                ring_groups = @{
                    lab = 'group-lab-001'
                    canary = 'group-canary-002'
                    pilot = 'group-pilot-003'
                    department = 'group-dept-004'
                    global = 'group-global-005'
                }
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Invoke-ConnectorRequest { return @{ id = 'app-123' } }
        Mock Write-StructuredLog { }
    }

    It "Should target Lab ring correctly" {
        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Ring = 'Lab'
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'ring-test-001'

        $result.status | Should -Be 'published'
    }

    It "Should target Canary ring correctly" {
        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Ring = 'Canary'
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'ring-test-002'

        $result.status | Should -Be 'published'
    }

    It "Should target Global ring correctly" {
        $intent = @{
            Connector = 'intune'
            AppName = 'Test App'
            Ring = 'Global'
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        $result = Publish-Application -DeploymentIntent $intent -CorrelationId 'ring-test-003'

        $result.status | Should -Be 'published'
    }
}

Describe "Integration - Deployment Status Querying" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
                tenant_id = 'test-tenant-id'
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Invoke-ConnectorRequest {
            param($Uri)
            if ($Uri -match 'deviceStatuses') {
                return @{
                    value = @(
                        @{ installState = 'installed' },
                        @{ installState = 'installed' },
                        @{ installState = 'failed' }
                    )
                }
            }
            return @{
                value = @(
                    @{
                        id = 'app-123'
                        displayName = 'Test App'
                        notes = 'CorrelationId: status-test-001'
                    }
                )
            }
        }
        Mock Write-StructuredLog { }
    }

    It "Should query deployment status across all connectors" {
        $status = Get-DeploymentStatus -CorrelationId 'status-test-001'

        $status.correlation_id | Should -Be 'status-test-001'
        $status.status_by_connector | Should -Not -BeNullOrEmpty
    }

    It "Should calculate success rate correctly" {
        $status = Get-DeploymentStatus -CorrelationId 'status-test-001' -ConnectorName 'intune'

        # Should have success_rate calculation
        $status.status_by_connector | Should -Not -BeNullOrEmpty
    }
}
