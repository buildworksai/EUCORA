# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for evidence_store views and storage.
"""
from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from apps.evidence_store.models import EvidencePack
from apps.evidence_store.views import _validate_evidence_pack


@pytest.mark.django_db
class TestEvidenceStoreViews:
    """Test evidence store view endpoints."""

    def test_get_evidence_pack(self, authenticated_client, sample_evidence_pack):
        """Test retrieving an evidence pack."""
        url = f"/api/v1/evidence/{sample_evidence_pack.correlation_id}/"
        response = authenticated_client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["app_name"] == "TestApp"
        assert data["version"] == "1.0.0"
        assert data["is_validated"] is True

    @patch("apps.evidence_store.storage.get_storage")
    def test_upload_evidence_pack(self, mock_get_storage, authenticated_client):
        """Test uploading evidence pack with artifact."""
        # Mock storage
        mock_storage = MagicMock()
        mock_storage.upload_artifact.return_value = ("artifacts/test/1.0.0/test.msi", "abc123hash")
        mock_get_storage.return_value = mock_storage

        # Create test file
        test_file = BytesIO(b"test file content")
        test_file.name = "test.msi"

        url = "/api/v1/evidence/"
        response = authenticated_client.post(
            url,
            {
                "app_name": "TestApp",
                "version": "1.0.0",
                "artifact": test_file,
                "sbom_data": '{"packages": [{"name": "test"}]}',
                "vulnerability_scan_results": '{"critical": 0, "high": 0}',
                "rollback_plan": "Test rollback plan with sufficient detail to pass validation",
            },
            format="multipart",
        )

        assert response.status_code in [201, 200]

    def test_upload_evidence_pack_missing_fields(self, authenticated_client):
        """Test uploading evidence pack with missing required fields."""
        url = "/api/v1/evidence/"
        response = authenticated_client.post(
            url,
            {
                "app_name": "TestApp",
            },
            format="multipart",
        )

        assert response.status_code == 400
        assert "error" in response.data

    @patch("apps.evidence_store.storage.get_storage")
    def test_upload_evidence_pack_with_vulnerabilities(self, mock_get_storage, authenticated_client):
        """Test uploading evidence pack with critical vulnerabilities."""
        # Mock storage
        mock_storage = MagicMock()
        mock_storage.upload_artifact.return_value = ("artifacts/test/1.0.0/test.msi", "abc123hash")
        mock_get_storage.return_value = mock_storage

        # Create test file
        test_file = BytesIO(b"test file content")
        test_file.name = "test.msi"

        url = "/api/v1/evidence/"
        response = authenticated_client.post(
            url,
            {
                "app_name": "TestApp",
                "version": "1.0.0",
                "artifact": test_file,
                "sbom_data": '{"packages": [{"name": "test"}]}',
                "vulnerability_scan_results": '{"critical": 2, "high": 5}',
                "rollback_plan": "Test rollback plan with sufficient detail to pass validation",
            },
            format="multipart",
        )

        assert response.status_code == 201
        assert response.data["is_validated"] is False  # Should fail validation due to critical vulns

    @patch("apps.evidence_store.storage.get_storage")
    def test_upload_evidence_pack_invalid_json(self, mock_get_storage, authenticated_client):
        """Test uploading evidence pack with invalid JSON payloads."""
        mock_storage = MagicMock()
        mock_storage.upload_artifact.return_value = ("artifacts/test/1.0.0/test.msi", "abc123hash")
        mock_get_storage.return_value = mock_storage

        test_file = BytesIO(b"test file content")
        test_file.name = "test.msi"

        url = "/api/v1/evidence/"
        response = authenticated_client.post(
            url,
            {
                "app_name": "TestApp",
                "version": "1.0.0",
                "artifact": test_file,
                "sbom_data": '{"packages": [}',
                "vulnerability_scan_results": '{"critical": 0}',
                "rollback_plan": "Rollback plan with sufficient detail to pass validation",
            },
            format="multipart",
        )

        assert response.status_code == 400
        assert "error" in response.data

    @patch("apps.evidence_store.storage.get_storage")
    def test_upload_evidence_pack_storage_failure(self, mock_get_storage, authenticated_client):
        """Test upload failure when storage upload throws error."""
        mock_storage = MagicMock()
        mock_storage.upload_artifact.side_effect = Exception("upload failed")
        mock_get_storage.return_value = mock_storage

        test_file = BytesIO(b"test file content")
        test_file.name = "test.msi"

        url = "/api/v1/evidence/"
        response = authenticated_client.post(
            url,
            {
                "app_name": "TestApp",
                "version": "1.0.0",
                "artifact": test_file,
                "sbom_data": '{"packages": [{"name": "test"}]}',
                "vulnerability_scan_results": '{"critical": 0, "high": 0}',
                "rollback_plan": "Rollback plan with sufficient detail to pass validation",
            },
            format="multipart",
        )

        assert response.status_code == 500
        assert "error" in response.data

    def test_validate_evidence_pack_missing_sbom(self):
        """Test validation fails when SBOM data is missing."""
        assert _validate_evidence_pack({}, {"critical": 0}, "Valid rollback plan" * 5) is False

    def test_validate_evidence_pack_missing_vuln_results(self):
        """Test validation fails when vulnerability scan results are missing."""
        assert _validate_evidence_pack({"packages": [{"name": "test"}]}, {}, "Valid rollback plan" * 5) is False

    def test_validate_evidence_pack_short_rollback(self):
        """Test validation fails when rollback plan is too short."""
        assert _validate_evidence_pack({"packages": [{"name": "test"}]}, {"critical": 0}, "Too short") is False

    def test_validate_evidence_pack_high_vulnerabilities(self):
        """Test validation fails when high vulnerabilities exceed threshold."""
        assert (
            _validate_evidence_pack(
                {"packages": [{"name": "test"}]},
                {"critical": 0, "high": 6},
                "Valid rollback plan" * 5,
            )
            is False
        )

    def test_get_evidence_pack_not_found(self, authenticated_client):
        """Test getting non-existent evidence pack."""
        url = f"/api/v1/evidence/{uuid4()}/"
