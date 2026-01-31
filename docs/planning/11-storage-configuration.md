# E2: Storage Configuration — Multi-Cloud Object Storage

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P1-Critical
**Dependencies**: None

---

## Overview

Enable administrators to configure object storage backends (MinIO, AWS S3, Azure Blob Storage) through the admin settings UI. This provides a unified storage abstraction layer for evidence packs, policy documents, artifacts, and other binary content.

---

## Requirements

### Functional Requirements

1. **Storage Provider Configuration**
   - MinIO (self-hosted, S3-compatible)
   - AWS S3 (cloud-native)
   - Azure Blob Storage (cloud-native)
   - Connection testing with validation feedback
   - Multiple provider configuration (primary + failover)

2. **Admin Settings Tab**
   - New "Storage" tab in Settings page
   - Provider selection with appropriate credential fields
   - Connection test button with detailed results
   - Health status indicators
   - Usage metrics (capacity, objects, bandwidth)

3. **Storage Operations**
   - Unified API for upload/download/delete
   - Automatic retry with exponential backoff
   - Failover to secondary provider
   - Presigned URL generation for direct access
   - Lifecycle policies (retention, archival)

4. **Security**
   - Encrypted credentials stored in vault
   - IAM role support (AWS) / Managed Identity (Azure)
   - Bucket/container access policies
   - Audit logging for all storage operations

---

## Data Model

### Backend Models (Django)

```python
# backend/apps/storage/models.py

class StorageProvider(TimeStampedModel):
    """Configured storage providers."""

    class ProviderType(models.TextChoices):
        MINIO = "minio", "MinIO (S3-Compatible)"
        AWS_S3 = "aws_s3", "AWS S3"
        AZURE_BLOB = "azure_blob", "Azure Blob Storage"

    class ProviderStatus(models.TextChoices):
        CONFIGURED = "configured", "Configured"
        TESTING = "testing", "Testing Connection"
        HEALTHY = "healthy", "Healthy"
        DEGRADED = "degraded", "Degraded"
        FAILED = "failed", "Connection Failed"
        DISABLED = "disabled", "Disabled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    provider_type = models.CharField(max_length=32, choices=ProviderType.choices)

    # Priority for failover
    priority = models.IntegerField(default=100)  # Lower = higher priority
    is_primary = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)

    # Connection status
    status = models.CharField(max_length=32, choices=ProviderStatus.choices, default=ProviderStatus.CONFIGURED)
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_check_error = models.TextField(blank=True)

    # Audit
    configured_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["priority", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_primary"],
                condition=models.Q(is_primary=True),
                name="unique_primary_provider"
            )
        ]


class MinIOConfig(TimeStampedModel):
    """MinIO-specific configuration."""

    provider = models.OneToOneField(StorageProvider, on_delete=models.CASCADE, related_name="minio_config")

    endpoint_url = models.URLField()  # e.g., http://minio.local:9000
    bucket_name = models.CharField(max_length=63)
    access_key_id = EncryptedCharField(max_length=256)
    secret_access_key = EncryptedCharField(max_length=256)
    use_ssl = models.BooleanField(default=True)
    region = models.CharField(max_length=64, default="us-east-1")

    # Optional
    path_style = models.BooleanField(default=True)  # MinIO uses path-style


class AWSS3Config(TimeStampedModel):
    """AWS S3-specific configuration."""

    provider = models.OneToOneField(StorageProvider, on_delete=models.CASCADE, related_name="s3_config")

    bucket_name = models.CharField(max_length=63)
    region = models.CharField(max_length=64)

    # Authentication method
    class AuthMethod(models.TextChoices):
        ACCESS_KEY = "access_key", "Access Key + Secret"
        IAM_ROLE = "iam_role", "IAM Role (EC2/ECS/EKS)"
        ASSUME_ROLE = "assume_role", "Assume Role (Cross-Account)"

    auth_method = models.CharField(max_length=32, choices=AuthMethod.choices, default=AuthMethod.ACCESS_KEY)
    access_key_id = EncryptedCharField(max_length=256, blank=True)
    secret_access_key = EncryptedCharField(max_length=256, blank=True)
    role_arn = models.CharField(max_length=256, blank=True)  # For assume_role
    external_id = models.CharField(max_length=256, blank=True)  # For assume_role

    # Optional
    endpoint_url = models.URLField(blank=True, null=True)  # For S3-compatible services
    kms_key_id = models.CharField(max_length=256, blank=True)  # Server-side encryption


class AzureBlobConfig(TimeStampedModel):
    """Azure Blob Storage-specific configuration."""

    provider = models.OneToOneField(StorageProvider, on_delete=models.CASCADE, related_name="azure_config")

    account_name = models.CharField(max_length=24)
    container_name = models.CharField(max_length=63)

    # Authentication method
    class AuthMethod(models.TextChoices):
        CONNECTION_STRING = "connection_string", "Connection String"
        ACCOUNT_KEY = "account_key", "Account Key"
        SAS_TOKEN = "sas_token", "SAS Token"
        MANAGED_IDENTITY = "managed_identity", "Managed Identity"
        SERVICE_PRINCIPAL = "service_principal", "Service Principal"

    auth_method = models.CharField(max_length=32, choices=AuthMethod.choices, default=AuthMethod.CONNECTION_STRING)
    connection_string = EncryptedCharField(max_length=1024, blank=True)
    account_key = EncryptedCharField(max_length=256, blank=True)
    sas_token = EncryptedCharField(max_length=1024, blank=True)

    # Service Principal
    tenant_id = models.CharField(max_length=36, blank=True)
    client_id = models.CharField(max_length=36, blank=True)
    client_secret = EncryptedCharField(max_length=256, blank=True)


class StorageMetrics(TimeStampedModel):
    """Storage usage metrics (collected periodically)."""

    provider = models.ForeignKey(StorageProvider, on_delete=models.CASCADE, related_name="metrics")
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    # Capacity
    total_bytes = models.BigIntegerField(default=0)
    used_bytes = models.BigIntegerField(default=0)
    object_count = models.BigIntegerField(default=0)

    # Operations (since last metric)
    uploads = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)
    deletes = models.IntegerField(default=0)
    bytes_uploaded = models.BigIntegerField(default=0)
    bytes_downloaded = models.BigIntegerField(default=0)

    # Errors
    failed_operations = models.IntegerField(default=0)

    class Meta:
        ordering = ["-recorded_at"]
```

