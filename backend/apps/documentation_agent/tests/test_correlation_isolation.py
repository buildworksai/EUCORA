# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for Documentation Agent.

MANDATORY: All models with CorrelationIdModel must have these tests.
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
class TestCorrelationIdIsolation:
    """Test correlation ID isolation."""

    def test_analysis_correlation_id_generated(self, repository):
        """Verify correlation_id is auto-generated for CodeAnalysis."""
        analysis = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.PENDING,
        )
        assert analysis.correlation_id is not None
        assert str(analysis.correlation_id) != ""

    def test_analysis_correlation_id_unique(self, repository):
        """Verify correlation_ids are unique."""
        analysis1 = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.PENDING,
        )
        analysis2 = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.PENDING,
        )
        assert analysis1.correlation_id != analysis2.correlation_id

    def test_document_correlation_id_generated(self, repository):
        """Verify correlation_id is auto-generated for GeneratedDocument."""
        analysis = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.COMPLETED,
        )
        document = GeneratedDocument.objects.create(
            analysis=analysis,
            doc_type=GeneratedDocument.DocType.README,
            title="Test",
            content="# Test",
        )
        assert document.correlation_id is not None

    def test_correlation_id_filtering(self, repository):
        """Verify filtering by correlation_id works."""
        analysis1 = CodeAnalysis.objects.create(
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.PENDING,
        )
        analysis2 = CodeAnalysis.objects.create(  # noqa: F841
            repository=repository,
            branch="main",
            status=CodeAnalysis.Status.PENDING,
        )

        filtered = CodeAnalysis.objects.filter(correlation_id=analysis1.correlation_id)
        assert filtered.count() == 1
        assert filtered.first() == analysis1
