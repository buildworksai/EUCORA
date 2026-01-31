# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for KB & Triage Agent models.
"""
import pytest
from django.utils import timezone

from apps.kb_triage.models import (
    IncidentPattern,
    KnowledgeArticle,
    KnowledgeSource,
    ResolutionStep,
    TriageFeedback,
    TriageRequest,
    TriageSuggestion,
)


@pytest.mark.django_db
class TestKnowledgeSource:
    """Test KnowledgeSource model."""

    def test_create_source(self):
        """Test creating a knowledge source."""
        source = KnowledgeSource.objects.create(
            name="ServiceNow KB",
            source_type=KnowledgeSource.SourceType.SERVICENOW_KB,
            connection_config={"instance_url": "https://servicenow.example.com"},
        )
        assert source.name == "ServiceNow KB"
        assert source.source_type == "servicenow_kb"
        assert source.is_active is True


@pytest.mark.django_db
class TestKnowledgeArticle:
    """Test KnowledgeArticle model."""

    def test_create_article(self):
        """Test creating a knowledge article."""
        source = KnowledgeSource.objects.create(
            name="Test Source",
            source_type=KnowledgeSource.SourceType.CUSTOM,
        )
        article = KnowledgeArticle.objects.create(
            source=source,
            external_id="KB001",
            title="How to Reset Password",
            content="Step 1: Click forgot password...",
            category="User Support",
        )
        assert article.title == "How to Reset Password"
        assert article.external_id == "KB001"
        assert article.view_count == 0


@pytest.mark.django_db
class TestTriageRequest:
    """Test TriageRequest model."""

    def test_create_request(self):
        """Test creating a triage request."""
        request = TriageRequest.objects.create(
            servicenow_number="INC0012345",
            caller_name="John Doe",
            caller_email="john@example.com",
            short_description="Outlook not syncing",
            description="User reports Outlook emails not syncing to server",
            symptoms=["emails not syncing", "sync errors"],
        )
        assert request.servicenow_number == "INC0012345"
        assert request.status == TriageRequest.Status.PENDING
        assert request.correlation_id is not None


@pytest.mark.django_db
class TestTriageSuggestion:
    """Test TriageSuggestion model."""

    def test_create_suggestion(self):
        """Test creating a triage suggestion."""
        source = KnowledgeSource.objects.create(
            name="Test Source",
            source_type=KnowledgeSource.SourceType.CUSTOM,
        )
        article = KnowledgeArticle.objects.create(
            source=source,
            external_id="KB001",
            title="Test Article",
            content="Test content",
        )
        request = TriageRequest.objects.create(
            caller_name="Test User",
            short_description="Test issue",
            description="Test description",
        )
        suggestion = TriageSuggestion.objects.create(
            triage_request=request,
            suggestion_type=TriageSuggestion.SuggestionType.ARTICLE,
            title="Related KB Article",
            content="Try this solution...",
            source_article=article,
            relevance_score=0.95,
        )
        assert suggestion.relevance_score == 0.95
        assert suggestion.suggestion_type == "article"


@pytest.mark.django_db
class TestResolutionStep:
    """Test ResolutionStep model."""

    def test_create_step(self):
        """Test creating a resolution step."""
        request = TriageRequest.objects.create(
            caller_name="Test User",
            short_description="Test",
            description="Test",
        )
        step = ResolutionStep.objects.create(
            triage_request=request,
            step_number=1,
            instruction="Check network connectivity",
            expected_outcome="Network connection established",
        )
        assert step.step_number == 1
        assert step.status == ResolutionStep.Status.PENDING


@pytest.mark.django_db
class TestIncidentPattern:
    """Test IncidentPattern model."""

    def test_create_pattern(self):
        """Test creating an incident pattern."""
        pattern = IncidentPattern.objects.create(
            name="Outlook Sync Issues",
            pattern_type=IncidentPattern.PatternType.RECURRING,
            description="Multiple reports of Outlook sync issues",
            category="Email",
            occurrence_count=15,
            affected_users=12,
        )
        assert pattern.name == "Outlook Sync Issues"
        assert pattern.pattern_type == "recurring"
        assert pattern.status == IncidentPattern.Status.ACTIVE
        assert pattern.correlation_id is not None


@pytest.mark.django_db
class TestTriageFeedback:
    """Test TriageFeedback model."""

    def test_create_feedback(self):
        """Test creating triage feedback."""
        request = TriageRequest.objects.create(
            caller_name="Test User",
            short_description="Test",
            description="Test",
        )
        feedback = TriageFeedback.objects.create(
            triage_request=request,
            feedback_type=TriageFeedback.FeedbackType.CATEGORY,
            was_accurate=True,
            comments="Category was correct",
        )
        assert feedback.feedback_type == "category"
        assert feedback.was_accurate is True