---

## API Endpoints

```python
# backend/apps/storage/urls.py

# Storage Providers
GET    /api/v1/storage/providers/                    # List configured providers
POST   /api/v1/storage/providers/                    # Create new provider
GET    /api/v1/storage/providers/{id}/               # Get provider details
PUT    /api/v1/storage/providers/{id}/               # Update provider config
DELETE /api/v1/storage/providers/{id}/               # Delete provider
POST   /api/v1/storage/providers/{id}/test/          # Test connection
POST   /api/v1/storage/providers/{id}/set-primary/   # Set as primary

# Health & Metrics
GET    /api/v1/storage/health/                       # Overall storage health
GET    /api/v1/storage/providers/{id}/metrics/       # Provider metrics
GET    /api/v1/storage/providers/{id}/metrics/history/  # Historical metrics

# Storage Operations (internal, called by other services)
POST   /api/v1/storage/upload/                       # Upload file
GET    /api/v1/storage/download/{path}/              # Download file
DELETE /api/v1/storage/delete/{path}/                # Delete file
POST   /api/v1/storage/presigned-url/                # Generate presigned URL
```

---

## Storage Service Abstraction

### Interface

```python
# backend/apps/storage/services/base.py

from abc import ABC, abstractmethod
from typing import BinaryIO, AsyncGenerator

class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: str = None,
        metadata: dict = None,
    ) -> StorageResult:
        """Upload file to storage."""
        pass

    @abstractmethod
    async def download(self, path: str) -> AsyncGenerator[bytes, None]:
        """Download file as async stream."""
        pass

    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        pass

    @abstractmethod
    async def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """Generate presigned URL for direct access."""
        pass

    @abstractmethod
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[StorageObject]:
        """List objects in storage."""
        pass

    @abstractmethod
    async def health_check(self) -> HealthCheckResult:
        """Check storage health."""
        pass
```

### Implementations

```python
# backend/apps/storage/services/minio.py

class MinIOBackend(StorageBackend):
    """MinIO S3-compatible storage backend."""

    def __init__(self, config: MinIOConfig):
        self.config = config
        self.client = Minio(
            endpoint=config.endpoint_url.replace("http://", "").replace("https://", ""),
            access_key=config.access_key_id,
            secret_key=config.secret_access_key,
            secure=config.use_ssl,
        )


# backend/apps/storage/services/s3.py

class AWSS3Backend(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(self, config: AWSS3Config):
        self.config = config
        self.client = self._create_client()

    def _create_client(self):
        if self.config.auth_method == AWSS3Config.AuthMethod.IAM_ROLE:
            # Use default credential chain
            return boto3.client("s3", region_name=self.config.region)
        elif self.config.auth_method == AWSS3Config.AuthMethod.ASSUME_ROLE:
            # Assume role
            sts = boto3.client("sts")
            credentials = sts.assume_role(
                RoleArn=self.config.role_arn,
                ExternalId=self.config.external_id,
                RoleSessionName="eucora-storage",
            )["Credentials"]
            return boto3.client(
                "s3",
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"],
                region_name=self.config.region,
            )
        else:
            return boto3.client(
                "s3",
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                region_name=self.config.region,
            )


# backend/apps/storage/services/azure.py

class AzureBlobBackend(StorageBackend):
    """Azure Blob Storage backend."""

    def __init__(self, config: AzureBlobConfig):
        self.config = config
        self.client = self._create_client()

    def _create_client(self):
        if self.config.auth_method == AzureBlobConfig.AuthMethod.CONNECTION_STRING:
            return BlobServiceClient.from_connection_string(self.config.connection_string)
        elif self.config.auth_method == AzureBlobConfig.AuthMethod.MANAGED_IDENTITY:
            credential = DefaultAzureCredential()
            return BlobServiceClient(
                account_url=f"https://{self.config.account_name}.blob.core.windows.net",
                credential=credential,
            )
        # ... other auth methods
```

