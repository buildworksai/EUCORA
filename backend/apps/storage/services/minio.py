# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
MinIO S3-compatible storage backend implementation.
"""
import time
from io import BytesIO
from typing import BinaryIO, Optional

from minio import Minio
from minio.error import S3Error

from .base import HealthCheckResult, StorageBackend, StorageObject, StorageResult

try:
    from ..models import MinIOConfig
except ImportError:
    # For type hints
    pass


class MinIOBackend(StorageBackend):
    """MinIO S3-compatible storage backend."""

    def __init__(self, config: "MinIOConfig"):
        """
        Initialize MinIO backend.

        Args:
            config: MinIOConfig instance
        """
        self.config = config
        endpoint = config.endpoint_url.replace("http://", "").replace("https://", "")
        self.client = Minio(
            endpoint=endpoint,
            access_key=config.access_key_id,
            secret_key=config.secret_access_key,
            secure=config.use_ssl,
        )
        self.bucket_name = config.bucket_name

    def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StorageResult:
        """Upload file to MinIO."""
        try:
            # Read file content
            file.seek(0)
            file_data = file.read()
            file_size = len(file_data)

            # Upload
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=path,
                data=BytesIO(file_data),
                length=file_size,
                content_type=content_type or "application/octet-stream",
                metadata=metadata or {},
            )

            return StorageResult(
                path=path,
                size=file_size,
                etag=result.etag if hasattr(result, "etag") else None,
                metadata=metadata,
            )
        except S3Error as e:
            raise Exception(f"MinIO upload failed: {e}") from e

    def download(self, path: str) -> bytes:
        """Download file from MinIO."""
        try:
            response = self.client.get_object(self.bucket_name, path)
            return response.read()
        except S3Error as e:
            if e.code == "NoSuchKey":
                raise FileNotFoundError(f"Object not found: {path}") from e
            raise Exception(f"MinIO download failed: {e}") from e
        finally:
            if "response" in locals():
                response.close()
                response.release_conn()

    def delete(self, path: str) -> bool:
        """Delete file from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, path)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            raise Exception(f"MinIO delete failed: {e}") from e

    def exists(self, path: str) -> bool:
        """Check if file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket_name, path)
            return True
        except S3Error:
            return False

    def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """Generate presigned URL for MinIO."""
        try:
            from datetime import timedelta

            if method == "GET":
                return self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=path,
                    expires=timedelta(seconds=expires_in),
                )
            elif method == "PUT":
                return self.client.presigned_put_object(
                    bucket_name=self.bucket_name,
                    object_name=path,
                    expires=timedelta(seconds=expires_in),
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
        except S3Error as e:
            raise Exception(f"MinIO presigned URL failed: {e}") from e

    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[StorageObject]:
        """List objects in MinIO."""
        try:
            objects = []
            for obj in self.client.list_objects(
                bucket_name=self.bucket_name,
                prefix=prefix,
                recursive=True,
            ):
                if len(objects) >= max_keys:
                    break
                objects.append(
                    StorageObject(
                        path=obj.object_name,
                        size=obj.size,
                        last_modified=obj.last_modified.isoformat() if obj.last_modified else None,
                        etag=obj.etag,
                    )
                )
            return objects
        except S3Error as e:
            raise Exception(f"MinIO list objects failed: {e}") from e

    def health_check(self) -> HealthCheckResult:
        """Check MinIO health."""
        start_time = time.time()
        try:
            # Try to list buckets (lightweight operation)
            buckets = self.client.list_buckets()
            latency_ms = (time.time() - start_time) * 1000

            # Check if our bucket exists
            bucket_exists = any(b.name == self.bucket_name for b in buckets)
            if not bucket_exists:
                return HealthCheckResult(
                    is_healthy=False,
                    message=f"Bucket {self.bucket_name} not found",
                    latency_ms=latency_ms,
                )

            return HealthCheckResult(
                is_healthy=True,
                message="MinIO is healthy",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                is_healthy=False,
                message=f"Health check failed: {str(e)}",
                latency_ms=latency_ms,
                error=str(e),
            )
