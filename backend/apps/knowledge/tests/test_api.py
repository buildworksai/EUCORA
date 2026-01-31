# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for Knowledge endpoints.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.knowledge.models import EmbeddingConfig, KnowledgeVector

User = get_user_model()


@pytest.mark.django_db
class TestKnowledgeAPI:
    """Test Knowledge API endpoints."""

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
    def embedding_config(self):
        """Create test embedding config."""
        return EmbeddingConfig.objects.create(
            provider=EmbeddingConfig.Provider.OPENAI,
            model_name="text-embedding-3-small",
            dimensions=1536,
            api_key="test-key",  # pragma: allowlist secret
            is_active=True,
            is_default=True,
        )

    def test_list_embedding_configs(self, authenticated_client, embedding_config):
        """Test listing embedding configurations."""
        response = authenticated_client.get("/api/v1/knowledge/config/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_embedding_config(self, authenticated_client):
        """Test creating embedding configuration."""
        data = {
            "provider": "openai",
            "model_name": "text-embedding-3-small",
            "dimensions": 1536,
            "api_key": "test-key",
            "is_active": True,
            "is_default": False,
        }
        response = authenticated_client.post("/api/v1/knowledge/config/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["provider"] == "openai"

    def test_update_embedding_config(self, authenticated_client, embedding_config):
        """Test updating embedding configuration."""
        data = {"is_active": False}
        response = authenticated_client.patch(f"/api/v1/knowledge/config/{embedding_config.id}/", data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    @patch("apps.knowledge.views.EmbeddingService")
    def test_test_embedding_provider(self, mock_service_class, authenticated_client, embedding_config):
        """Test testing embedding provider."""
        mock_service = MagicMock()
        mock_provider = MagicMock()
        mock_provider.embed = AsyncMock(return_value=[0.1] * 1536)
        mock_service._create_provider.return_value = mock_provider
        mock_service_class.get_instance.return_value = mock_service

        response = authenticated_client.post(
            f"/api/v1/knowledge/config/{embedding_config.id}/test/",
            {"test_text": "Test sentence"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

    @patch("apps.knowledge.views.EmbeddingService")
    def test_search(self, mock_service_class, authenticated_client):
        """Test semantic search."""
        mock_service = MagicMock()
        mock_retrieval = MagicMock()
        mock_retrieval.search = AsyncMock(return_value=[])
        mock_service_class.get_instance.return_value = mock_service

        with patch("apps.knowledge.views.KnowledgeRetrievalService") as mock_retrieval_class:
            mock_retrieval_class.return_value = mock_retrieval
            response = authenticated_client.post(
                "/api/v1/knowledge/search/search/",
                {
                    "query": "test query",
                    "top_k": 10,
                    "min_similarity": 0.7,
                },
            )
            assert response.status_code == status.HTTP_200_OK

    def test_stats(self, authenticated_client):
        """Test getting index statistics."""
        # Create test vector
        KnowledgeVector.objects.create(
            source_type=KnowledgeVector.SourceType.POLICY_DOCUMENT,
            source_id=uuid.uuid4(),
            content="Test content",
            content_hash=KnowledgeVector.hash_content("Test content"),
            embedding=[0.1] * 1536,
            embedding_model="test-model",
        )

        response = authenticated_client.get("/api/v1/knowledge/search/stats/")
        assert response.status_code == status.HTTP_200_OK
        assert "total_vectors" in response.data
