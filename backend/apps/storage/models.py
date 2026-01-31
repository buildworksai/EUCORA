# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Storage models for EUCORA Control Plane.

Implements multi-cloud object storage configuration with:
- MinIO (S3-compatible)
- AWS S3
- Azure Blob Storage
- Provider health monitoring and metrics
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.core.encryption import EncryptedCharField, EncryptedTextField
from apps.core.models import TimeStampedModel

User = get_user_model()


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
    priority = models.IntegerField(default=100, help_text="Lower = higher priority")
    is_primary = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=True)

    # Connection status
    status = models.CharField(max_length=32, choices=ProviderStatus.choices, default=ProviderStatus.CONFIGURED)
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_check_error = models.TextField(blank=True)

    # Audit
    configured_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="storage_providers"
    )

    class Meta:
        ordering = ["priority", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["is_primary"],
                condition=models.Q(is_primary=True),
                name="unique_primary_provider",
            )
        ]
        verbose_name = "Storage Provider"
        verbose_name_plural = "Storage Providers"

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class MinIOConfig(TimeStampedModel):
    """MinIO-specific configuration."""

    provider = models.OneToOneField(StorageProvider, on_delete=models.CASCADE, related_name="minio_config")

    endpoint_url = models.URLField(help_text="e.g., http://minio.local:9000")
    bucket_name = models.CharField(max_length=63)
    access_key_id = EncryptedCharField(max_length=256)
    secret_access_key = EncryptedCharField(max_length=256)
    use_ssl = models.BooleanField(default=True)
    region = models.CharField(max_length=64, default="us-east-1")

    # Optional
    path_style = models.BooleanField(default=True, help_text="MinIO uses path-style URLs")

    class Meta:
        verbose_name = "MinIO Configuration"
        verbose_name_plural = "MinIO Configurations"

    def __str__(self):
        return f"MinIO: {self.bucket_name}@{self.endpoint_url}"


class AWSS3Config(TimeStampedModel):
    """AWS S3-specific configuration."""

    class AuthMethod(models.TextChoices):
        ACCESS_KEY = "access_key", "Access Key + Secret"
        IAM_ROLE = "iam_role", "IAM Role (EC2/ECS/EKS)"
        ASSUME_ROLE = "assume_role", "Assume Role (Cross-Account)"

    provider = models.OneToOneField(StorageProvider, on_delete=models.CASCADE, related_name="s3_config")

    bucket_name = models.CharField(max_length=63)
    region = models.CharField(max_length=64)

    # Authentication method
    auth_method = models.CharField(max_length=32, choices=AuthMethod.choices, default=AuthMethod.ACCESS_KEY)
    access_key_id = EncryptedCharField(max_length=256, blank=True)
    secret_access_key = EncryptedCharField(max_length=256, blank=True)
    role_arn = models.CharField(max_length=256, blank=True, help_text="For assume_role")
    external_id = models.CharField(max_length=256, blank=True, help_text="For assume_role")

    # Optional
    endpoint_url = models.URLField(blank=True, null=True, help_text="For S3-compatible services")
    kms_key_id = models.CharField(max_length=256, blank=True, help_text="Server-side encryption KMS key")

    class Meta:
        verbose_name = "AWS S3 Configuration"
        verbose_name_plural = "AWS S3 Configurations"

    def __str__(self):
        return f"AWS S3: {self.bucket_name}@{self.region}"


class AzureBlobConfig(TimeStampedModel):
    """Azure Blob Storage-specific configuration."""

    class AuthMethod(models.TextChoices):
        CONNECTION_STRING = "connection_string", "Connection String"
        ACCOUNT_KEY = "account_key", "Account Key"
        SAS_TOKEN = "sas_token", "SAS Token"
        MANAGED_IDENTITY = "managed_identity", "Managed Identity"
        SERVICE_PRINCIPAL = "service_principal", "Service Principal"

    provider = models.OneToOneField(StorageProvider, on_delete=models.CASCADE, related_name="azure_config")

    account_name = models.CharField(max_length=24)
    container_name = models.CharField(max_length=63)

    # Authentication method
    auth_method = models.CharField(max_length=32, choices=AuthMethod.choices, default=AuthMethod.CONNECTION_STRING)
    connection_string = EncryptedTextField(blank=True)
    account_key = EncryptedCharField(max_length=256, blank=True)
    sas_token = EncryptedTextField(blank=True)

    # Service Principal
    tenant_id = models.CharField(max_length=36, blank=True)
    client_id = models.CharField(max_length=36, blank=True)
    client_secret = EncryptedCharField(max_length=256, blank=True)

    class Meta:
        verbose_name = "Azure Blob Configuration"
        verbose_name_plural = "Azure Blob Configurations"

    def __str__(self):
        return f"Azure Blob: {self.container_name}@{self.account_name}"


class StorageMetrics(TimeStampedModel):
    """Storage usage metrics (collected periodically)."""

    provider = models.ForeignKey(StorageProvider, on_delete=models.CASCADE, related_name="metrics")
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

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
        verbose_name = "Storage Metric"
        verbose_name_plural = "Storage Metrics"

    def __str__(self):
        return f"{self.provider.name} - {self.recorded_at}"
