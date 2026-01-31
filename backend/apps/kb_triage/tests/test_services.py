# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for KB & Triage Agent.
"""
import pytest

from apps.kb_triage.models import KnowledgeSource, TriageRequest


@pytest.mark.django_db
class TestKnowledgeSourceService:
    """Test knowledge source service."""

    def test_knowledge_source_creation(self):
        """Test creating knowledge source."""
        source = KnowledgeSource.objects.create(
            name="ServiceNow KB",
            source_type=KnowledgeSource.SourceType.SERVICENOW_KB,
            connection_config={"instance_url": "https://servicenow.example.com"},
        )
        assert source.name == "ServiceNow KB"
        assert source.is_active is True


@pytest.mark.django_db
class TestTriageService:
    """Test triage service."""

    def test_triage_request_creation(self):
        """Test creating triage request."""
        request = TriageRequest.objects.create(
            caller_name="John Doe",
            short_description="Outlook not syncing",
            description="User reports Outlook emails not syncing",
        )
        assert request.caller_name == "John Doe"
        assert request.status == TriageRequest.Status.PENDING