### Unified Storage Service

```python
# backend/apps/storage/services/storage.py

class StorageService:
    """Unified storage service with failover support."""

    def __init__(self):
        self._backends: dict[str, StorageBackend] = {}
        self._primary_id: str | None = None

    async def get_backend(self, provider_id: str = None) -> StorageBackend:
        """Get storage backend, with failover if primary fails."""
        if provider_id:
            return self._backends[provider_id]

        # Try primary
        if self._primary_id:
            backend = self._backends[self._primary_id]
            health = await backend.health_check()
            if health.is_healthy:
                return backend

        # Failover to next healthy provider
        for backend in self._get_backends_by_priority():
            health = await backend.health_check()
            if health.is_healthy:
                return backend

        raise StorageUnavailableError("No healthy storage providers available")

    async def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: str = None,
        metadata: dict = None,
        provider_id: str = None,
    ) -> StorageResult:
        """Upload with automatic retry and failover."""
        backend = await self.get_backend(provider_id)

        for attempt in range(3):
            try:
                return await backend.upload(path, file, content_type, metadata)
            except TransientError as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## Frontend Components

### Storage Settings Tab

```tsx
// frontend/src/routes/settings/StorageTab.tsx

export default function StorageTab() {
  return (
    <div className="space-y-6">
      {/* Storage Health Overview */}
      <Card className="glass">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="h-5 w-5 text-eucora-teal" />
            Storage Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard title="Primary Provider" value={primaryProvider?.name} status={primaryProvider?.status} />
            <StatCard title="Total Storage" value={formatBytes(totalUsed)} />
            <StatCard title="Objects" value={formatNumber(objectCount)} />
          </div>
        </CardContent>
      </Card>

      {/* Configured Providers */}
      <Card className="glass">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Storage Providers</CardTitle>
              <CardDescription>Configure object storage backends</CardDescription>
            </div>
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Provider
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {providers.map(provider => (
            <ProviderCard key={provider.id} provider={provider} />
          ))}
        </CardContent>
      </Card>

      {/* Add/Edit Provider Dialog */}
      <ProviderDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSave={handleSaveProvider}
      />
    </div>
  );
}
```

### Provider Configuration Form

```tsx
// frontend/src/components/storage/ProviderForm.tsx

// Dynamic form based on provider type
const PROVIDER_FIELDS = {
  minio: [
    { name: "endpoint_url", label: "Endpoint URL", type: "url", required: true },
    { name: "bucket_name", label: "Bucket Name", type: "text", required: true },
    { name: "access_key_id", label: "Access Key ID", type: "password", required: true },
    { name: "secret_access_key", label: "Secret Access Key", type: "password", required: true },
    { name: "use_ssl", label: "Use SSL", type: "switch", default: true },
    { name: "region", label: "Region", type: "text", default: "us-east-1" },
  ],
  aws_s3: [
    { name: "bucket_name", label: "Bucket Name", type: "text", required: true },
    { name: "region", label: "AWS Region", type: "select", options: AWS_REGIONS, required: true },
    { name: "auth_method", label: "Authentication", type: "select", options: S3_AUTH_METHODS, required: true },
    // Conditional fields based on auth_method
  ],
  azure_blob: [
    { name: "account_name", label: "Storage Account", type: "text", required: true },
    { name: "container_name", label: "Container Name", type: "text", required: true },
    { name: "auth_method", label: "Authentication", type: "select", options: AZURE_AUTH_METHODS, required: true },
    // Conditional fields based on auth_method
  ],
};
```

---

## Configuration Testing

```python
# backend/apps/storage/services/testing.py

class StorageConnectionTester:
    """Test storage provider connections."""

    async def test_connection(self, provider: StorageProvider) -> ConnectionTestResult:
        """Run comprehensive connection test."""
        results = []

        # 1. Basic connectivity
        results.append(await self._test_connectivity(provider))

        # 2. Authentication
        results.append(await self._test_authentication(provider))

        # 3. Bucket/container access
        results.append(await self._test_bucket_access(provider))

        # 4. Write permission
        results.append(await self._test_write_permission(provider))

        # 5. Read permission
        results.append(await self._test_read_permission(provider))

        # 6. Delete permission
        results.append(await self._test_delete_permission(provider))

        return ConnectionTestResult(
            success=all(r.success for r in results),
            tests=results,
        )
```

---

## Security Considerations

1. **Credential Storage**: All secrets encrypted with Fernet (AES-128) at rest
2. **Credential Rotation**: Support for credential rotation without downtime
3. **IAM/Managed Identity**: Prefer cloud-native auth over static keys
4. **Bucket Policies**: Validate bucket policies allow required operations
5. **Audit Logging**: Log all storage operations with correlation IDs

---

## Deliverables

1. `backend/apps/storage/` Django app with provider models and services
2. `frontend/src/routes/settings/StorageTab.tsx` settings page
3. `frontend/src/components/storage/` component library
4. Migration scripts for existing storage references
5. API documentation in `docs/api/storage-api.yaml`
