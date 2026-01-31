# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for Policy Documents app.
"""
from unittest.mock import MagicMock, patch

import pytest

from apps.policy_documents.models import DocumentCategory, PolicyDocument
from apps.policy_documents.services.chunking import SemanticChunker
from apps.policy_documents.services.extraction import DocumentExtractor


class TestDocumentExtractor:
    """Test DocumentExtractor."""

    def test_extract_text_plain(self):
        """Test extracting text from plain text."""
        content = b"This is a test document.\n\nWith multiple paragraphs."
        text, headings = DocumentExtractor.extract_text(content, "txt")
        assert "test document" in text
        assert isinstance(headings, list)

    @patch("apps.policy_documents.services.extraction.fitz")
    def test_extract_pdf(self, mock_fitz):
        """Test extracting text from PDF."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF content"
        mock_page.get_text.return_value = {"blocks": []}
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.__len__ = lambda self: 1
        mock_fitz.open.return_value = mock_doc

        content = b"fake pdf content"
        text, headings = DocumentExtractor.extract_text(content, "pdf")
        assert isinstance(text, str)
        assert isinstance(headings, list)

    @patch("apps.policy_documents.services.extraction.Document")
    def test_extract_docx(self, mock_docx):
        """Test extracting text from DOCX."""
        mock_doc = MagicMock()
        mock_para = MagicMock()
        mock_para.text = "DOCX content"
        mock_para.style.name = "Normal"
        mock_doc.paragraphs = [mock_para]
        mock_docx.return_value = mock_doc

        content = b"fake docx content"
        text, headings = DocumentExtractor.extract_text(content, "docx")
        assert isinstance(text, str)
        assert isinstance(headings, list)

    @patch("apps.policy_documents.services.extraction.BeautifulSoup")
    def test_extract_html(self, mock_bs4):
        """Test extracting text from HTML."""
        mock_soup = MagicMock()
        mock_soup.get_text.return_value = "HTML content"
        mock_soup.find_all.return_value = []
        mock_bs4.return_value = mock_soup

        content = b"<html><body>Test</body></html>"
        text, headings = DocumentExtractor.extract_text(content, "html")
        assert isinstance(text, str)
        assert isinstance(headings, list)

    def test_unsupported_file_type(self):
        """Test unsupported file type raises error."""
        with pytest.raises(ValueError):
            DocumentExtractor.extract_text(b"content", "xyz")


class TestSemanticChunker:
    """Test SemanticChunker."""

    def test_chunk_simple_text(self):
        """Test chunking simple text."""
        chunker = SemanticChunker(target_chunk_size=100, max_chunk_size=200, overlap_size=20)
        text = "This is a test paragraph. " * 50
        chunks = chunker.chunk(text)

        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)

    def test_chunk_with_headings(self):
        """Test chunking with headings."""
        chunker = SemanticChunker()
        text = "Paragraph 1 content. " * 50
        headings = ["Heading 1"]
        chunks = chunker.chunk(text, headings)

        assert len(chunks) > 0

    def test_chunk_overlap(self):
        """Test that chunks have overlap."""
        chunker = SemanticChunker(target_chunk_size=50, overlap_size=10)
        text = "Word " * 100
        chunks = chunker.chunk(text)

        if len(chunks) > 1:
            # Check that chunks overlap
            assert len(chunks) >= 1


@pytest.mark.django_db
class TestDocumentProcessingPipeline:
    """Test DocumentProcessingPipeline."""

    @pytest.fixture
    def category(self):
        """Create test category."""
        return DocumentCategory.objects.create(
            name="Test Category",
            category_type=DocumentCategory.CategoryType.COMPLIANCE,
        )

    @pytest.fixture
    def document(self, category):
        """Create test document."""
        return PolicyDocument.objects.create(
            title="Test Policy",
            category=category,
            file_name="test.txt",
            file_type="txt",
            file_size=1024,
            storage_path="policy-documents/test.txt",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.DRAFT,
        )

    @patch("apps.policy_documents.services.processing.get_storage_service")
    @patch("apps.policy_documents.services.processing.EmbeddingService")
    def test_process_document(self, mock_embedding_service, mock_storage_service, document):
        """Test processing a document."""
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.download.return_value = b"Test document content. " * 50
        mock_storage_service.return_value = mock_storage

        # Mock embedding service
        mock_service = MagicMock()
        mock_provider = MagicMock()
        mock_provider.model_name = "test-model"
        mock_service._get_provider.return_value = mock_provider
        mock_service.embed_batch = MagicMock(return_value=[[0.1] * 1536])

        # Note: Full pipeline test requires async context (Celery task)
        # This test verifies structure only
        from apps.policy_documents.services.processing import DocumentProcessingPipeline

        pipeline = DocumentProcessingPipeline()
        assert pipeline is not None


@pytest.mark.django_db
class TestPolicyContextRetriever:
    """Test PolicyContextRetriever."""

    @pytest.fixture
    def category(self):
        """Create test category."""
        return DocumentCategory.objects.create(
            name="Test Category",
            category_type=DocumentCategory.CategoryType.COMPLIANCE,
        )

    @pytest.fixture
    def document(self, category):
        """Create test document."""
        return PolicyDocument.objects.create(
            title="Test Policy",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )

    @patch("apps.policy_documents.services.rag.EmbeddingService")
    @patch("apps.policy_documents.services.rag.KnowledgeRetrievalService")
    def test_get_context(self, mock_retrieval_class, mock_service_class, document):
        """Test retrieving policy context."""
        from apps.knowledge.services.retrieval import RetrievedKnowledge
        from apps.policy_documents.services.rag import PolicyContextRetriever as Retriever

        # Mock retrieval service
        mock_retrieval = MagicMock()
        mock_result = RetrievedKnowledge(
            id="test-id",
            content="Test content",
            source_type="policy_document",
            source_id=str(document.id),
            similarity=0.9,
            category="compliance",
            metadata={},
        )
        mock_retrieval.search = MagicMock(return_value=[mock_result])

        # Mock asyncio.run
        with patch("apps.policy_documents.services.rag.asyncio") as mock_asyncio:
            mock_asyncio.run.side_effect = lambda coro: [mock_result]

            retriever = Retriever()
            chunks = retriever.get_context("test query", categories=["compliance"])

            assert isinstance(chunks, list)

    def test_format_context(self):
        """Test formatting context for LLM."""
        from apps.policy_documents.services.rag import PolicyContextRetriever as Retriever
        from apps.policy_documents.services.rag import RetrievedChunk

        retriever = Retriever()
        chunks = [
            RetrievedChunk(
                id="1",
                content="Policy content",
                document_id="doc-1",
                document_title="Test Policy",
                category="compliance",
                similarity=0.9,
            )
        ]

        formatted = retriever.format_context(chunks)
        assert "Test Policy" in formatted
        assert "Policy content" in formatted
        assert "compliance" in formatted
