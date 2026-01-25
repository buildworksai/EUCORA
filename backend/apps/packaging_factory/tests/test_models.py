# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for packaging factory (15 tests).
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.packaging_factory.models import PackagingPipeline, PackagingStageLog

User = get_user_model()


class PackagingPipelineModelTests(TestCase):
    """Tests for PackagingPipeline model."""

    def setUp(self):
        """Set up test data."""
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()

    def test_pipeline_creation(self):
        """Test pipeline is created with correct attributes."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://artifacts.example.com/test-app-1.0.0.msi",
            source_artifact_hash="abc123",
            created_by=self.user,
        )

        self.assertEqual(pipeline.package_name, "test-app")
        self.assertEqual(pipeline.platform, "windows")
        self.assertEqual(pipeline.status, "PENDING")
        self.assertIsInstance(pipeline.id, uuid.UUID)

    def test_pipeline_str_representation(self):
        """Test string representation of pipeline."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
        )

        expected = "test-app 1.0.0 (windows) - PENDING"
        self.assertEqual(str(pipeline), expected)

    def test_is_completed_property(self):
        """Test is_completed property."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            status="PENDING",
        )

        self.assertFalse(pipeline.is_completed)

        pipeline.status = "COMPLETED"
        pipeline.save()

        self.assertTrue(pipeline.is_completed)

    def test_has_blocking_vulnerabilities_property(self):
        """Test has_blocking_vulnerabilities property."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            critical_count=0,
            high_count=0,
        )

        self.assertFalse(pipeline.has_blocking_vulnerabilities)

        pipeline.critical_count = 1
        pipeline.save()

        self.assertTrue(pipeline.has_blocking_vulnerabilities)

        pipeline.critical_count = 0
        pipeline.high_count = 1
        pipeline.save()

        self.assertTrue(pipeline.has_blocking_vulnerabilities)

    def test_duration_seconds_property(self):
        """Test duration_seconds calculation."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
        )

        # No completion yet
        self.assertIsNone(pipeline.duration_seconds)

        # Complete pipeline
        pipeline.completed_at = pipeline.created_at + timedelta(seconds=120)
        pipeline.save()

        self.assertEqual(pipeline.duration_seconds, 120.0)

    def test_platform_choices(self):
        """Test platform field accepts only valid choices."""
        for platform in ["windows", "macos", "linux"]:
            pipeline = PackagingPipeline.objects.create(
                package_name=f"test-{platform}",
                package_version="1.0.0",
                platform=platform,
                package_type="MSI",
                source_artifact_url="https://test.com/app",
                source_artifact_hash="hash",
                created_by=self.user,
            )
            self.assertEqual(pipeline.platform, platform)

    def test_status_transitions(self):
        """Test pipeline status transitions."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            status="PENDING",
        )

        stages = ["INTAKE", "BUILD", "SIGN", "SBOM", "SCAN", "POLICY", "STORE", "COMPLETED"]
        for stage in stages:
            pipeline.status = stage
            pipeline.save()
            self.assertEqual(pipeline.status, stage)

    def test_policy_decision_choices(self):
        """Test policy decision field."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
        )

        for decision in ["PASS", "FAIL", "EXCEPTION"]:
            pipeline.policy_decision = decision
            pipeline.save()
            self.assertEqual(pipeline.policy_decision, decision)

    def test_scan_results_json_field(self):
        """Test scan_results JSON field."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            scan_results={"scanner": "trivy", "vulnerabilities": []},
        )

        self.assertEqual(pipeline.scan_results["scanner"], "trivy")


class PackagingStageLogModelTests(TestCase):
    """Tests for PackagingStageLog model."""

    def setUp(self):
        """Set up test data."""
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
        )

    def test_stage_log_creation(self):
        """Test stage log is created correctly."""
        log = PackagingStageLog.objects.create(
            pipeline=self.pipeline, stage_name="BUILD", status="SUCCESS", output="Build completed successfully"
        )

        self.assertEqual(log.pipeline, self.pipeline)
        self.assertEqual(log.stage_name, "BUILD")
        self.assertEqual(log.status, "SUCCESS")

    def test_stage_log_str_representation(self):
        """Test string representation of stage log."""
        log = PackagingStageLog.objects.create(pipeline=self.pipeline, stage_name="SCAN", status="SUCCESS")

        expected = f"{self.pipeline.package_name} - SCAN (SUCCESS)"
        self.assertEqual(str(log), expected)

    def test_stage_log_duration(self):
        """Test stage log duration calculation."""
        log = PackagingStageLog.objects.create(pipeline=self.pipeline, stage_name="BUILD", status="SUCCESS")

        # No completion yet
        self.assertIsNone(log.duration_seconds)

        # Complete stage
        log.completed_at = log.started_at + timedelta(seconds=60)
        log.save()

        self.assertEqual(log.duration_seconds, 60.0)

    def test_stage_log_ordering(self):
        """Test stage logs are ordered by started_at."""
        log1 = PackagingStageLog.objects.create(pipeline=self.pipeline, stage_name="INTAKE", status="SUCCESS")
        log2 = PackagingStageLog.objects.create(pipeline=self.pipeline, stage_name="BUILD", status="SUCCESS")

        logs = PackagingStageLog.objects.all()
        self.assertEqual(logs[0], log1)
        self.assertEqual(logs[1], log2)

    def test_stage_log_metadata_field(self):
        """Test metadata JSON field."""
        log = PackagingStageLog.objects.create(
            pipeline=self.pipeline, stage_name="SCAN", status="SUCCESS", metadata={"tool": "trivy", "version": "0.1.0"}
        )

        self.assertEqual(log.metadata["tool"], "trivy")

    def test_stage_log_relationship_with_pipeline(self):
        """Test relationship between stage log and pipeline."""
        log1 = PackagingStageLog.objects.create(pipeline=self.pipeline, stage_name="BUILD", status="SUCCESS")
        log2 = PackagingStageLog.objects.create(pipeline=self.pipeline, stage_name="SCAN", status="SUCCESS")

        self.assertEqual(self.pipeline.stage_logs.count(), 2)
        self.assertIn(log1, self.pipeline.stage_logs.all())
        self.assertIn(log2, self.pipeline.stage_logs.all())
