# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
RAG context retriever for policy documents.
"""
from dataclasses import dataclass
from typing import List, Optional

from apps.core.async_utils import run_async
from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.services.retrieval import KnowledgeRetrievalService


@dataclass
class RetrievedChunk:
    """Retrieved document chunk with metadata."""

    id: str
    content: str
    document_id: str
    document_title: str
    category: str
    similarity: float
    heading: Optional[str] = None
    chunk_index: int = 0


class PolicyContextRetriever:
    """Retrieve relevant policy context for AI agent operations."""

    def __init__(self):
        embedding_service = EmbeddingService.get_instance()
        self.retrieval_service = KnowledgeRetrievalService(embedding_service)

    def get_context(
        self,
        query: str,
        categories: Optional[List[str]] = None,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ) -> List[RetrievedChunk]:
        """
        Retrieve most relevant policy chunks for a query.

        Returns:
            List of chunks with content, source document, and similarity score.
        """
        # Use knowledge retrieval service
        results = run_async(
            self.retrieval_service.search(
                query=query,
                source_types=["policy_document"],
                categories=categories,
                top_k=top_k,
                min_similarity=min_similarity,
            )
        )

        # Convert to RetrievedChunk format
        from apps.policy_documents.models import PolicyDocument

        retrieved_chunks = []
        for result in results:
            try:
                document = PolicyDocument.objects.get(id=result.source_id)
                retrieved_chunks.append(
                    RetrievedChunk(
                        id=result.id,
                        content=result.content,
                        document_id=str(document.id),
                        document_title=document.title,
                        category=result.category,
                        similarity=result.similarity,
                    )
                )
            except PolicyDocument.DoesNotExist:
                continue

        return retrieved_chunks

    def format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format chunks into context string for LLM prompt."""
        context_parts = []
        for chunk in chunks:
            context_parts.append(
                f"""
--- Policy: {chunk.document_title} ({chunk.category}) ---
{chunk.content}
---
"""
            )
        return "\n".join(context_parts)
