# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for Knowledge.
"""
from django.db.models import Count, Max, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.models import EmbeddingConfig, KnowledgeVector
from apps.knowledge.serializers import (
    EmbeddingConfigSerializer,
    IndexRequestSerializer,
    RetrievedKnowledgeSerializer,
    SearchRequestSerializer,
    StatsSerializer,
)
from apps.knowledge.services.indexing import KnowledgeIndexingPipeline
from apps.knowledge.services.retrieval import KnowledgeRetrievalService
from apps.rbac.permissions import RBACPermission


class EmbeddingConfigViewSet(viewsets.ModelViewSet):
    """API viewset for EmbeddingConfig."""

    permission_classes = [RBACPermission("knowledge_config", "read")]
    queryset = EmbeddingConfig.objects.all()
    serializer_class = EmbeddingConfigSerializer
    lookup_field = "id"

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [RBACPermission("knowledge_config", "create")()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def test(self, request: Request, pk=None) -> Response:
        """Test embedding provider connection."""
        import asyncio

        config = self.get_object()
        test_text = request.data.get("test_text", "This is a test sentence.")

        try:
            service = EmbeddingService.get_instance()
            provider = service._create_provider(config)
            embedding = asyncio.run(provider.embed(test_text))

            return Response(
                {
                    "success": True,
                    "message": "Embedding generated successfully",
                    "dimensions": len(embedding),
                }
            )
        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class KnowledgeSearchViewSet(viewsets.ViewSet):
    """API viewset for knowledge search."""

    permission_classes = [RBACPermission("knowledge_search", "read")]

    @action(detail=False, methods=["post"])
    def search(self, request: Request) -> Response:
        """Semantic search."""
        import asyncio

        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = EmbeddingService.get_instance()
        retrieval_service = KnowledgeRetrievalService(service)

        results = asyncio.run(retrieval_service.search(**serializer.validated_data))

        result_serializer = RetrievedKnowledgeSerializer(results, many=True)
        return Response(result_serializer.data)

    @action(detail=False, methods=["post"])
    def hybrid(self, request: Request) -> Response:
        """Hybrid search (vector + keyword)."""
        import asyncio

        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = EmbeddingService.get_instance()
        retrieval_service = KnowledgeRetrievalService(service)

        results = asyncio.run(retrieval_service.hybrid_search(**serializer.validated_data))

        result_serializer = RetrievedKnowledgeSerializer(results, many=True)
        return Response(result_serializer.data)

    @action(detail=False, methods=["post"])
    def index(self, request: Request) -> Response:
        """Index content."""
        import asyncio

        serializer = IndexRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = EmbeddingService.get_instance()
        pipeline = KnowledgeIndexingPipeline(service)

        count = asyncio.run(pipeline.index_text(**serializer.validated_data))

        return Response({"success": True, "chunks_indexed": count})

    @action(detail=False, methods=["get"])
    def stats(self, request: Request) -> Response:
        """Get index statistics."""
        stats = KnowledgeVector.objects.aggregate(
            total_vectors=Count("id"),
            policy_documents=Count("id", filter=Q(source_type="policy_document")),
            deployments=Count("id", filter=Q(source_type="deployment")),
            last_indexed=Max("created_at"),
        )

        serializer = StatsSerializer(stats)
        return Response(serializer.data)
