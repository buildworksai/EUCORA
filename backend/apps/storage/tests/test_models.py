# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for Storage app.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.storage.models import AWSS3Config, AzureBlobConfig, MinIOConfig, StorageMetrics, StorageProvider

User = get_user_model()


@pytest.mark.django_db
class TestStorageProvider:
    """Test StorageProvider model."""

    def test_create_storage_provider(self):
        """Test creating a storage provider."""
        provider = StorageProvider.objects.create(
            name="Test Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
            priority=100,
            is_primary=False,
            is_enabled=True,
        )
        assert provider.name == "Test Storage"
        assert provider.provider_type == StorageProvider.ProviderType.MINIO
        assert provider.status == StorageProvider.ProviderStatus.CONFIGURED

    def test_unique_primary_provider(self):
        """Test that only one provider can be primary."""
        StorageProvider.objects.create(
            name="Primary",
            provider_type=StorageProvider.ProviderType.MINIO,
            is_primary=True,
        )
        # Creating second primary should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            StorageProvider.objects.create(
                name="Secondary",
                provider_type=StorageProvider.ProviderType.AWS_S3,
                is_primary=True,
            )


@pytest.mark.django_db
class TestMinIOConfig:
    """Test MinIOConfig model."""

    def test_create_minio_config(self):
        """Test creating MinIO configuration."""
        provider = StorageProvider.objects.create(
            name="MinIO Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
        )
        config = MinIOConfig.objects.create(
            provider=provider,
            endpoint_url="http://minio.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
            use_ssl=False,
            region="us-east-1",
        )
        assert config.provider == provider
        assert config.endpoint_url == "http://minio.local:9000"
        assert config.bucket_name == "test-bucket"


@pytest.mark.django_db
class TestAWSS3Config:
    """Test AWSS3Config model."""

    def test_create_s3_config(self):
        """Test creating AWS S3 configuration."""
        provider = StorageProvider.objects.create(
            name="AWS S3 Storage",
            provider_type=StorageProvider.ProviderType.AWS_S3,
        )
        config = AWSS3Config.objects.create(
            provider=provider,
            bucket_name="test-bucket",
            region="us-east-1",
            auth_method=AWSS3Config.AuthMethod.ACCESS_KEY,
            access_key_id="AKIA...",
            secret_access_key="secret",
        )
        assert config.provider == provider
        assert config.bucket_name == "test-bucket"
        assert config.auth_method == AWSS3Config.AuthMethod.ACCESS_KEY


@pytest.mark.django_db
class TestAzureBlobConfig:
    """Test AzureBlobConfig model."""

    def test_create_azure_config(self):
        """Test creating Azure Blob configuration."""
        provider = StorageProvider.objects.create(
            name="Azure Storage",
            provider_type=StorageProvider.ProviderType.AZURE_BLOB,
        )
        config = AzureBlobConfig.objects.create(
            provider=provider,
            account_name="testaccount",
            container_name="test-container",
            auth_method=AzureBlobConfig.AuthMethod.CONNECTION_STRING,
            connection_string="DefaultEndpointsProtocol=https;...",
        )
        assert config.provider == provider
        assert config.account_name == "testaccount"
        assert config.auth_method == AzureBlobConfig.AuthMethod.CONNECTION_STRING


@pytest.mark.django_db
class TestStorageMetrics:
    """Test StorageMetrics model."""

    def test_create_storage_metrics(self):
        """Test creating storage metrics."""
        provider = StorageProvider.objects.create(
            name="Test Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
        )
        metrics = StorageMetrics.objects.create(
            provider=provider,
            total_bytes=1000000,
            used_bytes=500000,
            object_count=100,
            uploads=10,
            downloads=5,
        )
        assert metrics.provider == provider
        assert metrics.total_bytes == 1000000
        assert metrics.used_bytes == 500000
        assert metrics.object_count == 100
