# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for Knowledge app.
"""
import uuid

import pytest

from apps.knowledge.models import EmbeddingConfig, KnowledgeVector


@pytest.mark.django_db
class TestEmbeddingConfig:
    """Test EmbeddingConfig model."""

    def test_create_embedding_config(self):
        """Test creating an embedding configuration."""
        config = EmbeddingConfig.objects.create(
            provider=EmbeddingConfig.Provider.OPENAI,
            model_name="text-embedding-3-small",
            dimensions=1536,
            api_key="test-key",
            is_active=True,
            is_default=False,
        )
        assert config.provider == EmbeddingConfig.Provider.OPENAI
        assert config.model_name == "text-embedding-3-small"
        assert config.dimensions == 1536
        assert config.is_active is True
        assert config.is_default is False

    def test_unique_default_embedding_config(self):
        """Test that only one config can be default."""
        EmbeddingConfig.objects.create(
            provider=EmbeddingConfig.Provider.OPENAI,
            model_name="text-embedding-3-small",
            dimensions=1536,
            is_default=True,
        )
        # Creating second default should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            EmbeddingConfig.objects.create(
                provider=EmbeddingConfig.Provider.COHERE,
                model_name="embed-english-v3.0",
                dimensions=1024,
                is_default=True,
            )

    def test_str_representation(self):
        """Test string representation."""
        config = EmbeddingConfig.objects.create(
            provider=EmbeddingConfig.Provider.OPENAI,
            model_name="text-embedding-3-small",
            dimensions=1536,
        )
        assert "OpenAI" in str(config)
        assert "text-embedding-3-small" in str(config)
        assert "1536D" in str(config)


@pytest.mark.django_db
class TestKnowledgeVector:
    """Test KnowledgeVector model."""

    def test_create_knowledge_vector(self):
        """Test creating a knowledge vector."""
        vector = KnowledgeVector.objects.create(
            source_type=KnowledgeVector.SourceType.POLICY_DOCUMENT,
            source_id=uuid.uuid4(),
            source_chunk_index=0,
            content="Test content",
            content_hash=KnowledgeVector.hash_content("Test content"),
            embedding=[0.1] * 1536,  # Mock embedding
            embedding_model="text-embedding-3-small",
            category="compliance",
        )
        assert vector.source_type == KnowledgeVector.SourceType.POLICY_DOCUMENT
        assert vector.content == "Test content"
        assert len(vector.embedding) == 1536
        assert vector.embedding_model == "text-embedding-3-small"

    def test_hash_content(self):
        """Test content hashing."""
        content = "Test content"
        hash1 = KnowledgeVector.hash_content(content)
        hash2 = KnowledgeVector.hash_content(content)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_str_representation(self):
        """Test string representation."""
        source_id = uuid.uuid4()
        vector = KnowledgeVector.objects.create(
            source_type=KnowledgeVector.SourceType.POLICY_DOCUMENT,
            source_id=source_id,
            source_chunk_index=5,
            content="Test content",
            content_hash=KnowledgeVector.hash_content("Test content"),
            embedding=[0.1] * 1536,
            embedding_model="text-embedding-3-small",
        )
        assert "Policy Document" in str(vector)
        assert "chunk 5" in str(vector)
