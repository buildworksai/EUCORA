# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for Knowledge API.
"""
from rest_framework import serializers

from apps.knowledge.models import EmbeddingConfig, KnowledgeVector


class EmbeddingConfigSerializer(serializers.ModelSerializer):
    """Serializer for EmbeddingConfig model."""

    provider_label = serializers.CharField(source="get_provider_display", read_only=True)

    class Meta:
        model = EmbeddingConfig
        fields = [
            "id",
            "provider",
            "provider_label",
            "model_name",
            "dimensions",
            "api_key",
            "api_endpoint",
            "is_active",
            "is_default",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate that only one default config exists."""
        if data.get("is_default"):
            existing_default = EmbeddingConfig.objects.filter(is_default=True).exclude(
                id=self.instance.id if self.instance else None
            )
            if existing_default.exists():
                raise serializers.ValidationError("Only one default embedding config is allowed.")
        return data


class KnowledgeVectorSerializer(serializers.ModelSerializer):
    """Serializer for KnowledgeVector model."""

    source_type_label = serializers.CharField(source="get_source_type_display", read_only=True)

    class Meta:
        model = KnowledgeVector
        fields = [
            "id",
            "correlation_id",
            "source_type",
            "source_type_label",
            "source_id",
            "source_chunk_index",
            "content",
            "content_hash",
            "embedding_model",
            "category",
            "tags",
            "application",
            "source_created_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "content_hash",
            "created_at",
            "updated_at",
        ]


class SearchRequestSerializer(serializers.Serializer):
    """Serializer for search requests."""

    query = serializers.CharField(required=True)
    source_types = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    categories = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    application_id = serializers.UUIDField(required=False, allow_null=True)
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=100)
    min_similarity = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0)


class RetrievedKnowledgeSerializer(serializers.Serializer):
    """Serializer for retrieved knowledge."""

    id = serializers.UUIDField()
    content = serializers.CharField()
    source_type = serializers.CharField()
    source_id = serializers.UUIDField()
    similarity = serializers.FloatField()
    category = serializers.CharField()
    metadata = serializers.DictField()


class IndexRequestSerializer(serializers.Serializer):
    """Serializer for indexing requests."""

    source_type = serializers.CharField(required=True)
    source_id = serializers.UUIDField(required=True)
    content = serializers.CharField(required=True)
    category = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    application_id = serializers.UUIDField(required=False, allow_null=True)


class StatsSerializer(serializers.Serializer):
    """Serializer for knowledge index statistics."""

    total_vectors = serializers.IntegerField()
    policy_documents = serializers.IntegerField()
    deployments = serializers.IntegerField()
    last_indexed = serializers.DateTimeField(allow_null=True)
