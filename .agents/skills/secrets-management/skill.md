---
name: secrets-management
description: Secrets management patterns for EUCORA using Azure Key Vault, HashiCorp Vault, rotation policies, and External Secrets Operator. Use when configuring secrets, implementing rotation, or managing credentials.
status: ✅ Working
last-validated: 2026-01-30
---

# Secrets Management

Secure secrets handling for the EUCORA platform.

---

## Quick Reference

| Environment | Vault | Pattern |
|-------------|-------|---------|
| Production | Azure Key Vault | External Secrets Operator |
| Development | HashiCorp Vault (dev) | Environment variables |
| CI/CD | GitHub Secrets | Injected at runtime |

---

## FORBIDDEN Patterns

❌ **NEVER do these:**

```python
# ❌ FORBIDDEN - Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgres://user:password@host/db"

# ❌ FORBIDDEN - Secrets in code or .env files committed to git
# .env files should be in .gitignore

# ❌ FORBIDDEN - Secrets in Docker images
ENV SECRET_KEY=mysecrethardcoded
```

---

## Azure Key Vault Integration

### Python Client

```python
# backend/apps/core/secrets.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from functools import lru_cache
import os

class KeyVaultSecretManager:
    """Azure Key Vault secret manager."""

    def __init__(self):
        vault_url = os.environ.get('AZURE_KEYVAULT_URL')
        if not vault_url:
            raise ValueError("AZURE_KEYVAULT_URL not set")

        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    @lru_cache(maxsize=100)
    def get_secret(self, name: str) -> str:
        """Get secret value from Key Vault."""
        secret = self.client.get_secret(name)
        return secret.value

    def set_secret(self, name: str, value: str) -> None:
        """Set secret value in Key Vault."""
        self.client.set_secret(name, value)
        # Clear cache
        self.get_secret.cache_clear()

# Singleton instance
_manager = None

def get_secret(name: str) -> str:
    """Get secret from vault."""
    global _manager
    if _manager is None:
        _manager = KeyVaultSecretManager()
    return _manager.get_secret(name)

# Usage
database_url = get_secret('eucora-database-url')
intune_secret = get_secret('eucora-intune-client-secret')
```

### Django Settings Integration

```python
# backend/config/settings/production.py
from apps.core.secrets import get_secret

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_secret('eucora-db-name'),
        'USER': get_secret('eucora-db-user'),
        'PASSWORD': get_secret('eucora-db-password'),
        'HOST': get_secret('eucora-db-host'),
        'PORT': '5432',
    }
}

# Django secret key
SECRET_KEY = get_secret('eucora-django-secret-key')

# Connector credentials
INTUNE_CLIENT_ID = get_secret('eucora-intune-client-id')
INTUNE_CLIENT_SECRET = get_secret('eucora-intune-client-secret')
INTUNE_TENANT_ID = get_secret('eucora-intune-tenant-id')
```

---

## External Secrets Operator (Kubernetes)

### ClusterSecretStore

```yaml
# k8s/cluster-secret-store.yaml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: azure-keyvault
spec:
  provider:
    azurekv:
      authType: ManagedIdentity
      vaultUrl: "https://eucora-prod-kv.vault.azure.net"
      # For workload identity
      serviceAccountRef:
        name: external-secrets
        namespace: external-secrets
```

### ExternalSecret

```yaml
# k8s/external-secrets.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: eucora-secrets
  namespace: eucora
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: azure-keyvault
    kind: ClusterSecretStore
  target:
    name: eucora-secrets
    creationPolicy: Owner
  data:
    # Database
    - secretKey: DATABASE_URL
      remoteRef:
        key: eucora-database-url

    # Django
    - secretKey: SECRET_KEY
      remoteRef:
        key: eucora-django-secret-key

    # Intune connector
    - secretKey: INTUNE_CLIENT_ID
      remoteRef:
        key: eucora-intune-client-id
    - secretKey: INTUNE_CLIENT_SECRET
      remoteRef:
        key: eucora-intune-client-secret
    - secretKey: INTUNE_TENANT_ID
      remoteRef:
        key: eucora-intune-tenant-id

    # Jamf connector
    - secretKey: JAMF_API_URL
      remoteRef:
        key: eucora-jamf-api-url
    - secretKey: JAMF_CLIENT_ID
      remoteRef:
        key: eucora-jamf-client-id
    - secretKey: JAMF_CLIENT_SECRET
      remoteRef:
        key: eucora-jamf-client-secret
```

---

## Rotation Policies

### Rotation Schedule

| Secret Type | Rotation Interval | Method |
|-------------|-------------------|--------|
| Database passwords | 90 days | Automated |
| API keys | 30 days | Automated |
| Signing certificates | 365 days | Manual with CAB |
| Service principals | 90 days | Automated |
| JWT signing keys | 30 days | Automated |

### Automated Rotation (Azure)

