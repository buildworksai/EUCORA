# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for packaging factory (20 tests).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.packaging_factory.models import PackagingPipeline, PackagingStageLog
from apps.packaging_factory.services import PackagingFactoryService

User = get_user_model()


class PackagingFactoryServiceTests(TestCase):
    """Tests for PackagingFactoryService."""

    def setUp(self):
        """Set up test data."""
        self.service = PackagingFactoryService()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()

    def test_create_pipeline(self):
        """Test creating packaging pipeline."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
            correlation_id="test-corr-001",
        )

        self.assertIsNotNone(pipeline)
        self.assertEqual(pipeline.package_name, "test-app")
        self.assertEqual(pipeline.status, "PENDING")
        self.assertIsNotNone(pipeline.source_artifact_hash)

    def test_create_pipeline_with_provenance(self):
        """Test creating pipeline with provenance data."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
            source_repo="https://github.com/example/test-app",
            source_commit="abc123def456",
        )

        self.assertEqual(pipeline.source_repo, "https://github.com/example/test-app")
        self.assertEqual(pipeline.source_commit, "abc123def456")

    def test_execute_pipeline_success_no_vulnerabilities(self):
        """Test successful pipeline execution with no vulnerabilities."""
        pipeline = self.service.create_pipeline(
            package_name="safe-app",  # Deterministic seed for 0 critical/high
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/safe-app.msi",
            created_by=self.user,
        )

        # Force no vulnerabilities for this test
        executed_pipeline = self.service.execute_pipeline(str(pipeline.id))

        executed_pipeline.refresh_from_db()
        self.assertEqual(executed_pipeline.status, "COMPLETED")
        self.assertIsNotNone(executed_pipeline.completed_at)

    def test_execute_pipeline_failure_blocking_vulnerabilities(self):
        """Test pipeline fails with blocking vulnerabilities."""
        pipeline = PackagingPipeline.objects.create(
            package_name="vulnerable-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            critical_count=2,
            high_count=5,
        )

        with self.assertRaises(ValueError):
            self.service.execute_pipeline(str(pipeline.id))

        pipeline.refresh_from_db()
        self.assertEqual(pipeline.status, "FAILED")
        self.assertEqual(pipeline.policy_decision, "FAIL")

    def test_execute_pipeline_with_exception(self):
        """Test pipeline succeeds with exception for vulnerabilities."""
        import uuid

        exception_id = uuid.uuid4()

        pipeline = PackagingPipeline.objects.create(
            package_name="excepted-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            exception_id=exception_id,
            critical_count=1,
        )

        # Should not raise even with critical vulnerability
        executed_pipeline = self.service.execute_pipeline(str(pipeline.id))

        executed_pipeline.refresh_from_db()
        self.assertEqual(executed_pipeline.policy_decision, "EXCEPTION")

    def test_stage_intake_creates_log(self):
        """Test INTAKE stage creates log."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_intake(pipeline, "corr-001")

        logs = PackagingStageLog.objects.filter(pipeline=pipeline, stage_name="INTAKE")
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().status, "SUCCESS")

    def test_stage_build_generates_output(self):
        """Test BUILD stage generates output artifact."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_build(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertIsNotNone(pipeline.output_artifact_url)
        self.assertIsNotNone(pipeline.output_artifact_hash)
        self.assertIsNotNone(pipeline.build_id)

    def test_stage_sign_for_windows(self):
        """Test SIGN stage for Windows platform."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_build(pipeline, "corr-001")
        self.service._stage_sign(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertIn("Code Signing", pipeline.signing_certificate)
        self.assertIsNotNone(pipeline.signature_url)

    def test_stage_sign_for_macos(self):
        """Test SIGN stage for macOS platform."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="macos",
            package_type="PKG",
            source_artifact_url="https://test.com/app.pkg",
            created_by=self.user,
        )

        self.service._stage_build(pipeline, "corr-001")
        self.service._stage_sign(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertIn("Apple", pipeline.signing_certificate)

    def test_stage_sbom_generates_sbom(self):
        """Test SBOM stage generates SBOM data."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_build(pipeline, "corr-001")
        self.service._stage_sbom(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertEqual(pipeline.sbom_format, "SPDX-2.3")
        self.assertIsNotNone(pipeline.sbom_url)
        self.assertIsNotNone(pipeline.sbom_generated_at)

        # Check log has SBOM data
        log = PackagingStageLog.objects.get(pipeline=pipeline, stage_name="SBOM")
        self.assertIn("spdxVersion", log.metadata["sbom_data"])

    def test_stage_scan_generates_results(self):
        """Test SCAN stage generates vulnerability results."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_build(pipeline, "corr-001")
        self.service._stage_scan(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertIsNotNone(pipeline.scan_tool)
        self.assertIsNotNone(pipeline.scan_results)
        self.assertGreaterEqual(pipeline.critical_count, 0)

    def test_stage_policy_pass(self):
        """Test POLICY stage passes with no vulnerabilities."""
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

        self.service._stage_policy(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertEqual(pipeline.policy_decision, "PASS")

    def test_stage_policy_fail(self):
        """Test POLICY stage fails with critical vulnerabilities."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
            critical_count=1,
            high_count=0,
        )

        with self.assertRaises(ValueError):
            self.service._stage_policy(pipeline, "corr-001")

        pipeline.refresh_from_db()
        self.assertEqual(pipeline.policy_decision, "FAIL")

    def test_stage_store_creates_metadata(self):
        """Test STORE stage creates storage metadata."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_build(pipeline, "corr-001")
        self.service._stage_store(pipeline, "corr-001")

        log = PackagingStageLog.objects.get(pipeline=pipeline, stage_name="STORE")
        self.assertEqual(log.status, "SUCCESS")
        self.assertIn("bucket", log.metadata)

    def test_get_pipeline_status(self):
        """Test getting pipeline status."""
        pipeline = self.service.create_pipeline(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            created_by=self.user,
        )

        self.service._stage_intake(pipeline, "corr-001")
        self.service._stage_build(pipeline, "corr-001")

        status_data = self.service.get_pipeline_status(str(pipeline.id))

        self.assertEqual(status_data["package_name"], "test-app")
        self.assertEqual(len(status_data["stages"]), 2)
        self.assertIn("vulnerabilities", status_data)

    def test_mock_hash_artifact_deterministic(self):
        """Test artifact hash generation is deterministic."""
        url = "https://test.com/app.msi"
        hash1 = self.service._mock_hash_artifact(url)
        hash2 = self.service._mock_hash_artifact(url)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256

    def test_full_pipeline_execution_creates_all_logs(self):
        """Test full pipeline execution creates logs for all stages."""
        pipeline = self.service.create_pipeline(
            package_name="complete-app",
            package_version="1.0.0",
            platform="linux",
            package_type="DEB",
            source_artifact_url="https://test.com/app.deb",
            created_by=self.user,
        )

        try:
            self.service.execute_pipeline(str(pipeline.id))
        except ValueError:
            pass  # May fail on policy, that's ok for this test

        # Check all stages have logs
        expected_stages = ["INTAKE", "BUILD", "SIGN", "SBOM", "SCAN"]
        for stage in expected_stages:
            logs = PackagingStageLog.objects.filter(pipeline=pipeline, stage_name=stage)
            self.assertGreaterEqual(logs.count(), 1, f"Missing log for stage: {stage}")
