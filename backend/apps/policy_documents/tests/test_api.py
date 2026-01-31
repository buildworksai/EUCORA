# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for Policy Documents endpoints.
"""
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.policy_documents.models import DocumentCategory, PolicyDocument

User = get_user_model()


@pytest.mark.django_db
class TestPolicyDocumentsAPI:
    """Test Policy Documents API endpoints."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Create authenticated API client."""
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def category(self):
        """Create test category."""
        return DocumentCategory.objects.create(
            name="Test Category",
            category_type=DocumentCategory.CategoryType.COMPLIANCE,
        )

    def test_list_categories(self, authenticated_client, category):
        """Test listing document categories."""
        response = authenticated_client.get("/api/v1/policy-documents/categories/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_create_category(self, authenticated_client):
        """Test creating a document category."""
        data = {
            "name": "New Category",
            "category_type": "compliance",
            "description": "Test description",
        }
        response = authenticated_client.post("/api/v1/policy-documents/categories/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "New Category"

    def test_list_documents(self, authenticated_client, category):
        """Test listing policy documents."""
        PolicyDocument.objects.create(
            title="Test Document",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )

        response = authenticated_client.get("/api/v1/policy-documents/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    @patch("apps.policy_documents.views.get_storage_service")
    @patch("apps.policy_documents.views.process_document_task")
    def test_upload_document(self, mock_task, mock_storage_service, authenticated_client, category):
        """Test uploading a document."""
        # Mock storage service
        mock_storage = MagicMock()
        mock_result = MagicMock()
        mock_result.path = "policy-documents/test.pdf"
        mock_storage.upload.return_value = mock_result
        mock_storage_service.return_value = mock_storage

        # Create test file
        test_file = BytesIO(b"Test PDF content")
        test_file.name = "test.pdf"

        data = {
            "files": [test_file],
            "category_id": str(category.id),
        }

        response = authenticated_client.post("/api/v1/policy-documents/upload/", data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert "documents" in response.data

    def test_get_document_detail(self, authenticated_client, category):
        """Test getting document details."""
        document = PolicyDocument.objects.create(
            title="Test Document",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )

        response = authenticated_client.get(f"/api/v1/policy-documents/{document.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Test Document"

    @patch("apps.policy_documents.views.get_storage_service")
    def test_download_document(self, mock_storage_service, authenticated_client, category):
        """Test downloading a document."""
        document = PolicyDocument.objects.create(
            title="Test Document",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )

        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.download.return_value = b"PDF content"
        mock_storage_service.return_value = mock_storage

        response = authenticated_client.get(f"/api/v1/policy-documents/{document.id}/download/")
        assert response.status_code == status.HTTP_200_OK

    @patch("apps.policy_documents.views.reindex_document_task")
    def test_reprocess_document(self, mock_task, authenticated_client, category):
        """Test reprocessing a document."""
        document = PolicyDocument.objects.create(
            title="Test Document",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )

        response = authenticated_client.post(f"/api/v1/policy-documents/{document.id}/reprocess/")
        assert response.status_code == status.HTTP_200_OK
        mock_task.delay.assert_called_once()

    def test_search_documents(self, authenticated_client, category):
        """Test searching documents."""
        PolicyDocument.objects.create(
            title="Test Document",
            description="Test description",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )

        data = {
            "query": "Test",
            "limit": 20,
            "offset": 0,
        }
        response = authenticated_client.post("/api/v1/policy-documents/search/", data)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data

    @patch("apps.policy_documents.views.PolicyContextRetriever")
    def test_semantic_search(self, mock_retriever_class, authenticated_client, category):
        """Test semantic search."""
        from apps.policy_documents.services.rag import RetrievedChunk

        mock_retriever = MagicMock()
        mock_chunk = RetrievedChunk(
            id="1",
            content="Test content",
            document_id="doc-1",
            document_title="Test Document",
            category="compliance",
            similarity=0.9,
        )
        mock_retriever.get_context.return_value = [mock_chunk]
        mock_retriever_class.return_value = mock_retriever

        data = {
            "query": "test query",
            "top_k": 10,
            "min_similarity": 0.7,
        }
        response = authenticated_client.post("/api/v1/policy-documents/semantic_search/", data)
        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
