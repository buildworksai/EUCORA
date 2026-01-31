# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Document processing pipeline.
"""
from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.services.indexing import KnowledgeIndexingPipeline
from apps.policy_documents.models import DocumentChunk, PolicyDocument
from apps.policy_documents.services.chunking import SemanticChunker
from apps.policy_documents.services.extraction import DocumentExtractor
from apps.storage.services import get_storage_service


class DocumentProcessingPipeline:
    """Pipeline for processing uploaded documents."""

    def __init__(self):
        self.extractor = DocumentExtractor()
        self.chunker = SemanticChunker()
        self.embedding_service = EmbeddingService.get_instance()
        self.indexing_pipeline = KnowledgeIndexingPipeline(self.embedding_service)

    def process_document(self, document: PolicyDocument) -> int:
        """Process a document: extract, chunk, embed, store."""
        try:
            # Update status
            document.status = PolicyDocument.DocumentStatus.PROCESSING
            document.save(update_fields=["status"])

            # Download file from storage
            storage_service = get_storage_service()
            # Storage service download returns bytes directly
            file_content = storage_service.download(document.storage_path)

            # Extract text
            text, headings = self.extractor.extract_text(file_content, document.file_type)

            # Chunk content
            chunks = self.chunker.chunk(text, headings)

            # Generate embeddings and store chunks
            import asyncio

            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = asyncio.run(self.embedding_service.embed_batch(chunk_texts))

            # Create DocumentChunk records
            document_chunks = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                document_chunks.append(
                    DocumentChunk(
                        document=document,
                        chunk_index=i,
                        content=chunk.content,
                        content_hash=PolicyDocument.hash_content(chunk.content.encode()),
                        heading=chunk.heading or "",
                        start_char=chunk.start_char,
                        end_char=chunk.end_char,
                        embedding=embedding,
                        embedding_model=self.embedding_service._get_provider().model_name,
                    )
                )

            DocumentChunk.objects.bulk_create(document_chunks)

            # Index in knowledge vectors
            import asyncio

            asyncio.run(
                self.indexing_pipeline.index_text(
                    source_type="policy_document",
                    source_id=str(document.id),
                    content=text,
                    category=document.category.category_type,
                    tags=document.tags,
                    source_created_at=document.created_at,
                )
            )

            # Update document status
            document.status = PolicyDocument.DocumentStatus.ACTIVE
            document.chunk_count = len(chunks)
            document.save(update_fields=["status", "chunk_count"])

            return len(chunks)
        except Exception as e:
            document.status = PolicyDocument.DocumentStatus.FAILED
            document.processing_error = str(e)
            document.save(update_fields=["status", "processing_error"])
            raise
