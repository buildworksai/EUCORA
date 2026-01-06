# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Additional tests for evidence_store storage to reach 90% coverage.
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from minio.error import S3Error
from apps.evidence_store.storage import MinIOStorage, get_storage


@pytest.mark.django_db
class TestMinIOStorageCoverage:
    """Additional tests for MinIOStorage coverage."""
    
    @patch('apps.evidence_store.storage.Minio')
    def test_get_storage_singleton(self, mock_minio):
        """Test that get_storage returns singleton instance."""
        from apps.evidence_store.storage import _storage
        # Reset singleton
        import apps.evidence_store.storage
        apps.evidence_store.storage._storage = None
        
        storage1 = get_storage()
        storage2 = get_storage()
        
        assert storage1 is storage2
    
    @patch('apps.evidence_store.storage.Minio')
    def test_upload_artifact_calculates_hash(self, mock_minio_class):
        """Test that upload_artifact calculates SHA-256 hash."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        storage = MinIOStorage()
        
        file_obj = BytesIO(b'test content')
        mock_client.put_object.return_value = None
        
        object_path, artifact_hash = storage.upload_artifact(
            file_obj, 'test-object', 'application/octet-stream'
        )
        
        assert artifact_hash is not None
        assert len(artifact_hash) == 64  # SHA-256 hex length
        assert object_path == f'{storage.bucket_name}/test-object'
    
    @patch('apps.evidence_store.storage.Minio')
    def test_get_artifact_url_generates_presigned_url(self, mock_minio_class):
        """Test that get_artifact_url generates presigned URL."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.presigned_get_object.return_value = 'https://example.com/presigned-url'
        
        storage = MinIOStorage()
        url = storage.get_artifact_url('test-object', 3600)
        
        assert url == 'https://example.com/presigned-url'
        mock_client.presigned_get_object.assert_called_once()
    
    @patch('apps.evidence_store.storage.Minio')
    def test_delete_artifact_removes_object(self, mock_minio_class):
        """Test that delete_artifact removes object from MinIO."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        
        storage = MinIOStorage()
        storage.delete_artifact('test-object')
        
        mock_client.remove_object.assert_called_once_with(
            storage.bucket_name, 'test-object'
        )
    
    @patch('apps.evidence_store.storage.Minio')
    def test_upload_artifact_handles_s3_error(self, mock_minio_class):
        """Test that upload_artifact raises S3Error on failure."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        mock_client.put_object.side_effect = S3Error('Upload failed')
        
        storage = MinIOStorage()
        file_obj = BytesIO(b'test content')
        
        with pytest.raises(S3Error):
            storage.upload_artifact(file_obj, 'test-object')

