# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Knowledge retrieval service for semantic search.
"""
from dataclasses import dataclass
from typing import List, Optional

from pgvector.django import CosineDistance

from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.models import KnowledgeVector


@dataclass
class RetrievedKnowledge:
    """Retrieved knowledge with metadata."""

    id: str
    content: str
    source_type: str
    source_id: str
    similarity: float
    category: str
    metadata: dict


class KnowledgeRetrievalService:
    """Service for semantic knowledge retrieval."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        source_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        application_id: Optional[str] = None,
        top_k: int = 10,
        min_similarity: float = 0.7,
    ) -> List[RetrievedKnowledge]:
        """Semantic search for relevant knowledge."""
        # Generate query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Build query
        qs = KnowledgeVector.objects.all()

        if source_types:
            qs = qs.filter(source_type__in=source_types)
        if categories:
            qs = qs.filter(category__in=categories)
        if application_id:
            qs = qs.filter(application_id=application_id)

        # Vector similarity search
        results = (
            qs.annotate(similarity=1 - CosineDistance("embedding", query_embedding))
            .filter(similarity__gte=min_similarity)
            .order_by("-similarity")[:top_k]
        )

        # Format results
        return [
            RetrievedKnowledge(
                id=str(r.id),
                content=r.content,
                source_type=r.source_type,
                source_id=str(r.source_id),
                similarity=float(r.similarity),
                category=r.category,
                metadata={
                    "source_created_at": r.source_created_at.isoformat() if r.source_created_at else None,
                    "tags": r.tags,
                },
            )
            for r in results
        ]

    async def hybrid_search(
        self,
        query: str,
        keyword_weight: float = 0.3,
        **kwargs,
    ) -> List[RetrievedKnowledge]:
        """Combined vector + keyword search."""
        # Vector search
        vector_results = await self.search(query, **kwargs)

        # Keyword search
        top_k = kwargs.get("top_k", 10)
        keyword_results = KnowledgeVector.objects.filter(content__icontains=query)[:top_k]

        # Combine and rerank (simple merge - can be enhanced with proper reranking)
        combined = list(vector_results)
        seen_ids = {r.id for r in vector_results}

        for r in keyword_results:
            if str(r.id) not in seen_ids:
                combined.append(
                    RetrievedKnowledge(
                        id=str(r.id),
                        content=r.content,
                        source_type=r.source_type,
                        source_id=str(r.source_id),
                        similarity=keyword_weight,  # Lower weight for keyword matches
                        category=r.category,
                        metadata={
                            "source_created_at": r.source_created_at.isoformat() if r.source_created_at else None,
                            "tags": r.tags,
                        },
                    )
                )

        # Sort by similarity
        combined.sort(key=lambda x: x.similarity, reverse=True)
        return combined[:top_k]
