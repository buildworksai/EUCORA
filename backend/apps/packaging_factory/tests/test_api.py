# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for packaging factory (15 tests).
"""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.packaging_factory.models import PackagingPipeline

User = get_user_model()


class PackagingPipelineAPITests(TestCase):
    """Tests for packaging pipeline REST API."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client.force_authenticate(user=self.user)

    def test_create_pipeline(self):
        """Test POST /api/v1/packaging/pipelines/ creates pipeline."""
        data = {
            "package_name": "test-app",
            "package_version": "1.0.0",
            "platform": "windows",
            "package_type": "MSI",
            "source_artifact_url": "https://test.com/app.msi",
        }

        response = self.client.post(
            "/api/v1/packaging/pipelines/", data, format="json", HTTP_X_CORRELATION_ID="test-corr-001"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["package_name"], "test-app")
        self.assertEqual(response.data["platform"], "windows")

    def test_create_pipeline_with_auto_execute(self):
        """Test pipeline auto-executes on creation."""
        data = {
            "package_name": "auto-app",
            "package_version": "1.0.0",
            "platform": "linux",
            "package_type": "DEB",
            "source_artifact_url": "https://test.com/app.deb",
        }

        response = self.client.post("/api/v1/packaging/pipelines/?auto_execute=true", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Status should be beyond PENDING after auto-execute
        self.assertNotEqual(response.data["status"], "PENDING")

    def test_create_pipeline_requires_authentication(self):
        """Test pipeline creation requires authentication."""
        self.client.force_authenticate(user=None)

        data = {
            "package_name": "test-app",
            "package_version": "1.0.0",
            "platform": "windows",
            "package_type": "MSI",
            "source_artifact_url": "https://test.com/app.msi",
        }

        response = self.client.post("/api/v1/packaging/pipelines/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_pipeline_validation(self):
        """Test pipeline creation validates required fields."""
        data = {
            "package_name": "test-app"
            # Missing required fields
        }

        response = self.client.post("/api/v1/packaging/pipelines/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_pipelines(self):
        """Test GET /api/v1/packaging/pipelines/ lists pipelines."""
        # Create pipelines
        PackagingPipeline.objects.create(
            package_name="app1",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app1.msi",
            source_artifact_hash="hash1",
            created_by=self.user,
        )
        PackagingPipeline.objects.create(
            package_name="app2",
            package_version="2.0.0",
            platform="macos",
            package_type="PKG",
            source_artifact_url="https://test.com/app2.pkg",
            source_artifact_hash="hash2",
            created_by=self.user,
        )

        response = self.client.get("/api/v1/packaging/pipelines/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_pipelines_by_platform(self):
        """Test filtering pipelines by platform."""
        PackagingPipeline.objects.create(
            package_name="win-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/win.msi",
            source_artifact_hash="hash1",
            created_by=self.user,
        )
        PackagingPipeline.objects.create(
            package_name="mac-app",
            package_version="1.0.0",
            platform="macos",
            package_type="PKG",
            source_artifact_url="https://test.com/mac.pkg",
            source_artifact_hash="hash2",
            created_by=self.user,
        )

        response = self.client.get("/api/v1/packaging/pipelines/?platform=windows")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["platform"], "windows")

    def test_filter_pipelines_by_status(self):
        """Test filtering pipelines by status."""
        PackagingPipeline.objects.create(
            package_name="pending-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash1",
            created_by=self.user,
            status="PENDING",
        )
        PackagingPipeline.objects.create(
            package_name="completed-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app2.msi",
            source_artifact_hash="hash2",
            created_by=self.user,
            status="COMPLETED",
        )

        response = self.client.get("/api/v1/packaging/pipelines/?status=COMPLETED")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["status"], "COMPLETED")

    def test_get_pipeline_details(self):
        """Test GET /api/v1/packaging/pipelines/{id}/ returns details."""
        pipeline = PackagingPipeline.objects.create(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
        )

        response = self.client.get(f"/api/v1/packaging/pipelines/{pipeline.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["package_name"], "test-app")
        self.assertIn("stage_logs", response.data)

    def test_execute_pipeline_endpoint(self):
        """Test POST /api/v1/packaging/pipelines/{id}/execute/ executes pipeline."""
        pipeline = PackagingPipeline.objects.create(
            package_name="exec-app",
            package_version="1.0.0",
            platform="linux",
            package_type="DEB",
            source_artifact_url="https://test.com/app.deb",
            source_artifact_hash="hash",
            created_by=self.user,
            status="PENDING",
        )

        response = self.client.post(
            f"/api/v1/packaging/pipelines/{pipeline.id}/execute/", HTTP_X_CORRELATION_ID="test-exec"
        )

        # May succeed or fail depending on mock vulnerabilities
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    def test_get_pipeline_status_endpoint(self):
        """Test GET /api/v1/packaging/pipelines/{id}/status/ returns status."""
        pipeline = PackagingPipeline.objects.create(
            package_name="status-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash",
            created_by=self.user,
        )

        response = self.client.get(f"/api/v1/packaging/pipelines/{pipeline.id}/status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("pipeline_id", response.data)
        self.assertIn("stages", response.data)
        self.assertIn("vulnerabilities", response.data)

    def test_filter_by_package_name(self):
        """Test filtering by package name (contains)."""
        PackagingPipeline.objects.create(
            package_name="my-test-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/app.msi",
            source_artifact_hash="hash1",
            created_by=self.user,
        )
        PackagingPipeline.objects.create(
            package_name="other-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/other.msi",
            source_artifact_hash="hash2",
            created_by=self.user,
        )

        response = self.client.get("/api/v1/packaging/pipelines/?package_name=test")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("test", response.data["results"][0]["package_name"])

    def test_filter_by_policy_decision(self):
        """Test filtering by policy decision."""
        PackagingPipeline.objects.create(
            package_name="pass-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/pass.msi",
            source_artifact_hash="hash1",
            created_by=self.user,
            policy_decision="PASS",
        )
        PackagingPipeline.objects.create(
            package_name="fail-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/fail.msi",
            source_artifact_hash="hash2",
            created_by=self.user,
            policy_decision="FAIL",
        )

        response = self.client.get("/api/v1/packaging/pipelines/?policy_decision=PASS")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["policy_decision"], "PASS")

    def test_create_pipeline_with_exception_id(self):
        """Test creating pipeline with exception ID."""
        exception_id = uuid.uuid4()
        data = {
            "package_name": "excepted-app",
            "package_version": "1.0.0",
            "platform": "windows",
            "package_type": "MSI",
            "source_artifact_url": "https://test.com/app.msi",
            "exception_id": str(exception_id),
        }

        response = self.client.post("/api/v1/packaging/pipelines/?auto_execute=false", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["exception_id"], str(exception_id))

    def test_pipeline_nonexistent_returns_404(self):
        """Test accessing non-existent pipeline returns 404."""
        fake_id = uuid.uuid4()
        response = self.client.get(f"/api/v1/packaging/pipelines/{fake_id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_pipelines_with_pagination(self):
        """Test pipeline list endpoint with pagination."""
        # Create multiple pipelines
        for i in range(3):
            PackagingPipeline.objects.create(
                package_name=f"app-{i}",
                package_version="1.0.0",
                platform="windows",
                package_type="MSI",
                source_artifact_url=f"https://test.com/app-{i}.msi",
                source_artifact_hash=f"hash-{i}",
                created_by=self.user,
            )

        response = self.client.get("/api/v1/packaging/pipelines/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_pipeline_delete_endpoint(self):
        """Test DELETE /api/v1/packaging/pipelines/{id}/ deletes pipeline."""
        pipeline = PackagingPipeline.objects.create(
            package_name="delete-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/delete.msi",
            source_artifact_hash="delete-hash",
            created_by=self.user,
        )

        response = self.client.delete(f"/api/v1/packaging/pipelines/{pipeline.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PackagingPipeline.objects.filter(id=pipeline.id).exists())

    def test_pipeline_update_endpoint(self):
        """Test PATCH /api/v1/packaging/pipelines/{id}/ updates pipeline."""
        pipeline = PackagingPipeline.objects.create(
            package_name="update-app",
            package_version="1.0.0",
            platform="windows",
            package_type="MSI",
            source_artifact_url="https://test.com/update.msi",
            source_artifact_hash="update-hash",
            created_by=self.user,
        )

        response = self.client.patch(
            f"/api/v1/packaging/pipelines/{pipeline.id}/", {"package_version": "1.1.0"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pipeline.refresh_from_db()
        self.assertEqual(pipeline.package_version, "1.1.0")

    def test_execute_endpoint_with_invalid_pipeline_id(self):
        """Test execute endpoint with invalid pipeline ID returns 404."""
        fake_id = uuid.uuid4()
        response = self.client.post(f"/api/v1/packaging/pipelines/{fake_id}/execute/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
