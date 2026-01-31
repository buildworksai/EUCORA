# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for Documentation Agent.
"""
import pytest

from apps.documentation_agent.models import CodeAnalysis, CodeRepository, GeneratedDocument


@pytest.fixture
def repository():
    """Create a test repository."""
    return CodeRepository.objects.create(
        name="Test Repo",
        repo_type=CodeRepository.RepoType.LOCAL,
        local_path="/tmp/test",
    )


@pytest.mark.django_db
class TestCodeRepository:
    """Test CodeRepository model."""

    def test_create_repository(self):
        """Test repository creation."""
        repo = CodeRepository.objects.create(
            name="Test Repo",
            repo_type=CodeRepository.RepoType.GITHUB,
            url="https://github.com/test/repo",
        )
        assert repo.name == "Test Repo"
        assert repo.repo_type == CodeRepository.RepoType.GITHUB
        assert repo.is_active is True

    def test_repository_str(self, repository):
        """Test repository string representation."""
        assert str(repository) == "Test Repo (local)"


@pytest.mark.django_db
class TestCodeAnalysis:
    """Test CodeAnalysis model."""

    def test_create_analysis(self, repository):
        """Test analysis creation."""
        analysis = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.PENDING,
        )
        assert analysis.repository == repository
        assert analysis.branch == "main"
        assert analysis.status == CodeAnalysis.Status.PENDING
        assert analysis.correlation_id is not None

    def test_analysis_str(self, repository):
        """Test analysis string representation."""
        analysis = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.RUNNING,
        )
        assert "Test Repo" in str(analysis)
        assert "running" in str(analysis).lower()


@pytest.mark.django_db
class TestGeneratedDocument:
    """Test GeneratedDocument model."""

    def test_create_document(self, repository):
        """Test document creation."""
        analysis = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.COMPLETED,
        )
        document = GeneratedDocument.objects.create(
            analysis=analysis,
            doc_type=GeneratedDocument.DocType.README,
            title="Test README",
            content="# Test",
        )
        assert document.analysis == analysis
        assert document.doc_type == GeneratedDocument.DocType.README
        assert document.status == GeneratedDocument.DocStatus.DRAFT
        assert document.correlation_id is not None
