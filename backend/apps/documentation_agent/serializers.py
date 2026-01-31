# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for Documentation Agent API.
"""
from rest_framework import serializers

from .models import CodeAnalysis, CodeRepository, DocumentationTemplate, DocumentedModule, GeneratedDocument


class CodeRepositorySerializer(serializers.ModelSerializer):
    """Serializer for code repositories."""

    analysis_count = serializers.SerializerMethodField()

    class Meta:
        model = CodeRepository
        fields = [
            "id",
            "name",
            "repo_type",
            "url",
            "local_path",
            "default_branch",
            "auth_config",
            "last_analyzed",
            "is_active",
            "analysis_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_analyzed", "created_at", "updated_at"]

    def get_analysis_count(self, obj: CodeRepository) -> int:
        """Get count of analyses for this repository."""
        return obj.analyses.count()

    def to_representation(self, instance: CodeRepository) -> dict:
        """Mask sensitive auth config in response."""
        data = super().to_representation(instance)
        if data.get("auth_config"):
            data["auth_config"] = {k: "***" for k in data["auth_config"].keys()}
        return data


class CodeRepositoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating code repositories."""

    class Meta:
        model = CodeRepository
        fields = [
            "name",
            "repo_type",
            "url",
            "local_path",
            "default_branch",
            "auth_config",
            "is_active",
        ]


class DocumentedModuleSerializer(serializers.ModelSerializer):
    """Serializer for documented modules."""

    class Meta:
        model = DocumentedModule
        fields = [
            "id",
            "analysis",
            "module_path",
            "module_type",
            "name",
            "docstring",
            "generated_doc",
            "signature",
            "dependencies",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CodeAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for code analyses."""

    repository_name = serializers.CharField(source="repository.name", read_only=True)
    module_count = serializers.SerializerMethodField()
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = CodeAnalysis
        fields = [
            "id",
            "correlation_id",
            "repository",
            "repository_name",
            "commit_sha",
            "branch",
            "status",
            "started_at",
            "completed_at",
            "summary",
            "errors",
            "module_count",
            "document_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def get_module_count(self, obj: CodeAnalysis) -> int:
        """Get count of documented modules."""
        return obj.modules.count()

    def get_document_count(self, obj: CodeAnalysis) -> int:
        """Get count of generated documents."""
        return obj.documents.count()


class CodeAnalysisStartSerializer(serializers.Serializer):
    """Serializer for starting a code analysis."""

    branch = serializers.CharField(max_length=100, required=False, default="main")
    commit_sha = serializers.CharField(max_length=40, required=False, allow_blank=True)


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    """Serializer for generated documents."""

    analysis_repository = serializers.CharField(source="analysis.repository.name", read_only=True)
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)

    class Meta:
        model = GeneratedDocument
        fields = [
            "id",
            "correlation_id",
            "analysis",
            "analysis_repository",
            "doc_type",
            "title",
            "content",
            "format",
            "target_path",
            "status",
            "reviewed_by",
            "reviewed_by_username",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "reviewed_by",
            "published_at",
            "created_at",
            "updated_at",
        ]


class GeneratedDocumentPublishSerializer(serializers.Serializer):
    """Serializer for publishing a document."""

    target_path = serializers.CharField(max_length=500, required=False)


class DocumentationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for documentation templates."""

    class Meta:
        model = DocumentationTemplate
        fields = [
            "id",
            "name",
            "doc_type",
            "template_content",
            "variables",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GenerateDocumentSerializer(serializers.Serializer):
    """Serializer for generating documentation."""

    doc_type = serializers.ChoiceField(choices=GeneratedDocument.DocType.choices)
    template_id = serializers.UUIDField(required=False)
    target_path = serializers.CharField(max_length=500, required=False)
