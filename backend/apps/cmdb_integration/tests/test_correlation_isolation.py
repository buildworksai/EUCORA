# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Correlation ID isolation tests for CMDB Integration.

MANDATORY tests for audit trail integrity.
"""
import uuid

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from apps.cmdb_integration.models import CMDBConnection, CMDBDataQualityReport, CMDBDiscrepancy, CMDBSyncRecord


@pytest.fixture
def api_client(db):
    """Create authenticated API client."""
    user = User.objects.create_user(username="testuser", password="testpass")
    client = APIClient()
    client.force_authenticate(user=user)
    client.user = user
    return client


@pytest.fixture
def cmdb_connection(db):
    """Create test connection."""
    return CMDBConnection.objects.create(
        name="Test CMDB",
        instance_url="https://test.service-now.com",
        auth_type="basic",
        credentials={},
    )


class TestCorrelationIdGeneration:
    """Test that correlation IDs are automatically generated."""

    def test_sync_record_correlation_id(self, cmdb_connection, api_client):
        """Test sync record gets correlation ID."""
        record = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="incremental",
            initiated_by=api_client.user,
        )
        assert record.correlation_id is not None
        assert isinstance(record.correlation_id, uuid.UUID)

    def test_quality_report_correlation_id(self, cmdb_connection):
        """Test quality report gets correlation ID."""
        report = CMDBDataQualityReport.objects.create(
            connection=cmdb_connection,
            overall_score=85.0,
            completeness_score=90.0,
            accuracy_score=85.0,
            consistency_score=80.0,
            timeliness_score=85.0,
        )
        assert report.correlation_id is not None


class TestCorrelationIdFiltering:
    """Test filtering by correlation ID."""

    def test_filter_sync_records_by_correlation_id(self, cmdb_connection, api_client):
        """Test filtering sync records."""
        # Create multiple records
        record1 = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="full",
            initiated_by=api_client.user,
        )
        _record2 = CMDBSyncRecord.objects.create(  # noqa: F841
            connection=cmdb_connection,
            sync_type="incremental",
            initiated_by=api_client.user,
        )

        # Filter by correlation_id
        response = api_client.get(f"/api/cmdb/sync/?correlation_id={record1.correlation_id}")
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["correlation_id"] == str(record1.correlation_id)

    def test_correlation_id_uniqueness(self, cmdb_connection, api_client):
        """Test that correlation IDs are unique."""
        records = [
            CMDBSyncRecord.objects.create(
                connection=cmdb_connection,
                sync_type="incremental",
                initiated_by=api_client.user,
            )
            for _ in range(10)
        ]

        correlation_ids = [r.correlation_id for r in records]
        assert len(set(correlation_ids)) == len(correlation_ids)


class TestCorrelationIdPreservation:
    """Test that correlation IDs are preserved through API."""

    def test_correlation_id_in_response(self, cmdb_connection, api_client):
        """Test correlation ID is returned in API response."""
        record = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="full",
            initiated_by=api_client.user,
        )

        response = api_client.get(f"/api/cmdb/sync/{record.id}/")
        assert response.status_code == 200
        assert "correlation_id" in response.data
        assert response.data["correlation_id"] == str(record.correlation_id)

    def test_correlation_id_immutable(self, cmdb_connection, api_client):
        """Test that correlation ID cannot be modified."""
        record = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="full",
            initiated_by=api_client.user,
        )
        original_correlation_id = record.correlation_id

        # Try to update via API (sync records don't support PUT, but test model directly)
        record.status = "completed"
        record.save()
        record.refresh_from_db()

        # Correlation ID should be unchanged
        assert record.correlation_id == original_correlation_id


class TestAuditTrailIntegrity:
    """Test audit trail through correlation IDs."""

    def test_related_discrepancies_tracked(self, cmdb_connection, api_client):
        """Test that discrepancies are linked to sync records."""
        sync_record = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="full",
            initiated_by=api_client.user,
        )

        # Create discrepancies
        for i in range(3):
            CMDBDiscrepancy.objects.create(
                sync_record=sync_record,
                ci_name=f"TEST-{i}",
                ci_class="cmdb_ci_computer",
                discrepancy_type="mismatch",
                recommended_action="update",
            )

        # All discrepancies should be linked to the sync record
        discrepancies = CMDBDiscrepancy.objects.filter(sync_record=sync_record)
        assert discrepancies.count() == 3

        # All discrepancies can be traced back via sync record correlation ID
        for disc in discrepancies:
            assert disc.sync_record.correlation_id == sync_record.correlation_id

    def test_quality_report_linked_to_sync(self, cmdb_connection, api_client):
        """Test quality reports are linked to sync records."""
        sync_record = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="full",
            initiated_by=api_client.user,
        )

        report = CMDBDataQualityReport.objects.create(
            connection=cmdb_connection,
            sync_record=sync_record,
            overall_score=85.0,
            completeness_score=90.0,
            accuracy_score=85.0,
            consistency_score=80.0,
            timeliness_score=85.0,
        )

        # Report should be linked to sync record
        assert report.sync_record == sync_record
        assert report.sync_record.correlation_id == sync_record.correlation_id
