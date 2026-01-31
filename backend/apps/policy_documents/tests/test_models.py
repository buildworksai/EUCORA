# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for Policy Documents app.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.policy_documents.models import DocumentCategory, DocumentChunk, PolicyDocument

User = get_user_model()


@pytest.mark.django_db
class TestDocumentCategory:
    """Test DocumentCategory model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

    def test_create_category(self, user):
        """Test creating a document category."""
        category = DocumentCategory.objects.create(
            name="Compliance Policies",
            category_type=DocumentCategory.CategoryType.COMPLIANCE,
            description="Compliance-related policies",
            created_by=user,
        )
        assert category.name == "Compliance Policies"
        assert category.category_type == DocumentCategory.CategoryType.COMPLIANCE
        assert category.is_system is False

    def test_unique_name(self):
        """Test that category names must be unique."""
        DocumentCategory.objects.create(
            name="Test Category",
            category_type=DocumentCategory.CategoryType.CUSTOM,
        )
        # Creating second with same name should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            DocumentCategory.objects.create(
                name="Test Category",
                category_type=DocumentCategory.CategoryType.CUSTOM,
            )

    def test_str_representation(self):
        """Test string representation."""
        category = DocumentCategory.objects.create(
            name="Security Policies",
            category_type=DocumentCategory.CategoryType.SECURITY,
        )
        assert "Security Policies" in str(category)
        assert "Security Policies" in str(category)


@pytest.mark.django_db
class TestPolicyDocument:
    """Test PolicyDocument model."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

    @pytest.fixture
    def category(self):
        """Create test category."""
        return DocumentCategory.objects.create(
            name="Test Category",
            category_type=DocumentCategory.CategoryType.COMPLIANCE,
        )

    def test_create_policy_document(self, user, category):
        """Test creating a policy document."""
        document = PolicyDocument.objects.create(
            title="Test Policy",
            description="Test description",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test content"),
            uploaded_by=user,
            status=PolicyDocument.DocumentStatus.DRAFT,
        )
        assert document.title == "Test Policy"
        assert document.category == category
        assert document.status == PolicyDocument.DocumentStatus.DRAFT
        assert document.correlation_id is not None

    def test_hash_content(self):
        """Test content hashing."""
        content = b"test content"
        hash1 = PolicyDocument.hash_content(content)
        hash2 = PolicyDocument.hash_content(content)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_str_representation(self, category):
        """Test string representation."""
        document = PolicyDocument.objects.create(
            title="Test Policy",
            category=category,
            file_name="test.pdf",
            file_type="pdf",
            file_size=1024,
            storage_path="policy-documents/test.pdf",
            content_hash=PolicyDocument.hash_content(b"test"),
            status=PolicyDocument.DocumentStatus.ACTIVE,
        )
        assert "Test Policy" in str(document)
        assert "Active" in str(document)


@pytest.mark.django_db
class TestDocumentChunk:
    """Test DocumentChunk model."""

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

    def test_create_document_chunk(self, document):
        """Test creating a document chunk."""
        chunk = DocumentChunk.objects.create(
            document=document,
            chunk_index=0,
            content="Test chunk content",
            content_hash=PolicyDocument.hash_content(b"Test chunk content"),
            start_char=0,
            end_char=20,
            embedding=[0.1] * 1536,
            embedding_model="text-embedding-3-small",
        )
        assert chunk.document == document
        assert chunk.chunk_index == 0
        assert chunk.content == "Test chunk content"
        assert len(chunk.embedding) == 1536

    def test_str_representation(self, document):
        """Test string representation."""
        chunk = DocumentChunk.objects.create(
            document=document,
            chunk_index=5,
            content="Test content",
            content_hash=PolicyDocument.hash_content(b"Test content"),
            start_char=0,
            end_char=12,
        )
        assert document.title in str(chunk)
        assert "Chunk 5" in str(chunk)
