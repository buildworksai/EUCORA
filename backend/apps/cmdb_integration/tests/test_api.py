# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for CMDB Integration.
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient

from apps.cmdb_integration.models import (
    CMDBConnection,
    CMDBDiscrepancy,
    CMDBSyncRecord,
    CMDBTableMapping,
    CMDBValidationRule,
)


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(db):
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
        credentials={"username": "test", "password": "test"},
    )


@pytest.fixture
def sync_record(db, cmdb_connection, authenticated_client):
    """Create test sync record."""
    return CMDBSyncRecord.objects.create(
        connection=cmdb_connection,
        sync_type="incremental",
        status="completed",
        initiated_by=authenticated_client.user,
        records_processed=100,
    )


class TestCMDBConnectionAPI:
    """Tests for CMDB Connection API."""

    def test_list_connections_unauthenticated(self, api_client):
        """Test listing connections without authentication."""
        response = api_client.get("/api/cmdb/connections/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_connections(self, authenticated_client, cmdb_connection):
        """Test listing connections."""
        response = authenticated_client.get("/api/cmdb/connections/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Test CMDB"

    def test_create_connection(self, authenticated_client):
        """Test creating a connection."""
        data = {
            "name": "New Connection",
            "instance_url": "https://new.service-now.com",
            "auth_type": "basic",
            "credentials": {"username": "admin", "password": "secret"},
        }
        response = authenticated_client.post("/api/cmdb/connections/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert CMDBConnection.objects.filter(name="New Connection").exists()

    def test_get_connection(self, authenticated_client, cmdb_connection):
        """Test getting a single connection."""
        response = authenticated_client.get(f"/api/cmdb/connections/{cmdb_connection.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test CMDB"
        # Credentials should be masked
        assert response.data["credentials"]["username"] == "***"

    def test_update_connection(self, authenticated_client, cmdb_connection):
        """Test updating a connection."""
        data = {"name": "Updated CMDB"}
        response = authenticated_client.patch(
            f"/api/cmdb/connections/{cmdb_connection.id}/",
            data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        cmdb_connection.refresh_from_db()
        assert cmdb_connection.name == "Updated CMDB"

    def test_delete_connection(self, authenticated_client, cmdb_connection):
        """Test deleting a connection."""
        response = authenticated_client.delete(f"/api/cmdb/connections/{cmdb_connection.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not CMDBConnection.objects.filter(id=cmdb_connection.id).exists()

    def test_test_connection(self, authenticated_client, cmdb_connection):
        """Test connection test endpoint."""
        response = authenticated_client.post(f"/api/cmdb/connections/{cmdb_connection.id}/test/")
        assert response.status_code == status.HTTP_200_OK
        assert "success" in response.data


class TestCMDBTableMappingAPI:
    """Tests for CMDB Table Mapping API."""

    def test_list_mappings(self, authenticated_client, cmdb_connection):
        """Test listing mappings."""
        CMDBTableMapping.objects.create(
            connection=cmdb_connection,
            source_type="sccm",
            source_table="v_R_System",
            cmdb_table="cmdb_ci_computer",
            field_mappings={"Name0": "name"},
        )
        response = authenticated_client.get("/api/cmdb/mappings/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_mapping(self, authenticated_client, cmdb_connection):
        """Test creating a mapping."""
        data = {
            "connection": str(cmdb_connection.id),
            "source_type": "intune",
            "source_table": "devices",
            "cmdb_table": "cmdb_ci_computer",
            "field_mappings": {"deviceName": "name"},
            "sync_enabled": True,
        }
        response = authenticated_client.post("/api/cmdb/mappings/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_by_connection(self, authenticated_client, cmdb_connection):
        """Test filtering mappings by connection."""
        CMDBTableMapping.objects.create(
            connection=cmdb_connection,
            source_type="sccm",
            source_table="v_R_System",
            cmdb_table="cmdb_ci_computer",
            field_mappings={},
        )
        response = authenticated_client.get(f"/api/cmdb/mappings/?connection_id={cmdb_connection.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


class TestCMDBValidationRuleAPI:
    """Tests for CMDB Validation Rule API."""

    def test_list_rules(self, authenticated_client, db):
        """Test listing validation rules."""
        CMDBValidationRule.objects.create(
            name="Required Name",
            cmdb_table="cmdb_ci_computer",
            field_name="name",
            rule_type="required",
            severity="error",
        )
        response = authenticated_client.get("/api/cmdb/validation-rules/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_rule(self, authenticated_client):
        """Test creating a validation rule."""
        data = {
            "name": "IP Format",
            "cmdb_table": "cmdb_ci_computer",
            "field_name": "ip_address",
            "rule_type": "format",
            "rule_config": {"format": "ip_address"},
            "severity": "warning",
        }
        response = authenticated_client.post("/api/cmdb/validation-rules/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED


class TestCMDBSyncAPI:
    """Tests for CMDB Sync API."""

    def test_list_syncs(self, authenticated_client, sync_record):
        """Test listing sync records."""
        response = authenticated_client.get("/api/cmdb/sync/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_start_sync(self, authenticated_client, cmdb_connection):
        """Test starting a sync."""
        data = {
            "connection_id": str(cmdb_connection.id),
            "sync_type": "incremental",
        }
        response = authenticated_client.post("/api/cmdb/sync/", data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["status"] in ["pending", "running", "completed"]

    def test_get_sync_discrepancies(self, authenticated_client, sync_record):
        """Test getting discrepancies for a sync."""
        CMDBDiscrepancy.objects.create(
            sync_record=sync_record,
            ci_name="TEST-001",
            ci_class="cmdb_ci_computer",
            discrepancy_type="mismatch",
            recommended_action="update",
        )
        response = authenticated_client.get(f"/api/cmdb/sync/{sync_record.id}/discrepancies/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


class TestCMDBDiscrepancyAPI:
    """Tests for CMDB Discrepancy API."""

    @pytest.fixture
    def discrepancy(self, db, sync_record):
        """Create test discrepancy."""
        return CMDBDiscrepancy.objects.create(
            sync_record=sync_record,
            ci_name="TEST-001",
            ci_class="cmdb_ci_computer",
            discrepancy_type="mismatch",
            field_name="serial_number",
            source_value="SN-NEW",
            cmdb_value="SN-OLD",
            recommended_action="update",
            status="pending",
        )

    def test_list_discrepancies(self, authenticated_client, discrepancy):
        """Test listing discrepancies."""
        response = authenticated_client.get("/api/cmdb/discrepancies/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_filter_by_status(self, authenticated_client, discrepancy):
        """Test filtering by status."""
        response = authenticated_client.get("/api/cmdb/discrepancies/?status=pending")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        response = authenticated_client.get("/api/cmdb/discrepancies/?status=approved")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_approve_discrepancy(self, authenticated_client, discrepancy):
        """Test approving a discrepancy."""
        data = {"action": "approve", "resolution_notes": "Approved by admin"}
        response = authenticated_client.post(
            f"/api/cmdb/discrepancies/{discrepancy.id}/approve/",
            data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        discrepancy.refresh_from_db()
        assert discrepancy.status == "approved"

    def test_reject_discrepancy(self, authenticated_client, discrepancy):
        """Test rejecting a discrepancy."""
        data = {"action": "reject", "resolution_notes": "Not valid"}
        response = authenticated_client.post(
            f"/api/cmdb/discrepancies/{discrepancy.id}/reject/",
            data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        discrepancy.refresh_from_db()
        assert discrepancy.status == "rejected"

    def test_bulk_approve(self, authenticated_client, sync_record):
        """Test bulk approving discrepancies."""
        discs = [
            CMDBDiscrepancy.objects.create(
                sync_record=sync_record,
                ci_name=f"TEST-{i}",
                ci_class="cmdb_ci_computer",
                discrepancy_type="mismatch",
                recommended_action="update",
                status="pending",
            )
            for i in range(3)
        ]
        data = {
            "discrepancy_ids": [str(d.id) for d in discs],
            "action": "approve",
        }
        response = authenticated_client.post(
            "/api/cmdb/discrepancies/bulk-approve/",
            data,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["updated"] == 3


class TestCMDBReportsAPI:
    """Tests for CMDB Reports API."""

    def test_quality_score_empty(self, authenticated_client):
        """Test quality score with no data."""
        response = authenticated_client.get("/api/cmdb/reports/quality-score/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["overall_score"] == 0

    def test_sync_history(self, authenticated_client, sync_record):
        """Test sync history endpoint."""
        response = authenticated_client.get("/api/cmdb/reports/sync-history/")
        assert response.status_code == status.HTTP_200_OK


class TestCorrelationIdFiltering:
    """Tests for correlation ID filtering."""

    def test_sync_records_filter_by_correlation_id(self, authenticated_client, sync_record):
        """Test filtering sync records by correlation ID."""
        response = authenticated_client.get(f"/api/cmdb/sync/?correlation_id={sync_record.correlation_id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["correlation_id"] == str(sync_record.correlation_id)
