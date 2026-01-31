# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin configuration for Documentation Agent.
"""
from django.contrib import admin

from .models import CodeAnalysis, CodeRepository, DocumentationTemplate, DocumentedModule, GeneratedDocument


@admin.register(CodeRepository)
class CodeRepositoryAdmin(admin.ModelAdmin):
    """Admin for code repositories."""

    list_display = ["name", "repo_type", "is_active", "last_analyzed", "created_at"]
    list_filter = ["repo_type", "is_active", "created_at"]
    search_fields = ["name", "url", "local_path"]
    readonly_fields = ["id", "created_at", "updated_at", "last_analyzed"]


@admin.register(CodeAnalysis)
class CodeAnalysisAdmin(admin.ModelAdmin):
    """Admin for code analyses."""

    list_display = [
        "repository",
        "branch",
        "status",
        "started_at",
        "completed_at",
        "correlation_id",
    ]
    list_filter = ["status", "branch", "started_at"]
    search_fields = ["repository__name", "commit_sha", "correlation_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at"]
    raw_id_fields = ["repository"]


@admin.register(DocumentedModule)
class DocumentedModuleAdmin(admin.ModelAdmin):
    """Admin for documented modules."""

    list_display = ["name", "module_type", "module_path", "analysis", "created_at"]
    list_filter = ["module_type", "created_at"]
    search_fields = ["name", "module_path"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["analysis"]


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    """Admin for generated documents."""

    list_display = [
        "title",
        "doc_type",
        "status",
        "analysis",
        "reviewed_by",
        "published_at",
        "correlation_id",
    ]
    list_filter = ["doc_type", "status", "format", "created_at"]
    search_fields = ["title", "correlation_id"]
    readonly_fields = ["id", "correlation_id", "created_at", "updated_at", "published_at"]
    raw_id_fields = ["analysis", "reviewed_by"]


@admin.register(DocumentationTemplate)
class DocumentationTemplateAdmin(admin.ModelAdmin):
    """Admin for documentation templates."""

    list_display = ["name", "doc_type", "is_active", "created_at"]
    list_filter = ["doc_type", "is_active", "created_at"]
    search_fields = ["name"]
    readonly_fields = ["id", "created_at", "updated_at"]
