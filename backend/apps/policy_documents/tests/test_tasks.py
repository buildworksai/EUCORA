# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for Celery tasks.
"""
from unittest.mock import MagicMock, patch

import pytest

from apps.policy_documents.models import DocumentCategory, PolicyDocument
from apps.policy_documents.tasks import process_document_task, reindex_document_task


@pytest.mark.django_db
class TestDocumentTasks:
    """Test document processing tasks."""

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

    @patch("apps.policy_documents.tasks.DocumentProcessingPipeline")
    def test_process_document_task(self, mock_pipeline_class, document):
        """Test process_document_task."""
        mock_pipeline = MagicMock()
        mock_pipeline.process_document.return_value = 5
        mock_pipeline_class.return_value = mock_pipeline

        result = process_document_task(str(document.id))
        assert result == 5
        mock_pipeline.process_document.assert_called_once_with(document)

    @patch("apps.policy_documents.tasks.DocumentProcessingPipeline")
    def test_reindex_document_task(self, mock_pipeline_class, document):
        """Test reindex_document_task."""
        mock_pipeline = MagicMock()
        mock_pipeline.process_document.return_value = 3
        mock_pipeline_class.return_value = mock_pipeline

        result = reindex_document_task(str(document.id))
        assert result == 3
        # Should delete existing chunks first
        assert document.chunks.count() == 0
