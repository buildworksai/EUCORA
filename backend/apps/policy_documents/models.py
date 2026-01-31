# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Documents models for document management and RAG.
"""
import hashlib
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from pgvector.django import VectorField

from apps.core.models import CorrelationIdModel, TimeStampedModel

User = get_user_model()


class DocumentCategory(TimeStampedModel):
    """Policy document categories."""

    class CategoryType(models.TextChoices):
        COMPLIANCE = "compliance", "Compliance Policies"
        SECURITY = "security", "Security Policies"
        OPERATIONAL = "operational", "Operational Policies"
        GOVERNANCE = "governance", "Governance Policies"
        APPLICATION = "application", "Application Policies"
        CUSTOM = "custom", "Custom Category"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128, unique=True)
    category_type = models.CharField(max_length=32, choices=CategoryType.choices)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=64, blank=True)  # Lucide icon name
    color = models.CharField(max_length=32, blank=True)  # Tailwind color class
    is_system = models.BooleanField(default=False)  # Cannot be deleted
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Document Category"
        verbose_name_plural = "Document Categories"
        ordering = ["category_type", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class PolicyDocument(TimeStampedModel, CorrelationIdModel):
    """Uploaded policy documents for RAG."""

    class DocumentStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROCESSING = "processing", "Processing"
        ACTIVE = "active", "Active"
        DEPRECATED = "deprecated", "Deprecated"
        ARCHIVED = "archived", "Archived"
        FAILED = "failed", "Processing Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Metadata
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT)
    tags = models.JSONField(default=list)

    # File storage
    file_name = models.CharField(max_length=256)
    file_type = models.CharField(max_length=32)  # pdf, docx, html, txt, md
    file_size = models.BigIntegerField()
    storage_path = models.CharField(max_length=512)  # Path in object storage
    content_hash = models.CharField(max_length=64, db_index=True)  # SHA-256

    # Processing status
    status = models.CharField(max_length=32, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    processing_error = models.TextField(blank=True)
    chunk_count = models.IntegerField(default=0)

    # Versioning
    version = models.IntegerField(default=1)
    parent_document = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="versions"
    )

    # Governance
    effective_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    author = models.CharField(max_length=256, blank=True)

    # Audit
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["content_hash"]),
        ]
        verbose_name = "Policy Document"
        verbose_name_plural = "Policy Documents"

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @staticmethod
    def hash_content(content: bytes) -> str:
        """Generate SHA-256 hash for content deduplication."""
        return hashlib.sha256(content).hexdigest()


class DocumentChunk(TimeStampedModel):
    """Chunked document content for vector storage."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE, related_name="chunks")

    # Chunk content
    chunk_index = models.IntegerField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64)

    # Metadata for retrieval
    heading = models.CharField(max_length=256, blank=True)  # Section heading if available
    page_number = models.IntegerField(null=True, blank=True)
    start_char = models.IntegerField()
    end_char = models.IntegerField()

    # Vector embedding (stored in pgvector)
    embedding = VectorField(dimensions=1536, null=True)  # OpenAI ada-002 dimensions
    embedding_model = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"

    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"
