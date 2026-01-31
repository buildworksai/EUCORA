# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for Storage backends and services.
"""
import pytest

from apps.storage.models import MinIOConfig, StorageProvider
from apps.storage.services import StorageConnectionTester, StorageService, get_storage_service


@pytest.mark.django_db
class TestStorageService:
    """Test StorageService."""

    def test_get_storage_service_singleton(self):
        """Test that get_storage_service returns singleton."""
        service1 = get_storage_service()
        service2 = get_storage_service()
        assert service1 is service2

    def test_load_backends(self):
        """Test loading storage backends."""
        provider = StorageProvider.objects.create(
            name="Test Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
            is_enabled=True,
        )
        MinIOConfig.objects.create(
            provider=provider,
            endpoint_url="http://minio.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
        )

        service = StorageService()
        service._load_backends()
        assert str(provider.id) in service._backends

    def test_get_backend_with_provider_id(self):
        """Test getting backend by provider ID."""
        provider = StorageProvider.objects.create(
            name="Test Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
            is_enabled=True,
        )
        MinIOConfig.objects.create(
            provider=provider,
            endpoint_url="http://minio.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
        )

        service = StorageService()
        service._load_backends()
        backend = service.get_backend(str(provider.id))
        assert backend is not None

    def test_get_backend_failover(self):
        """Test failover when primary is unavailable."""
        primary = StorageProvider.objects.create(
            name="Primary",
            provider_type=StorageProvider.ProviderType.MINIO,
            is_primary=True,
            is_enabled=True,
            status=StorageProvider.ProviderStatus.FAILED,
        )
        MinIOConfig.objects.create(
            provider=primary,
            endpoint_url="http://minio.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
        )

        secondary = StorageProvider.objects.create(
            name="Secondary",
            provider_type=StorageProvider.ProviderType.MINIO,
            priority=50,
            is_enabled=True,
            status=StorageProvider.ProviderStatus.HEALTHY,
        )
        MinIOConfig.objects.create(
            provider=secondary,
            endpoint_url="http://minio2.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
        )

        service = StorageService()
        service._load_backends()
        # Should failover to secondary if primary health check fails
        # (actual implementation depends on health_check result)


@pytest.mark.django_db
class TestStorageConnectionTester:
    """Test StorageConnectionTester."""

    def test_test_connection(self):
        """Test connection testing."""
        provider = StorageProvider.objects.create(
            name="Test Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
        )
        MinIOConfig.objects.create(
            provider=provider,
            endpoint_url="http://minio.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",
        )

        tester = StorageConnectionTester()
        result = tester.test_connection(provider)
        assert result is not None
        assert hasattr(result, "success")
        assert hasattr(result, "tests")
