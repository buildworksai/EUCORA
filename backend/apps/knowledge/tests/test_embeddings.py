# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for embedding providers.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.knowledge.embeddings.cohere import CohereEmbeddingProvider
from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.embeddings.local import LocalEmbeddingProvider
from apps.knowledge.embeddings.openai import OpenAIEmbeddingProvider


@pytest.mark.asyncio
class TestOpenAIEmbeddingProvider:
    """Test OpenAI embedding provider."""

    @patch("apps.knowledge.embeddings.openai.AsyncOpenAI")
    async def test_embed(self, mock_openai_class):
        """Test single text embedding."""
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        mock_client.embeddings.create = AsyncMock(return_value=MagicMock(data=[MagicMock(embedding=[0.1] * 1536)]))

        provider = OpenAIEmbeddingProvider("test-key", "text-embedding-3-small")
        result = await provider.embed("Test text")

        assert len(result) == 1536
        assert result == [0.1] * 1536
        mock_client.embeddings.create.assert_called_once()

    @patch("apps.knowledge.embeddings.openai.AsyncOpenAI")
    async def test_embed_batch(self, mock_openai_class):
        """Test batch embedding."""
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        mock_client.embeddings.create = AsyncMock(
            return_value=MagicMock(
                data=[
                    MagicMock(embedding=[0.1] * 1536),
                    MagicMock(embedding=[0.2] * 1536),
                ]
            )
        )

        provider = OpenAIEmbeddingProvider("test-key", "text-embedding-3-small")
        results = await provider.embed_batch(["Text 1", "Text 2"])

        assert len(results) == 2
        assert len(results[0]) == 1536
        assert len(results[1]) == 1536

    def test_dimensions(self):
        """Test dimensions property."""
        provider = OpenAIEmbeddingProvider("test-key", "text-embedding-3-small")
        assert provider.dimensions == 1536

        provider_large = OpenAIEmbeddingProvider("test-key", "text-embedding-3-large")
        assert provider_large.dimensions == 3072

    def test_model_name(self):
        """Test model_name property."""
        provider = OpenAIEmbeddingProvider("test-key", "text-embedding-3-small")
        assert provider.model_name == "text-embedding-3-small"


@pytest.mark.asyncio
class TestCohereEmbeddingProvider:
    """Test Cohere embedding provider."""

    @patch("apps.knowledge.embeddings.cohere.AsyncClient")
    async def test_embed(self, mock_cohere_class):
        """Test single text embedding."""
        mock_client = AsyncMock()
        mock_cohere_class.return_value = mock_client
        mock_client.embed = AsyncMock(return_value=MagicMock(embeddings=[[0.1] * 1024]))

        provider = CohereEmbeddingProvider("test-key", "embed-english-v3.0")
        result = await provider.embed("Test text")

        assert len(result) == 1024
        mock_client.embed.assert_called_once()

    def test_dimensions(self):
        """Test dimensions property."""
        provider = CohereEmbeddingProvider("test-key", "embed-english-v3.0")
        assert provider.dimensions == 1024


@pytest.mark.asyncio
class TestLocalEmbeddingProvider:
    """Test Local embedding provider."""

    @patch("apps.knowledge.embeddings.local.SentenceTransformer")
    async def test_embed(self, mock_st_class):
        """Test single text embedding."""
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=[[0.1] * 384])
        mock_model.get_sentence_embedding_dimension = MagicMock(return_value=384)
        mock_st_class.return_value = mock_model

        provider = LocalEmbeddingProvider("all-MiniLM-L6-v2")
        result = await provider.embed("Test text")

        assert len(result) == 384
        mock_model.encode.assert_called_once()

    @patch("apps.knowledge.embeddings.local.SentenceTransformer")
    async def test_embed_batch(self, mock_st_class):
        """Test batch embedding."""
        mock_model = MagicMock()
        mock_model.encode = MagicMock(return_value=[[0.1] * 384, [0.2] * 384])
        mock_model.get_sentence_embedding_dimension = MagicMock(return_value=384)
        mock_st_class.return_value = mock_model

        provider = LocalEmbeddingProvider("all-MiniLM-L6-v2")
        results = await provider.embed_batch(["Text 1", "Text 2"])

        assert len(results) == 2
        assert len(results[0]) == 384


@pytest.mark.django_db
class TestEmbeddingService:
    """Test EmbeddingService factory."""

    def test_get_instance_singleton(self):
        """Test that get_instance returns singleton."""
        service1 = EmbeddingService.get_instance()
        service2 = EmbeddingService.get_instance()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initializing service with configs."""
        from apps.knowledge.models import EmbeddingConfig

        config = EmbeddingConfig.objects.create(
            provider=EmbeddingConfig.Provider.OPENAI,
            model_name="text-embedding-3-small",
            dimensions=1536,
            api_key="test-key",
            is_active=True,
            is_default=True,
        )

        service = EmbeddingService.get_instance()
        await service.initialize()

        assert str(config.id) in service._providers
        assert service._default_provider is not None
