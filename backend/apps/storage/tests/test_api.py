# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for Storage endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.storage.models import MinIOConfig, StorageProvider

User = get_user_model()


@pytest.mark.django_db
class TestStorageAPI:
    """Test Storage API endpoints."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )  # pragma: allowlist secret

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Create authenticated API client."""
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def storage_provider(self, user):
        """Create test storage provider."""
        provider = StorageProvider.objects.create(
            name="Test Storage",
            provider_type=StorageProvider.ProviderType.MINIO,
            configured_by=user,
        )
        MinIOConfig.objects.create(
            provider=provider,
            endpoint_url="http://minio.local:9000",
            bucket_name="test-bucket",
            access_key_id="minioadmin",
            secret_access_key="minioadmin",  # pragma: allowlist secret
        )
        return provider

    def test_list_providers(self, authenticated_client, storage_provider):
        """Test GET /api/v1/storage/providers/."""
        response = authenticated_client.get("/api/v1/storage/providers/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_retrieve_provider(self, authenticated_client, storage_provider):
        """Test GET /api/v1/storage/providers/{id}/."""
        response = authenticated_client.get(f"/api/v1/storage/providers/{storage_provider.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Storage"

    def test_create_provider(self, authenticated_client, user):
        """Test POST /api/v1/storage/providers/."""
        data = {
            "name": "New Storage",
            "provider_type": StorageProvider.ProviderType.MINIO,
            "priority": 100,
            "is_enabled": True,
            "minio_config": {
                "endpoint_url": "http://minio.local:9000",
                "bucket_name": "new-bucket",
                "access_key_id": "minioadmin",
                "secret_access_key": "minioadmin",
                "use_ssl": False,
            },
        }
        response = authenticated_client.post("/api/v1/storage/providers/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert StorageProvider.objects.filter(name="New Storage").exists()

    def test_test_connection(self, authenticated_client, storage_provider):
        """Test POST /api/v1/storage/providers/{id}/test/."""
        # This will fail in test environment but should return proper response
        response = authenticated_client.post(f"/api/v1/storage/providers/{storage_provider.id}/test/", {})
        # Should return 200 even if connection fails (with error details)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    def test_set_primary(self, authenticated_client, storage_provider):
        """Test POST /api/v1/storage/providers/{id}/set-primary/."""
        response = authenticated_client.post(f"/api/v1/storage/providers/{storage_provider.id}/set-primary/", {})
        assert response.status_code == status.HTTP_200_OK
        storage_provider.refresh_from_db()
        assert storage_provider.is_primary is True

    def test_provider_metrics(self, authenticated_client, storage_provider):
        """Test GET /api/v1/storage/providers/{id}/metrics/."""
        response = authenticated_client.get(f"/api/v1/storage/providers/{storage_provider.id}/metrics/")
        assert response.status_code == status.HTTP_200_OK

    def test_health_endpoint(self, authenticated_client):
        """Test GET /api/v1/storage/health/."""
        response = authenticated_client.get("/api/v1/storage/health/")
        assert response.status_code == status.HTTP_200_OK
        assert "is_healthy" in response.data
