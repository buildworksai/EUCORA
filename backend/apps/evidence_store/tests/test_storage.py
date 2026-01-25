# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Additional tests for evidence_store storage to reach 90% coverage.
"""
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error

from apps.evidence_store.storage import MinIOStorage


class TestMinIOStorage:
    """Test MinIO storage backend."""

    @patch("apps.evidence_store.storage.Minio")
    def test_init_creates_bucket(self, mock_minio_class):
        """Test MinIO storage initialization creates bucket if missing."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_minio_class.return_value = mock_client

        storage = MinIOStorage()

        mock_client.make_bucket.assert_called_once()

    @patch("apps.evidence_store.storage.Minio")
    def test_init_bucket_exists(self, mock_minio_class):
        """Test MinIO storage initialization when bucket exists."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client

        storage = MinIOStorage()

        mock_client.make_bucket.assert_not_called()

    @patch("apps.evidence_store.storage.Minio")
    def test_upload_artifact_success(self, mock_minio_class):
        """Test successful artifact upload."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client

        storage = MinIOStorage()

        # Create test file
        test_file = BytesIO(b"test content")

        path, hash_val = storage.upload_artifact(test_file, "test/artifact.msi")

        assert "test/artifact.msi" in path
        assert len(hash_val) == 64  # SHA-256 hash length
        mock_client.put_object.assert_called_once()

    @patch("apps.evidence_store.storage.Minio")
    def test_upload_artifact_failure(self, mock_minio_class):
        """Test artifact upload failure."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.put_object.side_effect = S3Error("Upload failed", None, None, None, None, None)
        mock_minio_class.return_value = mock_client

        storage = MinIOStorage()
        test_file = BytesIO(b"test content")

        with pytest.raises(S3Error):
            storage.upload_artifact(test_file, "test/artifact.msi")

    @patch("apps.evidence_store.storage.Minio")
    def test_get_artifact_url(self, mock_minio_class):
        """Test getting presigned URL."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = "https://minio/bucket/object?signature=abc"
        mock_minio_class.return_value = mock_client

        storage = MinIOStorage()
        url = storage.get_artifact_url("test/artifact.msi")

        assert "https://" in url
        mock_client.presigned_get_object.assert_called_once()

    @patch("apps.evidence_store.storage.Minio")
    def test_delete_artifact(self, mock_minio_class):
        """Test artifact deletion."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client

        storage = MinIOStorage()
        storage.delete_artifact("test/artifact.msi")

        mock_client.remove_object.assert_called_once()
