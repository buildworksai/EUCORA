# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for CMDB Integration.
"""
import pytest

from apps.cmdb_integration.models import CMDBConnection, CMDBValidationRule
from apps.cmdb_integration.services.servicenow_client import MockServiceNowCMDBClient
from apps.cmdb_integration.services.validation_engine import (
    CMDBValidationEngine,
    RecordValidationResult,
    ValidationResult,
)


@pytest.fixture
def cmdb_connection(db):
    """Create test connection."""
    return CMDBConnection.objects.create(
        name="Test CMDB",
        instance_url="https://test.service-now.com",
        auth_type="basic",
        credentials={"username": "test", "password": "test"},
    )


class TestMockServiceNowClient:
    """Tests for MockServiceNowCMDBClient."""

    @pytest.mark.asyncio
    async def test_test_connection(self, cmdb_connection):
        """Test connection test."""
        client = MockServiceNowCMDBClient(cmdb_connection)
        result = await client.test_connection()
        assert result["success"] is True
        assert result["mock"] is True
        await client.close()

    @pytest.mark.asyncio
    async def test_query_cis(self, cmdb_connection):
        """Test querying CIs."""
        client = MockServiceNowCMDBClient(cmdb_connection)
        records = await client.query_cis("cmdb_ci_computer", limit=10)
        assert len(records) <= 10
        await client.close()

    @pytest.mark.asyncio
    async def test_get_ci(self, cmdb_connection):
        """Test getting a single CI."""
        client = MockServiceNowCMDBClient(cmdb_connection)
        records = await client.query_cis("cmdb_ci_computer", limit=1)
        if records:
            ci = await client.get_ci("cmdb_ci_computer", records[0]["sys_id"])
            assert ci is not None
            assert ci["sys_id"] == records[0]["sys_id"]
        await client.close()

    @pytest.mark.asyncio
    async def test_create_ci(self, cmdb_connection):
        """Test creating a CI."""
        client = MockServiceNowCMDBClient(cmdb_connection)
        data = {"name": "TEST-NEW-001", "serial_number": "SN-12345"}
        result = await client.create_ci("cmdb_ci_computer", data)
        assert "sys_id" in result
        assert result["name"] == "TEST-NEW-001"
        await client.close()

    @pytest.mark.asyncio
    async def test_update_ci(self, cmdb_connection):
        """Test updating a CI."""
        client = MockServiceNowCMDBClient(cmdb_connection)
        # First create a CI
        data = {"name": "TEST-UPDATE", "serial_number": "SN-UPDATE"}
        created = await client.create_ci("cmdb_ci_computer", data)
        # Then update it
        updated = await client.update_ci(
            "cmdb_ci_computer",
            created["sys_id"],
            {"name": "TEST-UPDATED"},
        )
        assert updated["name"] == "TEST-UPDATED"
        await client.close()

    @pytest.mark.asyncio
    async def test_delete_ci(self, cmdb_connection):
        """Test deleting a CI."""
        client = MockServiceNowCMDBClient(cmdb_connection)
        # First create a CI
        data = {"name": "TEST-DELETE", "serial_number": "SN-DELETE"}
        created = await client.create_ci("cmdb_ci_computer", data)
        # Then delete it
        result = await client.delete_ci("cmdb_ci_computer", created["sys_id"])
        assert result is True
        await client.close()


class TestCMDBValidationEngine:
    """Tests for CMDBValidationEngine."""

    @pytest.fixture
    def validation_rules(self, db):
        """Create test validation rules."""
        return [
            CMDBValidationRule.objects.create(
                name="Name Required",
                cmdb_table="cmdb_ci_computer",
                field_name="name",
                rule_type="required",
                severity="error",
                is_active=True,
            ),
            CMDBValidationRule.objects.create(
                name="Serial Number Required",
                cmdb_table="cmdb_ci_computer",
                field_name="serial_number",
                rule_type="required",
                severity="warning",
                is_active=True,
            ),
            CMDBValidationRule.objects.create(
                name="IP Format",
                cmdb_table="cmdb_ci_computer",
                field_name="ip_address",
                rule_type="format",
                rule_config={"format": "ip_address"},
                severity="error",
                is_active=True,
            ),
        ]

    def test_validate_valid_record(self, validation_rules):
        """Test validating a valid record."""
        engine = CMDBValidationEngine(rules=validation_rules)
        record = {
            "sys_id": "abc123",
            "name": "TEST-001",
            "serial_number": "SN-001",
            "ip_address": "192.168.1.100",
        }
        result = engine.validate_record(record, "cmdb_ci_computer")
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_required(self, validation_rules):
        """Test validation with missing required field."""
        engine = CMDBValidationEngine(rules=validation_rules)
        record = {
            "sys_id": "abc123",
            "serial_number": "SN-001",
        }
        result = engine.validate_record(record, "cmdb_ci_computer")
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].field_name == "name"

    def test_validate_invalid_ip(self, validation_rules):
        """Test validation with invalid IP address."""
        engine = CMDBValidationEngine(rules=validation_rules)
        record = {
            "sys_id": "abc123",
            "name": "TEST-001",
            "serial_number": "SN-001",
            "ip_address": "invalid-ip",
        }
        result = engine.validate_record(record, "cmdb_ci_computer")
        assert result.is_valid is False
        assert any(e.field_name == "ip_address" for e in result.errors)

    def test_validate_valid_ip_formats(self, validation_rules):
        """Test validation with various valid IP formats."""
        engine = CMDBValidationEngine(rules=validation_rules)
        valid_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.100", "255.255.255.0"]

        for ip in valid_ips:
            record = {
                "sys_id": "abc123",
                "name": "TEST-001",
                "serial_number": "SN-001",
                "ip_address": ip,
            }
            result = engine.validate_record(record, "cmdb_ci_computer")
            assert result.is_valid is True, f"IP {ip} should be valid"

    def test_validate_no_rules_for_table(self, validation_rules):
        """Test validation when no rules exist for table."""
        engine = CMDBValidationEngine(rules=validation_rules)
        record = {"sys_id": "abc123", "name": "TEST-001"}
        result = engine.validate_record(record, "cmdb_ci_server")  # Different table
        assert result.is_valid is True

    def test_calculate_quality_score_perfect(self, validation_rules):
        """Test quality score calculation with all valid records."""
        engine = CMDBValidationEngine(rules=validation_rules)

        results = [
            RecordValidationResult(
                ci_sys_id=f"id{i}",
                ci_name=f"TEST-{i}",
                ci_class="cmdb_ci_computer",
                is_valid=True,
            )
            for i in range(10)
        ]

        scores = engine.calculate_quality_score(results)
        assert scores["overall_score"] == 100.0

    def test_calculate_quality_score_with_issues(self, validation_rules):
        """Test quality score calculation with validation issues."""
        engine = CMDBValidationEngine(rules=validation_rules)

        # Create some failed validation results
        results = []
        for i in range(10):
            result = RecordValidationResult(
                ci_sys_id=f"id{i}",
                ci_name=f"TEST-{i}",
                ci_class="cmdb_ci_computer",
                is_valid=i >= 5,  # 5 valid, 5 invalid
            )
            if i < 5:
                result.errors.append(
                    ValidationResult(
                        passed=False,
                        rule_name="Required",
                        rule_type="required",
                        severity="error",
                        field_name="name",
                    )
                )
            results.append(result)

        scores = engine.calculate_quality_score(results)
        assert scores["overall_score"] < 100.0
        assert scores["completeness_score"] < 100.0

    def test_regex_validation(self, db):
        """Test regex rule validation."""
        rule = CMDBValidationRule.objects.create(
            name="Hostname Format",
            cmdb_table="cmdb_ci_computer",
            field_name="name",
            rule_type="regex",
            rule_config={"pattern": r"^[A-Z]+-\d{3,}$"},
            severity="error",
            is_active=True,
        )
        engine = CMDBValidationEngine(rules=[rule])

        # Valid hostname
        result = engine.validate_record(
            {"sys_id": "1", "name": "DESKTOP-001"},
            "cmdb_ci_computer",
        )
        assert result.is_valid is True

        # Invalid hostname
        result = engine.validate_record(
            {"sys_id": "1", "name": "invalid"},
            "cmdb_ci_computer",
        )
        assert result.is_valid is False

    def test_range_validation(self, db):
        """Test range rule validation."""
        rule = CMDBValidationRule.objects.create(
            name="CPU Count",
            cmdb_table="cmdb_ci_server",
            field_name="cpu_count",
            rule_type="range",
            rule_config={"min": 1, "max": 128},
            severity="warning",
            is_active=True,
        )
        engine = CMDBValidationEngine(rules=[rule])

        # Valid range
        result = engine.validate_record(
            {"sys_id": "1", "name": "SRV-001", "cpu_count": 16},
            "cmdb_ci_server",
        )
        assert result.is_valid is True

        # Below min
        result = engine.validate_record(
            {"sys_id": "1", "name": "SRV-001", "cpu_count": 0},
            "cmdb_ci_server",
        )
        assert len(result.warnings) == 1

        # Above max
        result = engine.validate_record(
            {"sys_id": "1", "name": "SRV-001", "cpu_count": 256},
            "cmdb_ci_server",
        )
        assert len(result.warnings) == 1
