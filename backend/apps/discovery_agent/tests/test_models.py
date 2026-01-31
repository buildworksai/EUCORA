# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for Discovery Agent models.
"""
import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.discovery_agent.models import (
    ApplicationVersion,
    DiscoveryReport,
    DiscoveryRun,
    DiscoverySource,
    LicenseGap,
    NormalizedApplication,
    PatchGap,
)


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture
def discovery_source(db):
    """Create a test discovery source."""
    return DiscoverySource.objects.create(
        name="Test SCCM",
        source_type="sccm",
        sync_schedule="daily",
        connection_config={"server": "sccm.example.com"},
    )


@pytest.fixture
def discovery_run(db, discovery_source, user):
    """Create a test discovery run."""
    return DiscoveryRun.objects.create(
        source=discovery_source,
        run_type="full",
        status="completed",
        initiated_by=user,
        completed_at=timezone.now(),
    )


@pytest.fixture
def normalized_app(db):
    """Create a test normalized application."""
    return NormalizedApplication.objects.create(
        name="Microsoft Office",
        publisher="Microsoft",
        fingerprint=NormalizedApplication.generate_fingerprint("Microsoft Office", "Microsoft"),
        is_managed=True,
        total_installs=500,
    )


class TestDiscoverySource:
    """Tests for DiscoverySource model."""

    def test_create_source(self, discovery_source):
        """Test creating a discovery source."""
        assert discovery_source.id is not None
        assert discovery_source.name == "Test SCCM"
        assert discovery_source.source_type == "sccm"
        assert discovery_source.is_active is True

    def test_source_str(self, discovery_source):
        """Test source string representation."""
        assert "Test SCCM" in str(discovery_source)
        assert "sccm" in str(discovery_source)

    def test_source_types(self, db):
        """Test all source types."""
        for source_type in ["sccm", "intune", "ad", "cmdb", "spreadsheet", "network_scan"]:
            source = DiscoverySource.objects.create(
                name=f"Test {source_type}",
                source_type=source_type,
                connection_config={},
            )
            assert source.source_type == source_type


class TestDiscoveryRun:
    """Tests for DiscoveryRun model."""

    def test_create_run(self, discovery_run, discovery_source):
        """Test creating a discovery run."""
        assert discovery_run.id is not None
        assert discovery_run.source == discovery_source
        assert discovery_run.run_type == "full"
        assert discovery_run.status == "completed"

    def test_run_correlation_id(self, discovery_run):
        """Test correlation ID is generated."""
        assert discovery_run.correlation_id is not None
        assert isinstance(discovery_run.correlation_id, uuid.UUID)

    def test_duration_seconds(self, db, discovery_source, user):
        """Test duration calculation."""
        start = timezone.now()
        run = DiscoveryRun.objects.create(
            source=discovery_source,
            run_type="incremental",
            status="completed",
            started_at=start,
            completed_at=start + timedelta(seconds=60),
            initiated_by=user,
        )
        assert run.duration_seconds == 60.0


class TestNormalizedApplication:
    """Tests for NormalizedApplication model."""

    def test_create_normalized_app(self, normalized_app):
        """Test creating a normalized application."""
        assert normalized_app.id is not None
        assert normalized_app.name == "Microsoft Office"
        assert normalized_app.publisher == "Microsoft"
        assert normalized_app.fingerprint is not None

    def test_fingerprint_generation(self):
        """Test fingerprint generation."""
        fp1 = NormalizedApplication.generate_fingerprint("Test App", "Test Publisher")
        fp2 = NormalizedApplication.generate_fingerprint("test app", "test publisher")
        fp3 = NormalizedApplication.generate_fingerprint("Other App", "Other Publisher")

        # Same name/publisher (case insensitive) should generate same fingerprint
        assert fp1 == fp2
        # Different app should have different fingerprint
        assert fp1 != fp3

    def test_fingerprint_uniqueness(self, db):
        """Test fingerprint uniqueness constraint."""
        fp = NormalizedApplication.generate_fingerprint("Unique App", "Publisher")
        NormalizedApplication.objects.create(
            name="Unique App",
            publisher="Publisher",
            fingerprint=fp,
        )
        with pytest.raises(Exception):  # IntegrityError
            NormalizedApplication.objects.create(
                name="Unique App 2",
                publisher="Publisher 2",
                fingerprint=fp,
            )


class TestApplicationVersion:
    """Tests for ApplicationVersion model."""

    def test_create_version(self, db, normalized_app):
        """Test creating an application version."""
        version = ApplicationVersion.objects.create(
            application=normalized_app,
            version="16.0.14326",
            version_major=16,
            version_minor=0,
            version_patch=14326,
            is_current=True,
        )
        assert version.id is not None
        assert version.version == "16.0.14326"
        assert version.is_current is True

    def test_version_str(self, db, normalized_app):
        """Test version string representation."""
        version = ApplicationVersion.objects.create(
            application=normalized_app,
            version="16.0.0",
        )
        assert "Microsoft Office" in str(version)
        assert "16.0.0" in str(version)


class TestLicenseGap:
    """Tests for LicenseGap model."""

    def test_create_license_gap(self, db, normalized_app):
        """Test creating a license gap."""
        gap = LicenseGap.objects.create(
            application=normalized_app,
            gap_type="over_deployment",
            detected_installs=600,
            licensed_count=500,
            gap_count=100,
            risk_level="high",
        )
        assert gap.id is not None
        assert gap.gap_count == 100
        assert gap.status == "open"

    def test_gap_correlation_id(self, db, normalized_app):
        """Test gap gets correlation ID."""
        gap = LicenseGap.objects.create(
            application=normalized_app,
            gap_type="missing_license",
            detected_installs=100,
            licensed_count=0,
            gap_count=100,
            risk_level="critical",
        )
        assert gap.correlation_id is not None


class TestPatchGap:
    """Tests for PatchGap model."""

    def test_create_patch_gap(self, db, normalized_app):
        """Test creating a patch gap."""
        version = ApplicationVersion.objects.create(
            application=normalized_app,
            version="15.0.0",
        )
        gap = PatchGap.objects.create(
            application=normalized_app,
            current_version=version,
            affected_devices=200,
            gap_type="eol_version",
            severity="critical",
        )
        assert gap.id is not None
        assert gap.severity == "critical"
        assert gap.status == "open"


class TestDiscoveryReport:
    """Tests for DiscoveryReport model."""

    def test_create_report(self, db, user):
        """Test creating a discovery report."""
        report = DiscoveryReport.objects.create(
            report_type="inventory",
            title="Application Inventory Report",
            summary={"total": 100},
            generated_by=user,
        )
        assert report.id is not None
        assert report.correlation_id is not None

    def test_report_types(self, db, user):
        """Test all report types."""
        for report_type in ["inventory", "shadow_it", "license_compliance", "patch_compliance", "risk_assessment"]:
            report = DiscoveryReport.objects.create(
                report_type=report_type,
                title=f"Test {report_type}",
                generated_by=user,
            )
            assert report.report_type == report_type
