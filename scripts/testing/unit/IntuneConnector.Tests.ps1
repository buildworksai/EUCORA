# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI

BeforeAll {
    . "$PSScriptRoot/../../connectors/intune/IntuneConnector.ps1"
}

Describe "IntuneConnector - Publish-IntuneApplication" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
                tenant_id = 'test-tenant-id'
                ring_groups = @{
                    canary = 'group-canary-123'
                }
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock New-IntuneWin32App {
            return @{
                id = 'app-123'
                displayName = 'Test App'
            }
        }
        Mock New-IntuneAssignment {
            return @{ id = 'assignment-456' }
        }
        Mock Write-StructuredLog { }
    }

    It "Should publish application successfully" {
        $intent = @{
            AppName = 'Test App'
            Description = 'Test Description'
            Publisher = 'Test Publisher'
            Ring = 'Canary'
            FileName = 'test.intunewin'
            InstallCommand = 'install.exe /silent'
            UninstallCommand = 'uninstall.exe /silent'
            RequiresAdmin = $true
            DetectionPath = 'C:\Program Files\TestApp'
            DetectionFile = 'test.exe'
        }

        $result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId 'test-cid-001'

        $result.status | Should -Be 'published'
        $result.app_id | Should -Be 'app-123'
        $result.connector | Should -Be 'intune'
        Should -Invoke Get-ConnectorAuthToken -Times 1
        Should -Invoke New-IntuneWin32App -Times 1
        Should -Invoke New-IntuneAssignment -Times 1
    }

    It "Should return stub when credentials are missing" {
        Mock Get-ConnectorConfig {
            return @{ client_id = $null; client_secret = $null }
        }

        $intent = @{ AppName = 'Test App'; Ring = 'Canary' }
        $result = Publish-IntuneApplication -DeploymentIntent $intent -CorrelationId 'test-cid-002'

        $result.status | Should -Be 'stubbed'
        Should -Invoke Get-ConnectorAuthToken -Times 0
    }
}

Describe "IntuneConnector - New-IntuneWin32App" {
    BeforeEach {
        Mock Get-ConnectorConfig { return @{} }
        Mock Invoke-ConnectorRequest {
            return @{
                id = 'app-789'
                displayName = 'Mock App'
            }
        }
        Mock Write-StructuredLog { }
    }

    It "Should create Win32 app with correct payload" {
        $intent = @{
            AppName = 'Test App'
            Description = 'Test Description'
            Publisher = 'Test Publisher'
            FileName = 'test.intunewin'
            InstallCommand = 'install.exe /silent'
            UninstallCommand = 'uninstall.exe /silent'
            RequiresAdmin = $true
            RestartBehavior = 'suppress'
            DetectionPath = 'C:\Program Files\TestApp'
            DetectionFile = 'test.exe'
        }

        $result = New-IntuneWin32App -DeploymentIntent $intent -AccessToken 'mock-token' -CorrelationId 'test-cid-003'

        $result.id | Should -Be 'app-789'
        Should -Invoke Invoke-ConnectorRequest -Times 1 -ParameterFilter {
            $Method -eq 'POST' -and $Uri -match 'deviceAppManagement/mobileApps'
        }
    }

    It "Should set runAsAccount to system when RequiresAdmin is true" {
        $intent = @{
            AppName = 'Admin App'
            RequiresAdmin = $true
            InstallCommand = 'install.exe'
            UninstallCommand = 'uninstall.exe'
            DetectionPath = 'C:\Test'
            DetectionFile = 'test.exe'
        }

        $result = New-IntuneWin32App -DeploymentIntent $intent -AccessToken 'mock-token' -CorrelationId 'test-cid-004'

        Should -Invoke Invoke-ConnectorRequest -Times 1
    }
}

