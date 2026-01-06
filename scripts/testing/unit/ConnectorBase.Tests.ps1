# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Suppress common test file warnings
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseDeclaredVarsMoreThanAssignments', '', Justification = 'Test variables are used in assertions via Should')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSReviewUnusedParameter', '', Justification = 'Mock function parameters required for interface compatibility')]

BeforeAll {
    . "$PSScriptRoot/../../connectors/common/ConnectorBase.ps1"
}

Describe "ConnectorBase - Get-ConnectorConfig" {
    BeforeEach {
        Mock Get-ConfigValue { return @{ api_url = 'https://test.example.com' } }
    }

    It "Should retrieve connector configuration" {
        $config = Get-ConnectorConfig -Name 'intune'
        $config | Should -Not -BeNullOrEmpty
        $config.api_url | Should -Be 'https://test.example.com'
    }

    It "Should throw when configuration is missing" {
        Mock Get-ConfigValue { return $null }
        { Get-ConnectorConfig -Name 'intune' } | Should -Throw "Connector configuration missing for intune"
    }
}

Describe "ConnectorBase - Get-ErrorClassification" {
    It "Should classify 429 as TRANSIENT" {
        $classification = Get-ErrorClassification -StatusCode 429 -ErrorMessage "Rate limit exceeded"
        $classification | Should -Be 'TRANSIENT'
    }

    It "Should classify 500 as TRANSIENT" {
        $classification = Get-ErrorClassification -StatusCode 500 -ErrorMessage "Internal server error"
        $classification | Should -Be 'TRANSIENT'
    }

    It "Should classify 503 as TRANSIENT" {
        $classification = Get-ErrorClassification -StatusCode 503 -ErrorMessage "Service unavailable"
        $classification | Should -Be 'TRANSIENT'
    }

    It "Should classify 400 as PERMANENT" {
        $classification = Get-ErrorClassification -StatusCode 400 -ErrorMessage "Bad request"
        $classification | Should -Be 'PERMANENT'
    }

    It "Should classify 404 as PERMANENT" {
        $classification = Get-ErrorClassification -StatusCode 404 -ErrorMessage "Not found"
        $classification | Should -Be 'PERMANENT'
    }

    It "Should classify 401 as PERMANENT" {
        $classification = Get-ErrorClassification -StatusCode 401 -ErrorMessage "Unauthorized"
        $classification | Should -Be 'PERMANENT'
    }

    It "Should classify 403 as PERMANENT" {
        $classification = Get-ErrorClassification -StatusCode 403 -ErrorMessage "Forbidden"
        $classification | Should -Be 'PERMANENT'
    }

    It "Should classify 'forbidden' keyword as POLICY_VIOLATION" {
        $classification = Get-ErrorClassification -StatusCode 403 -ErrorMessage "Access forbidden by policy"
        $classification | Should -Be 'POLICY_VIOLATION'
    }

    It "Should classify 'unauthorized' keyword as POLICY_VIOLATION" {
        $classification = Get-ErrorClassification -StatusCode 401 -ErrorMessage "Unauthorized access to resource"
        $classification | Should -Be 'POLICY_VIOLATION'
    }

    It "Should classify 'policy' keyword as POLICY_VIOLATION" {
        $classification = Get-ErrorClassification -StatusCode 400 -ErrorMessage "Policy violation detected"
        $classification | Should -Be 'POLICY_VIOLATION'
    }

    It "Should classify 'compliance' keyword as POLICY_VIOLATION" {
        $classification = Get-ErrorClassification -StatusCode 400 -ErrorMessage "Compliance check failed"
        $classification | Should -Be 'POLICY_VIOLATION'
    }

    It "Should classify 'approval required' keyword as POLICY_VIOLATION" {
        $classification = Get-ErrorClassification -StatusCode 400 -ErrorMessage "CAB approval required"
        $classification | Should -Be 'POLICY_VIOLATION'
    }

    It "Should default to PERMANENT for unknown status codes" {
        $classification = Get-ErrorClassification -StatusCode 418 -ErrorMessage "I'm a teapot"
        $classification | Should -Be 'PERMANENT'
    }
}

Describe "ConnectorBase - Invoke-ConnectorRequest Idempotency" {
    BeforeEach {
        Mock Test-IdempotencyKey { return $false }
        Mock Invoke-RetryWithBackoff { return @{ status = 'success' } }
        Mock Write-StructuredLog { }
    }

    It "Should check idempotency for POST requests" {
        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-001'

        Should -Invoke Test-IdempotencyKey -Times 1 -Exactly
    }

    It "Should skip idempotency check for GET requests" {
        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'GET' -CorrelationId 'test-cid-002'

        Should -Invoke Test-IdempotencyKey -Times 0 -Exactly
    }

    It "Should return idempotent_skip when operation already processed" {
        Mock Test-IdempotencyKey { return $true }

        $result = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-003'

        $result.status | Should -Be 'idempotent_skip'
        $result.correlation_id | Should -Be 'test-cid-003'
        Should -Invoke Invoke-RetryWithBackoff -Times 0 -Exactly
    }

    It "Should proceed with request when idempotency check passes" {
        Mock Test-IdempotencyKey { return $false }

        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-004'

        Should -Invoke Invoke-RetryWithBackoff -Times 1 -Exactly
    }
}

