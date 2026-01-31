# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for CMDB Integration models.
"""
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.cmdb_integration.models import (
    CMDBConnection,
    CMDBDataQualityReport,
    CMDBDiscrepancy,
    CMDBSyncRecord,
    CMDBTableMapping,
    CMDBValidationRule,
)


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def cmdb_connection(db):
    """Create a test CMDB connection."""
    return CMDBConnection.objects.create(
        name="Test ServiceNow",
        instance_url="https://test.service-now.com",
        auth_type="basic",
        credentials={"username": "admin", "password": "secret"},
        is_active=True,
    )


@pytest.fixture
def table_mapping(db, cmdb_connection):
    """Create a test table mapping."""
    return CMDBTableMapping.objects.create(
        connection=cmdb_connection,
        source_type="sccm",
        source_table="v_R_System",
        cmdb_table="cmdb_ci_computer",
        field_mappings={"Name0": "name", "SerialNumber": "serial_number"},
        sync_enabled=True,
    )


@pytest.fixture
def validation_rule(db):
    """Create a test validation rule."""
    return CMDBValidationRule.objects.create(
        name="Serial Number Required",
        cmdb_table="cmdb_ci_computer",
        field_name="serial_number",
        rule_type="required",
        rule_config={},
        severity="error",
        is_active=True,
    )


@pytest.fixture
def sync_record(db, cmdb_connection, user):
    """Create a test sync record."""
    return CMDBSyncRecord.objects.create(
        connection=cmdb_connection,
        sync_type="incremental",
        status="pending",
        initiated_by=user,
    )


class TestCMDBConnection:
    """Tests for CMDBConnection model."""

    def test_create_connection(self, cmdb_connection):
        """Test creating a CMDB connection."""
        assert cmdb_connection.id is not None
        assert cmdb_connection.name == "Test ServiceNow"
        assert cmdb_connection.instance_url == "https://test.service-now.com"
        assert cmdb_connection.auth_type == "basic"
        assert cmdb_connection.is_active is True

    def test_connection_str(self, cmdb_connection):
        """Test connection string representation."""
        expected = "Test ServiceNow (https://test.service-now.com)"
        assert str(cmdb_connection) == expected

    def test_connection_auth_types(self, db):
        """Test all auth types."""
        for auth_type in ["basic", "oauth", "api_key"]:
            conn = CMDBConnection.objects.create(
                name=f"Test {auth_type}",
                instance_url="https://test.service-now.com",
                auth_type=auth_type,
                credentials={},
            )
            assert conn.auth_type == auth_type

    def test_connection_timestamps(self, cmdb_connection):
        """Test timestamp fields."""
        assert cmdb_connection.created_at is not None
        assert cmdb_connection.updated_at is not None


class TestCMDBTableMapping:
    """Tests for CMDBTableMapping model."""

    def test_create_mapping(self, table_mapping, cmdb_connection):
        """Test creating a table mapping."""
        assert table_mapping.id is not None
        assert table_mapping.connection == cmdb_connection
        assert table_mapping.source_type == "sccm"
        assert table_mapping.cmdb_table == "cmdb_ci_computer"
        assert table_mapping.sync_enabled is True

    def test_mapping_str(self, table_mapping):
        """Test mapping string representation."""
        assert str(table_mapping) == "sccm → cmdb_ci_computer"

    def test_mapping_field_mappings(self, table_mapping):
        """Test field mappings JSON field."""
        assert "Name0" in table_mapping.field_mappings
        assert table_mapping.field_mappings["Name0"] == "name"

    def test_mapping_unique_constraint(self, db, cmdb_connection):
        """Test unique constraint on mapping."""
        CMDBTableMapping.objects.create(
            connection=cmdb_connection,
            source_type="sccm",
            source_table="v_R_System",
            cmdb_table="cmdb_ci_computer",
            field_mappings={},
        )
        with pytest.raises(Exception):  # IntegrityError
            CMDBTableMapping.objects.create(
                connection=cmdb_connection,
                source_type="sccm",
                source_table="v_R_System",
                cmdb_table="cmdb_ci_computer",
                field_mappings={},
            )


class TestCMDBValidationRule:
    """Tests for CMDBValidationRule model."""

    def test_create_rule(self, validation_rule):
        """Test creating a validation rule."""
        assert validation_rule.id is not None
        assert validation_rule.name == "Serial Number Required"
        assert validation_rule.rule_type == "required"
        assert validation_rule.severity == "error"

    def test_rule_str(self, validation_rule):
        """Test rule string representation."""
        assert "Serial Number Required" in str(validation_rule)
        assert "cmdb_ci_computer" in str(validation_rule)

    def test_rule_types(self, db):
        """Test all rule types."""
        for rule_type in ["required", "format", "reference", "range", "regex", "custom"]:
            rule = CMDBValidationRule.objects.create(
                name=f"Test {rule_type}",
                cmdb_table="cmdb_ci_computer",
                rule_type=rule_type,
                rule_config={},
            )
            assert rule.rule_type == rule_type


class TestCMDBSyncRecord:
    """Tests for CMDBSyncRecord model."""

    def test_create_sync_record(self, sync_record, cmdb_connection, user):
        """Test creating a sync record."""
        assert sync_record.id is not None
        assert sync_record.connection == cmdb_connection
        assert sync_record.sync_type == "incremental"
        assert sync_record.status == "pending"
        assert sync_record.initiated_by == user

    def test_sync_record_str(self, sync_record):
        """Test sync record string representation."""
        assert "incremental" in str(sync_record)

    def test_sync_record_correlation_id(self, sync_record):
        """Test correlation ID is generated."""
        assert sync_record.correlation_id is not None

    def test_duration_seconds(self, db, cmdb_connection, user):
        """Test duration calculation."""
        start = timezone.now()
        record = CMDBSyncRecord.objects.create(
            connection=cmdb_connection,
            sync_type="full",
            status="completed",
            started_at=start,
            completed_at=start + timedelta(seconds=120),
            initiated_by=user,
        )
        assert record.duration_seconds == 120.0

    def test_duration_seconds_not_completed(self, sync_record):
        """Test duration when not completed."""
        assert sync_record.duration_seconds is None


class TestCMDBDiscrepancy:
    """Tests for CMDBDiscrepancy model."""

    def test_create_discrepancy(self, db, sync_record):
        """Test creating a discrepancy."""
        discrepancy = CMDBDiscrepancy.objects.create(
            sync_record=sync_record,
            ci_sys_id="abc123",
            ci_name="DESKTOP-001",
            ci_class="cmdb_ci_computer",
            discrepancy_type="mismatch",
            field_name="serial_number",
            source_value="SN-001",
            cmdb_value="SN-OLD",
            recommended_action="update",
            confidence_score=0.9,
        )
        assert discrepancy.id is not None
        assert discrepancy.ci_name == "DESKTOP-001"
        assert discrepancy.status == "pending"

    def test_discrepancy_str(self, db, sync_record):
        """Test discrepancy string representation."""
        discrepancy = CMDBDiscrepancy.objects.create(
            sync_record=sync_record,
            ci_name="DESKTOP-001",
            ci_class="cmdb_ci_computer",
            discrepancy_type="missing",
            recommended_action="create",
        )
        assert "DESKTOP-001" in str(discrepancy)
        assert "missing" in str(discrepancy)


class TestCMDBDataQualityReport:
    """Tests for CMDBDataQualityReport model."""

    def test_create_report(self, db, cmdb_connection, sync_record):
        """Test creating a quality report."""
        report = CMDBDataQualityReport.objects.create(
            connection=cmdb_connection,
            sync_record=sync_record,
            overall_score=85.5,
            completeness_score=90.0,
            accuracy_score=88.0,
            consistency_score=82.0,
            timeliness_score=82.0,
            total_cis=1000,
            cis_with_issues=150,
        )
        assert report.id is not None
        assert report.overall_score == 85.5

    def test_report_str(self, db, cmdb_connection):
        """Test report string representation."""
        report = CMDBDataQualityReport.objects.create(
            connection=cmdb_connection,
            overall_score=85.5,
            completeness_score=90.0,
            accuracy_score=88.0,
            consistency_score=82.0,
            timeliness_score=82.0,
        )
        assert "85.5%" in str(report)