Describe "IntuneConnector - Get-IntuneDeploymentStatus" {
    BeforeEach {
        Mock Get-ConnectorConfig { return @{} }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Invoke-ConnectorRequest -ParameterFilter { $Uri -match 'mobileApps\?' } {
            return @{
                value = @(
                    @{
                        id = 'app-123'
                        displayName = 'Test App'
                        notes = 'CorrelationId: test-cid-005'
                    }
                )
            }
        }
        Mock Invoke-ConnectorRequest -ParameterFilter { $Uri -match 'deviceStatuses' } {
            return @{
                value = @(
                    @{ installState = 'installed' },
                    @{ installState = 'installed' },
                    @{ installState = 'failed' },
                    @{ installState = 'installing' }
                )
            }
        }
        Mock Write-StructuredLog { }
    }

    It "Should query deployment status successfully" {
        $result = Get-IntuneDeploymentStatus -CorrelationId 'test-cid-005'

        $result.status | Should -Be 'queried'
        $result.app_id | Should -Be 'app-123'
        $result.success_count | Should -Be 2
        $result.failure_count | Should -Be 1
        $result.pending_count | Should -Be 1
        $result.total_devices | Should -Be 4
        $result.success_rate | Should -Be 50
    }

    It "Should return not_found when no apps match correlation ID" {
        Mock Invoke-ConnectorRequest -ParameterFilter { $Uri -match 'mobileApps\?' } {
            return @{ value = @() }
        }

        $result = Get-IntuneDeploymentStatus -CorrelationId 'test-cid-006'

        $result.status | Should -Be 'not_found'
    }
}

Describe "IntuneConnector - Test-IntuneConnection" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                tenant_id = 'test-tenant-id'
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Get-CorrelationId { return 'test-cid-007' }
        Mock Write-StructuredLog { }
    }

    It "Should return healthy when connection succeeds" {
        Mock Invoke-ConnectorRequest {
            return @{ value = @() }
        }

        $result = Test-IntuneConnection -AuthToken 'dummy'

        $result.connector | Should -Be 'Intune'
        $result.status | Should -Be 'healthy'
        $result.tenant_id | Should -Be 'test-tenant-id'
    }

    It "Should return unhealthy when connection fails" {
        Mock Get-ConnectorAuthToken { throw "Authentication failed" }

        $result = Test-IntuneConnection -AuthToken 'dummy'

        $result.connector | Should -Be 'Intune'
        $result.status | Should -Be 'unhealthy'
        $result.error | Should -Match 'Authentication failed'
    }
}

Describe "IntuneConnector - Get-IntuneTargetDevices" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                ring_groups = @{
                    canary = 'group-canary-123'
                }
            }
        }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Get-CorrelationId { return 'test-cid-008' }
        Mock Invoke-ConnectorRequest {
            return @{
                value = @(
                    @{
                        '@odata.type' = '#microsoft.graph.device'
                        id = 'device-001'
                        displayName = 'Device 1'
                        operatingSystem = 'Windows'
                        approximateLastSignInDateTime = '2026-01-04T10:00:00Z'
                    },
                    @{
                        '@odata.type' = '#microsoft.graph.device'
                        id = 'device-002'
                        displayName = 'Device 2'
                        operatingSystem = 'Windows'
                        approximateLastSignInDateTime = '2026-01-04T11:00:00Z'
                    }
                )
            }
        }
        Mock Write-StructuredLog { }
    }

    It "Should retrieve target devices for ring" {
        $devices = Get-IntuneTargetDevices -Ring 'Canary'

        $devices.Count | Should -Be 2
        $devices[0].device_id | Should -Be 'device-001'
        $devices[0].ring | Should -Be 'Canary'
        $devices[1].device_id | Should -Be 'device-002'
    }

    It "Should return empty array when group ID is not configured" {
        Mock Get-ConnectorConfig {
            return @{ ring_groups = @{} }
        }

        $devices = Get-IntuneTargetDevices -Ring 'Lab'

        $devices | Should -BeNullOrEmpty
    }
}

Describe "IntuneConnector - Remove-IntuneApplication" {
    BeforeEach {
        Mock Get-ConnectorConfig { return @{} }
        Mock Get-ConnectorAuthToken { return 'mock-access-token' }
        Mock Invoke-ConnectorRequest { return @{} }
        Mock Write-StructuredLog { }
    }

    It "Should remove application successfully" {
        $result = Remove-IntuneApplication -ApplicationId 'app-123' -CorrelationId 'test-cid-009'

        $result.status | Should -Be 'removed'
        $result.app_id | Should -Be 'app-123'
        Should -Invoke Invoke-ConnectorRequest -Times 1 -ParameterFilter {
            $Method -eq 'DELETE' -and $Uri -match 'app-123'
        }
    }
}
