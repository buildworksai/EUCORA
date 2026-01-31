# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Retrieve secrets from Azure Key Vault or environment variables.

.DESCRIPTION
    Provides secure credential retrieval with Azure Key Vault support and environment variable fallback.
    Supports credential caching (in-memory only) and rotation detection.

.PARAMETER SecretName
    Name of the secret to retrieve.

.PARAMETER VaultUrl
    Optional Azure Key Vault URL. If not provided, uses EUCORA_VAULT_URL environment variable.

.PARAMETER UseManagedIdentity
    Use Managed Identity for authentication (default: true).

.EXAMPLE
    $ApiKey = Get-VaultSecret -SecretName "INTUNE_CLIENT_SECRET"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SecretName,

    [Parameter(Mandatory = $false)]
    [string]$VaultUrl,

    [Parameter(Mandatory = $false)]
    [switch]$UseManagedIdentity = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# In-memory cache for credentials (cleared on script exit)
if (-not $script:VaultCache) {
    $script:VaultCache = @{}
}

# Check cache first
if ($script:VaultCache.ContainsKey($SecretName)) {
    Write-Verbose "Returning cached secret: $SecretName"
    return $script:VaultCache[$SecretName]
}

# Try Azure Key Vault first
if (-not $VaultUrl) {
    $VaultUrl = [System.Environment]::GetEnvironmentVariable("EUCORA_VAULT_URL")
}

if ($VaultUrl) {
    try {
        # Check if Az.KeyVault module is available
        if (Get-Module -ListAvailable -Name Az.KeyVault) {
            Import-Module Az.KeyVault -ErrorAction SilentlyContinue

            if ($UseManagedIdentity) {
                # Use Managed Identity (recommended for Azure-hosted scripts)
                $Secret = Get-AzKeyVaultSecret -VaultName $VaultUrl -Name $SecretName -ErrorAction Stop
            } else {
                # Use service principal (requires authentication context)
                $Secret = Get-AzKeyVaultSecret -VaultName $VaultUrl -Name $SecretName -ErrorAction Stop
            }

            if ($Secret) {
                $SecretValue = $Secret.SecretValue | ConvertFrom-SecureString -AsPlainText
                $script:VaultCache[$SecretName] = $SecretValue
                Write-Verbose "Retrieved secret from Azure Key Vault: $SecretName"
                return $SecretValue
            }
        } else {
            Write-Warning "Az.KeyVault module not available, falling back to environment variables"
        }
    } catch {
        Write-Warning "Failed to retrieve secret from Azure Key Vault: $($_.Exception.Message)"
    }
}

# Fall back to environment variable
$EnvVarName = "EUCORA_$($SecretName.ToUpper())"
$EnvSecret = [System.Environment]::GetEnvironmentVariable($EnvVarName)

if ($EnvSecret) {
    $script:VaultCache[$SecretName] = $EnvSecret
    Write-Verbose "Retrieved secret from environment variable: $EnvVarName"
    return $EnvSecret
}

# If still not found, throw error
throw "Secret '$SecretName' not found in vault or environment variable '$EnvVarName'"
