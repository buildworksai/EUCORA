# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for integration models.
"""
import pytest
from django.utils import timezone

from apps.integrations.models import ExternalSystem, IntegrationSyncLog


@pytest.mark.django_db
class TestExternalSystem:
    """Test ExternalSystem model."""

    def test_create_external_system(self):
        """Test creating an external system."""
        system = ExternalSystem.objects.create(
            name="Test ServiceNow",
            type=ExternalSystem.SystemType.SERVICENOW_CMDB,
            api_url="https://test.service-now.com",
            auth_type=ExternalSystem.AuthType.BASIC,
            credentials={"username": "test", "password": "test"},
        )

        assert system.name == "Test ServiceNow"
        assert system.type == ExternalSystem.SystemType.SERVICENOW_CMDB
        assert system.is_enabled is False
        assert system.correlation_id is not None

    def test_external_system_str(self):
        """Test ExternalSystem string representation."""
        system = ExternalSystem.objects.create(
            name="Test System",
            type=ExternalSystem.SystemType.ENTRA_ID,
            api_url="https://graph.microsoft.com",
            auth_type=ExternalSystem.AuthType.OAUTH2,
            credentials={},
        )

        assert "Test System" in str(system)
        assert "Microsoft Entra ID" in str(system)


@pytest.mark.django_db
class TestIntegrationSyncLog:
    """Test IntegrationSyncLog model."""

    def test_create_sync_log(self):
        """Test creating a sync log."""
        system = ExternalSystem.objects.create(
            name="Test System",
            type=ExternalSystem.SystemType.SERVICENOW_CMDB,
            api_url="https://test.com",
            auth_type=ExternalSystem.AuthType.BASIC,
            credentials={},
        )

        log = IntegrationSyncLog.objects.create(
            system=system,
            sync_started_at=timezone.now(),
            status=IntegrationSyncLog.SyncStatus.RUNNING,
        )

        assert log.system == system
        assert log.status == IntegrationSyncLog.SyncStatus.RUNNING
        assert log.correlation_id is not None

    def test_sync_log_duration_calculation(self):
        """Test duration calculation when sync completes."""
        from datetime import timedelta

        system = ExternalSystem.objects.create(
            name="Test System",
            type=ExternalSystem.SystemType.SERVICENOW_CMDB,
            api_url="https://test.com",
            auth_type=ExternalSystem.AuthType.BASIC,
            credentials={},
        )

        started = timezone.now()
        completed = started + timedelta(seconds=30)

        log = IntegrationSyncLog.objects.create(
            system=system,
            sync_started_at=started,
            status=IntegrationSyncLog.SyncStatus.RUNNING,
        )

        log.sync_completed_at = completed
        log.status = IntegrationSyncLog.SyncStatus.SUCCESS
        log.save()

        assert log.duration_seconds == 30.0
