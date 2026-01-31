# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for Policy Documents API.
"""
from rest_framework import serializers

from apps.policy_documents.models import DocumentCategory, DocumentChunk, PolicyDocument


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for DocumentCategory model."""

    category_type_label = serializers.CharField(source="get_category_type_display", read_only=True)

    class Meta:
        model = DocumentCategory
        fields = [
            "id",
            "name",
            "category_type",
            "category_type_label",
            "description",
            "icon",
            "color",
            "is_system",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model."""

    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "document",
            "chunk_index",
            "content",
            "content_hash",
            "heading",
            "page_number",
            "start_char",
            "end_char",
            "embedding_model",
            "created_at",
        ]
        read_only_fields = ["id", "content_hash", "created_at"]


class PolicyDocumentSerializer(serializers.ModelSerializer):
    """Serializer for PolicyDocument model."""

    status_label = serializers.CharField(source="get_status_display", read_only=True)
    category = DocumentCategorySerializer(read_only=True)
    category_id = serializers.UUIDField(write_only=True, required=False)
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = PolicyDocument
        fields = [
            "id",
            "correlation_id",
            "title",
            "description",
            "category",
            "category_id",
            "tags",
            "file_name",
            "file_type",
            "file_size",
            "storage_path",
            "content_hash",
            "status",
            "status_label",
            "processing_error",
            "chunk_count",
            "version",
            "parent_document",
            "effective_date",
            "review_date",
            "author",
            "uploaded_by",
            "uploaded_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "storage_path",
            "content_hash",
            "status",
            "processing_error",
            "chunk_count",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Handle category assignment."""
        category_id = validated_data.pop("category_id", None)
        if category_id:
            validated_data["category"] = DocumentCategory.objects.get(id=category_id)
        return super().create(validated_data)


class PolicyDocumentDetailSerializer(PolicyDocumentSerializer):
    """Detailed serializer with chunks."""

    chunks = DocumentChunkSerializer(many=True, read_only=True)

    class Meta(PolicyDocumentSerializer.Meta):
        fields = PolicyDocumentSerializer.Meta.fields + ["chunks"]


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for search requests."""

    query = serializers.CharField(required=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    status = serializers.CharField(required=False)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)
    offset = serializers.IntegerField(default=0, min_value=0)


class SemanticSearchRequestSerializer(serializers.Serializer):
    """Serializer for semantic search requests."""

    query = serializers.CharField(required=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=100)
    min_similarity = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0)
