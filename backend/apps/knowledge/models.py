# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Knowledge models for vector storage and semantic search.
"""
import hashlib
import uuid

from django.db import models
from pgvector.django import HnswIndex, VectorField

from apps.core.encryption import EncryptedCharField
from apps.core.models import CorrelationIdModel, TimeStampedModel


class EmbeddingConfig(TimeStampedModel):
    """Configuration for embedding providers."""

    class Provider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        COHERE = "cohere", "Cohere"
        LOCAL = "local", "Local (Sentence Transformers)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    provider = models.CharField(max_length=32, choices=Provider.choices)
    model_name = models.CharField(max_length=128)
    dimensions = models.IntegerField()

    # API Configuration
    api_key = EncryptedCharField(max_length=512, blank=True)
    api_endpoint = models.URLField(blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Embedding Configuration"
        verbose_name_plural = "Embedding Configurations"
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="unique_default_embedding_config",
            )
        ]

    def __str__(self):
        return f"{self.get_provider_display()} - {self.model_name} ({self.dimensions}D)"


class KnowledgeVector(TimeStampedModel, CorrelationIdModel):
    """Vector embeddings for knowledge retrieval."""

    class SourceType(models.TextChoices):
        POLICY_DOCUMENT = "policy_document", "Policy Document"
        DEPLOYMENT = "deployment", "Deployment Record"
        CAB_DECISION = "cab_decision", "CAB Decision"
        INCIDENT = "incident", "Incident Report"
        RUNBOOK = "runbook", "Operational Runbook"
        APPLICATION = "application", "Application Metadata"
        VULNERABILITY = "vulnerability", "Vulnerability Record"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Source
    source_type = models.CharField(max_length=64, choices=SourceType.choices)
    source_id = models.UUIDField()
    source_chunk_index = models.IntegerField(default=0)

    # Content
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)

    # Vector
    embedding = VectorField(dimensions=1536)  # Default OpenAI dimensions
    embedding_model = models.CharField(max_length=64)

    # Metadata
    category = models.CharField(max_length=64, blank=True)
    tags = models.JSONField(default=list)
    application = models.ForeignKey(
        "application_portfolio.Application", on_delete=models.SET_NULL, null=True, blank=True
    )

    # Audit
    source_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            HnswIndex(
                name="knowledge_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["source_type", "source_id"]),
            models.Index(fields=["category"]),
            models.Index(fields=["application"]),
        ]
        verbose_name = "Knowledge Vector"
        verbose_name_plural = "Knowledge Vectors"

    def __str__(self):
        return f"{self.get_source_type_display()} - {self.source_id} (chunk {self.source_chunk_index})"

    @staticmethod
    def hash_content(content: str) -> str:
        """Generate SHA-256 hash for content deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()
