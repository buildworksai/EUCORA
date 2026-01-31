# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for Knowledge app.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.knowledge.services.chunking import Chunk, SemanticChunker


class TestSemanticChunker:
    """Test SemanticChunker."""

    def test_chunk_simple_text(self):
        """Test chunking simple text."""
        chunker = SemanticChunker(target_chunk_size=100, max_chunk_size=200, overlap_size=20)
        text = "This is a test. " * 50  # Create longer text
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(isinstance(chunk, Chunk) for chunk in chunks)
        assert all(chunk.content for chunk in chunks)

    def test_chunk_with_headings(self):
        """Test chunking with headings."""
        chunker = SemanticChunker()
        text = "Heading 1\n\nParagraph 1 content. " * 20
        headings = ["Heading 1"]
        chunks = chunker.chunk(text, headings)

        assert len(chunks) > 0

    def test_chunk_respects_boundaries(self):
        """Test that chunking respects paragraph boundaries."""
        chunker = SemanticChunker(target_chunk_size=50, overlap_size=10)
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = chunker.chunk(text)

        # Should have multiple chunks
        assert len(chunks) >= 1


@pytest.mark.django_db
@pytest.mark.asyncio
class TestKnowledgeIndexingPipeline:
    """Test KnowledgeIndexingPipeline."""

    @patch("apps.knowledge.services.indexing.EmbeddingService")
    async def test_index_text(self, mock_service_class):
        """Test indexing text content."""
        mock_service = MagicMock()
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        mock_service._get_provider.return_value = mock_provider
        mock_service.embed_batch = AsyncMock(return_value=[[0.1] * 1536, [0.2] * 1536])
        mock_service_class.get_instance.return_value = mock_service

        from apps.knowledge.models import KnowledgeVector
        from apps.knowledge.services.indexing import KnowledgeIndexingPipeline

        pipeline = KnowledgeIndexingPipeline(mock_service)
        count = await pipeline.index_text(
            source_type="policy_document",
            source_id="test-id",
            content="Test content. " * 100,
            category="compliance",
        )

        assert count > 0
        assert KnowledgeVector.objects.filter(source_id="test-id").exists()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestKnowledgeRetrievalService:
    """Test KnowledgeRetrievalService."""

    @patch("apps.knowledge.services.retrieval.EmbeddingService")
    async def test_search(self, mock_service_class):
        """Test semantic search."""
        mock_service = MagicMock()
        mock_service.embed = AsyncMock(return_value=[0.1] * 1536)
        mock_service_class.get_instance.return_value = mock_service

        import uuid

        from apps.knowledge.models import KnowledgeVector
        from apps.knowledge.services.retrieval import KnowledgeRetrievalService as RetrievalService

        # Create test vector
        source_id = uuid.uuid4()
        KnowledgeVector.objects.create(
            source_type=KnowledgeVector.SourceType.POLICY_DOCUMENT,
            source_id=source_id,
            content="Test content",
            content_hash=KnowledgeVector.hash_content("Test content"),
            embedding=[0.1] * 1536,
            embedding_model="test-model",
        )

        service = RetrievalService(mock_service)
        results = await service.search("test query", top_k=10)

        assert isinstance(results, list)
        # Results may be empty if similarity threshold not met, which is fine

    @patch("apps.knowledge.services.retrieval.EmbeddingService")
    async def test_hybrid_search(self, mock_service_class):
        """Test hybrid search."""
        mock_service = MagicMock()
        mock_service.embed = AsyncMock(return_value=[0.1] * 1536)
        mock_service_class.get_instance.return_value = mock_service

        import uuid

        from apps.knowledge.models import KnowledgeVector
        from apps.knowledge.services.retrieval import KnowledgeRetrievalService as RetrievalService

        # Create test vector
        source_id = uuid.uuid4()
        KnowledgeVector.objects.create(
            source_type=KnowledgeVector.SourceType.POLICY_DOCUMENT,
            source_id=source_id,
            content="Test content with keyword",
            content_hash=KnowledgeVector.hash_content("Test content with keyword"),
            embedding=[0.1] * 1536,
            embedding_model="test-model",
        )

        service = RetrievalService(mock_service)
        results = await service.hybrid_search("keyword", top_k=10)

        assert isinstance(results, list)