```python
# backend/apps/core/rotation.py
from azure.keyvault.secrets import SecretClient
from datetime import datetime, timedelta
import secrets

class SecretRotator:
    """Automated secret rotation."""

    def __init__(self, client: SecretClient):
        self.client = client

    async def rotate_database_password(self, db_name: str) -> str:
        """Rotate database password."""
        # Generate new password
        new_password = secrets.token_urlsafe(32)

        # Update in vault
        secret_name = f"eucora-{db_name}-password"
        self.client.set_secret(
            secret_name,
            new_password,
            expires_on=datetime.utcnow() + timedelta(days=90),
        )

        # Update database user
        await self._update_db_password(db_name, new_password)

        # Log rotation event
        await self._log_rotation_event(secret_name)

        return new_password

    async def rotate_api_key(self, service: str) -> str:
        """Rotate API key for a service."""
        new_key = secrets.token_urlsafe(48)

        secret_name = f"eucora-{service}-api-key"
        self.client.set_secret(
            secret_name,
            new_key,
            expires_on=datetime.utcnow() + timedelta(days=30),
        )

        await self._log_rotation_event(secret_name)

        return new_key
```

### Celery Task for Rotation

```python
# backend/apps/core/tasks.py
from celery import shared_task

@shared_task
def check_secret_expiry():
    """Check for secrets expiring soon and rotate."""
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential

    client = SecretClient(
        vault_url=os.environ['AZURE_KEYVAULT_URL'],
        credential=DefaultAzureCredential(),
    )

    # List all secrets
    for secret_props in client.list_properties_of_secrets():
        if secret_props.expires_on:
            days_until_expiry = (secret_props.expires_on - datetime.utcnow()).days

            if days_until_expiry <= 7:
                # Alert for upcoming expiry
                send_alert(
                    f"Secret {secret_props.name} expires in {days_until_expiry} days"
                )

            if days_until_expiry <= 0:
                # Attempt auto-rotation if configured
                auto_rotate_secret(secret_props.name)
```

---

## Separation of Duties

### Vault Paths by Role

```
# Key Vault Access Policies

/secrets/eucora-packaging-*
  - Role: Packaging Engineer
  - Permissions: Get

/secrets/eucora-publishing-*
  - Role: Publisher
  - Permissions: Get

/secrets/eucora-platform-*
  - Role: Platform Admin
  - Permissions: Get, Set, Delete

/secrets/eucora-signing-*
  - Role: Security Reviewer
  - Permissions: Get, Set
```

### Azure RBAC

```bash
# Assign Key Vault Secrets User to packaging team
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee-object-id <packaging-group-id> \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/eucora-prod-kv/secrets/eucora-packaging-*

# Assign Key Vault Secrets Officer to platform admins
az role assignment create \
  --role "Key Vault Secrets Officer" \
  --assignee-object-id <platform-admin-group-id> \
  --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/eucora-prod-kv
```

---

## Break-Glass Procedures

### Emergency Access

```python
# Break-glass access requires:
# 1. Two authorized personnel (dual control)
# 2. Approval from Security Team
# 3. Time-limited access (4 hours max)
# 4. Full audit logging

class BreakGlassAccess:
    """Emergency credential access with dual control."""

    async def request_access(
        self,
        requestor: User,
        secret_name: str,
        justification: str,
        approver: User,
    ) -> str:
        """Request emergency access to a secret."""
        # Validate dual control
        if requestor.id == approver.id:
            raise PermissionError("Dual control required - different approver needed")

        # Check roles
        if not approver.has_role('security_reviewer'):
            raise PermissionError("Approver must be Security Reviewer")

        # Log the access request
        await AuditLog.objects.acreate(
            action='break_glass.requested',
            actor=requestor,
            target=secret_name,
            justification=justification,
            approver=approver,
            correlation_id=generate_correlation_id('brk'),
        )

        # Get secret with time-limited cache
        secret = await self._get_secret_with_audit(secret_name, requestor)

        return secret
```

---

## PowerShell Integration

```powershell
# scripts/utilities/Get-VaultSecret.ps1

function Get-VaultSecret {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$SecretName,

        [Parameter()]
        [string]$VaultName = $env:AZURE_KEYVAULT_NAME
    )

    # Get secret from Azure Key Vault
    $secret = az keyvault secret show `
        --vault-name $VaultName `
        --name $SecretName `
        --query value `
        --output tsv

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to retrieve secret: $SecretName"
    }

    return $secret
}

# Usage
$clientSecret = Get-VaultSecret -SecretName 'eucora-intune-client-secret'
```

---

## Checklist

### Setup

```
☐ Azure Key Vault created and configured
☐ Managed Identity assigned to services
☐ External Secrets Operator installed (k8s)
☐ ClusterSecretStore configured
☐ ExternalSecrets created for all services
```

### Operations

```
☐ Rotation policies documented
☐ Expiry alerts configured (7-day warning)
☐ Break-glass procedures documented
☐ SoD enforced via access policies
☐ Audit logging enabled
```

### Compliance

```
☐ No secrets in source code
☐ No secrets in Docker images
☐ Secrets rotated per schedule
☐ Access reviewed quarterly
☐ Break-glass usage audited
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Hardcoded credentials | Azure Key Vault / Vault |
| Secrets in .env (committed) | External Secrets Operator |
| Shared service principals | Separate per role (SoD) |
| No rotation | 30-90 day rotation |
| Single approver for break-glass | Dual control required |
