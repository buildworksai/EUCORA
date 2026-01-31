# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin for Policy Documents models.
"""
from django.contrib import admin

from apps.policy_documents.models import DocumentCategory, DocumentChunk, PolicyDocument


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """Admin for DocumentCategory."""

    list_display = ["name", "category_type", "is_system", "created_at"]
    list_filter = ["category_type", "is_system"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(admin.ModelAdmin):
    """Admin for PolicyDocument."""

    list_display = ["title", "category", "status", "file_type", "chunk_count", "created_at"]
    list_filter = ["status", "category", "file_type"]
    search_fields = ["title", "description", "file_name"]
    readonly_fields = [
        "id",
        "correlation_id",
        "storage_path",
        "content_hash",
        "chunk_count",
        "created_at",
        "updated_at",
    ]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    """Admin for DocumentChunk."""

    list_display = ["document", "chunk_index", "heading", "embedding_model", "created_at"]
    list_filter = ["embedding_model"]
    search_fields = ["content", "document__title"]
    readonly_fields = ["id", "content_hash", "created_at", "updated_at"]