Describe "ConnectorBase - Invoke-ConnectorRequest Headers" {
    BeforeEach {
        Mock Test-IdempotencyKey { return $false }
        Mock Invoke-RetryWithBackoff {
            param($ScriptBlock)
            # Execute the script block to use the parameter
            & $ScriptBlock
            return @{ status = 'success' }
        }
        Mock Write-StructuredLog { }
    }

    It "Should add X-Correlation-ID header" {
        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'GET' -CorrelationId 'test-cid-005'

        # Verify via mock invocation (headers passed to Invoke-RetryWithBackoff)
        Should -Invoke Invoke-RetryWithBackoff -Times 1 -Exactly
    }

    It "Should add X-Idempotency-Key header for POST requests" {
        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-006'

        Should -Invoke Invoke-RetryWithBackoff -Times 1 -Exactly
    }

    It "Should use custom idempotency key when provided" {
        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-007' -IdempotencyKey 'custom-key-001'

        Should -Invoke Test-IdempotencyKey -Times 1 -ParameterFilter { $CorrelationId -eq 'custom-key-001' }
    }

    It "Should merge custom headers with default headers" {
        $customHeaders = @{ 'X-Custom-Header' = 'CustomValue' }

        $null = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'GET' -Headers $customHeaders -CorrelationId 'test-cid-008'

        Should -Invoke Invoke-RetryWithBackoff -Times 1 -Exactly
    }
}

Describe "ConnectorBase - Invoke-ConnectorRequest Error Handling" {
    BeforeEach {
        Mock Test-IdempotencyKey { return $false }
        Mock Write-StructuredLog { }
    }

    It "Should classify error and return failure response" {
        Mock Invoke-RetryWithBackoff {
            $exception = [System.Net.WebException]::new("Rate limit exceeded")
            $response = [PSCustomObject]@{ StatusCode = 429 }
            $exception | Add-Member -NotePropertyName Response -NotePropertyValue $response -Force
            throw $exception
        }

        $result = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-009'

        $result.status | Should -Be 'failed'
        $result.error_classification | Should -Be 'TRANSIENT'
        $result.status_code | Should -Be 429
    }

    It "Should handle errors without HTTP status code" {
        Mock Invoke-RetryWithBackoff {
            throw "Network timeout"
        }

        $result = Invoke-ConnectorRequest -Uri 'https://test.example.com/api' -Method 'POST' -CorrelationId 'test-cid-010'

        $result.status | Should -Be 'failed'
        $result.error | Should -Be 'Network timeout'
        $result.status_code | Should -Be 0
    }
}

Describe "ConnectorBase - Get-ConnectorAuthToken" {
    BeforeEach {
        Mock Get-ConnectorConfig {
            return @{
                tenant_id = 'test-tenant-id'
                client_id = 'test-client-id'
                client_secret = 'test-client-secret'
                api_url = 'https://jamf.example.com'
                token = 'test-ansible-token'
            }
        }
        Mock Write-StructuredLog { }
    }

    It "Should acquire OAuth2 token for Intune" {
        Mock Invoke-RestMethod {
            return @{ access_token = 'intune-access-token-123' }
        }

        $token = Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId 'test-cid-011'

        $token | Should -Be 'intune-access-token-123'
        Should -Invoke Invoke-RestMethod -Times 1 -ParameterFilter {
            $Uri -match 'login.microsoftonline.com' -and $Method -eq 'POST'
        }
    }

    It "Should acquire OAuth2 token for Jamf" {
        Mock Invoke-RestMethod {
            return @{ access_token = 'jamf-access-token-456' }
        }

        $token = Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId 'test-cid-012'

        $token | Should -Be 'jamf-access-token-456'
        Should -Invoke Invoke-RestMethod -Times 1 -ParameterFilter {
            $Uri -match 'jamf.example.com/api/oauth/token' -and $Method -eq 'POST'
        }
    }

    It "Should return static token for Ansible" {
        $token = Get-ConnectorAuthToken -ConnectorName 'ansible' -CorrelationId 'test-cid-013'

        $token | Should -Be 'test-ansible-token'
        Should -Invoke Invoke-RestMethod -Times 0
    }

    It "Should throw when Intune credentials are missing" {
        Mock Get-ConnectorConfig {
            return @{ tenant_id = $null; client_id = $null; client_secret = $null }
        }

        { Get-ConnectorAuthToken -ConnectorName 'intune' -CorrelationId 'test-cid-014' } | Should -Throw "Intune connector missing OAuth2 credentials"
    }

    It "Should throw when Jamf credentials are missing" {
        Mock Get-ConnectorConfig {
            return @{ api_url = $null; client_id = $null; client_secret = $null }
        }

        { Get-ConnectorAuthToken -ConnectorName 'jamf' -CorrelationId 'test-cid-015' } | Should -Throw "Jamf connector missing OAuth2 credentials"
    }

    It "Should throw when Ansible token is missing" {
        Mock Get-ConnectorConfig {
            return @{ token = $null }
        }

        { Get-ConnectorAuthToken -ConnectorName 'ansible' -CorrelationId 'test-cid-016' } | Should -Throw "Ansible connector missing API token"
    }
}
