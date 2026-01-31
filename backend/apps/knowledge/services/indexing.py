# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Knowledge indexing pipeline.
"""
from typing import List, Optional

from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.models import KnowledgeVector
from apps.knowledge.services.chunking import SemanticChunker


class KnowledgeIndexingPipeline:
    """Pipeline for indexing content into vector storage."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        self.embedding_service = embedding_service
        self.chunker = SemanticChunker(chunk_size, chunk_overlap)

    async def index_text(
        self,
        source_type: str,
        source_id: str,
        content: str,
        category: str = "",
        tags: Optional[List[str]] = None,
        application_id: str = None,
        source_created_at=None,
    ) -> int:
        """Index text content."""
        # Chunk content
        chunks = self.chunker.chunk(content)

        # Generate embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed_batch(chunk_texts)

        # Store vectors
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vectors.append(
                KnowledgeVector(
                    source_type=source_type,
                    source_id=source_id,
                    source_chunk_index=i,
                    content=chunk.content,
                    content_hash=KnowledgeVector.hash_content(chunk.content),
                    embedding=embedding,
                    embedding_model=self.embedding_service._get_provider().model_name,
                    category=category,
                    tags=tags or [],
                    application_id=application_id,
                    source_created_at=source_created_at,
                )
            )

        KnowledgeVector.objects.bulk_create(vectors)
        return len(vectors)
