# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
MinIO storage backend for evidence artifacts.
"""
from minio import Minio
from minio.error import S3Error
from django.conf import settings
import hashlib
import logging
from typing import BinaryIO, Tuple

logger = logging.getLogger(__name__)


class MinIOStorage:
    """MinIO storage client for artifact management."""
    
    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f'Created MinIO bucket: {self.bucket_name}')
        except S3Error as e:
            logger.error(f'Failed to create bucket: {e}')
            raise
    
    def upload_artifact(self, file_obj: BinaryIO, object_name: str, content_type: str = 'application/octet-stream') -> Tuple[str, str]:
        """
        Upload artifact to MinIO and return path and hash.
        
        Args:
            file_obj: File object to upload
            object_name: Object name in MinIO (e.g., 'artifacts/app-v1.0.0.msi')
            content_type: MIME type of the file
        
        Returns:
            Tuple of (object_path, sha256_hash)
        
        Raises:
            S3Error: If upload fails
        """
        # Calculate SHA-256 hash
        file_obj.seek(0)
        sha256_hash = hashlib.sha256()
        for chunk in iter(lambda: file_obj.read(8192), b''):
            sha256_hash.update(chunk)
        artifact_hash = sha256_hash.hexdigest()
        
        # Reset file pointer
        file_obj.seek(0)
        
        # Upload to MinIO
        try:
            file_size = file_obj.seek(0, 2)  # Seek to end to get size
            file_obj.seek(0)  # Reset to beginning
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_obj,
                length=file_size,
                content_type=content_type,
            )
            
            object_path = f'{self.bucket_name}/{object_name}'
            logger.info(
                f'Uploaded artifact to MinIO: {object_path}',
                extra={'object_path': object_path, 'hash': artifact_hash}
            )
            
            return object_path, artifact_hash
            
        except S3Error as e:
            logger.error(f'Failed to upload artifact: {e}')
            raise
    
    def get_artifact_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        Get presigned URL for artifact download.
        
        Args:
            object_name: Object name in MinIO
            expires_seconds: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            Presigned URL string
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires_seconds,
            )
            return url
        except S3Error as e:
            logger.error(f'Failed to generate presigned URL: {e}')
            raise
    
    def delete_artifact(self, object_name: str):
        """
        Delete artifact from MinIO.
        
        Args:
            object_name: Object name in MinIO
        
        Raises:
            S3Error: If deletion fails
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f'Deleted artifact from MinIO: {object_name}')
        except S3Error as e:
            logger.error(f'Failed to delete artifact: {e}')
            raise


# Singleton instance
_storage = None


def get_storage() -> MinIOStorage:
    """Get MinIO storage singleton instance."""
    global _storage
    if _storage is None:
        _storage = MinIOStorage()
    return _storage
