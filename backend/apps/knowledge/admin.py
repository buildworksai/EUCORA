# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin for Knowledge models.
"""
from django.contrib import admin

from apps.knowledge.models import EmbeddingConfig, KnowledgeVector


@admin.register(EmbeddingConfig)
class EmbeddingConfigAdmin(admin.ModelAdmin):
    """Admin for EmbeddingConfig."""

    list_display = ["provider", "model_name", "dimensions", "is_active", "is_default", "created_at"]
    list_filter = ["provider", "is_active", "is_default"]
    search_fields = ["model_name", "provider"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(KnowledgeVector)
class KnowledgeVectorAdmin(admin.ModelAdmin):
    """Admin for KnowledgeVector."""

    list_display = [
        "source_type",
        "source_id",
        "source_chunk_index",
        "category",
        "embedding_model",
        "created_at",
    ]
    list_filter = ["source_type", "category", "embedding_model"]
    search_fields = ["content", "source_id"]
    readonly_fields = ["id", "correlation_id", "content_hash", "created_at", "updated_at"]
