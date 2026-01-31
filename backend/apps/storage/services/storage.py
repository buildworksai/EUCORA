# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unified storage service with failover support.

Provides a single interface for storage operations with automatic failover
to healthy providers.
"""
import logging
import time
from typing import BinaryIO, Optional

from .base import HealthCheckResult, StorageBackend, StorageObject, StorageResult

# Lazy imports for optional backends
MinIOBackend = None
AWSS3Backend = None
AzureBlobBackend = None

try:
    from .minio import MinIOBackend
except ImportError:
    pass

try:
    from .s3 import AWSS3Backend
except ImportError:
    pass

try:
    from .azure import AzureBlobBackend
except ImportError:
    pass

try:
    from ..models import StorageProvider
except ImportError:
    # For type hints
    pass

logger = logging.getLogger(__name__)


class StorageUnavailableError(Exception):
    """Raised when no healthy storage providers are available."""


class TransientError(Exception):
    """Raised for transient storage errors that can be retried."""


class StorageService:
    """
    Unified storage service with failover support.

    Automatically routes requests to healthy providers and fails over
    if the primary provider is unavailable.
    """

    def __init__(self):
        """Initialize storage service."""
        self._backends: dict[str, StorageBackend] = {}
        self._primary_id: Optional[str] = None

    def _load_backends(self):
        """Load all enabled storage providers as backends."""
        providers = StorageProvider.objects.filter(is_enabled=True).select_related(
            "minio_config", "s3_config", "azure_config"
        )

        self._backends = {}
        self._primary_id = None

        for provider in providers:
            backend = self._create_backend(provider)
            if backend:
                self._backends[str(provider.id)] = backend
                if provider.is_primary:
                    self._primary_id = str(provider.id)

    def _create_backend(self, provider: "StorageProvider") -> Optional[StorageBackend]:  # noqa: C901
        """Create backend instance for provider."""
        try:
            if provider.provider_type == StorageProvider.ProviderType.MINIO:
                if MinIOBackend is None:
                    logger.warning("MinIO backend not available - minio package not installed")
                    return None
                if hasattr(provider, "minio_config"):
                    return MinIOBackend(provider.minio_config)
            elif provider.provider_type == StorageProvider.ProviderType.AWS_S3:
                if AWSS3Backend is None:
                    logger.warning("AWS S3 backend not available - boto3 package not installed")
                    return None
                if hasattr(provider, "s3_config"):
                    return AWSS3Backend(provider.s3_config)
            elif provider.provider_type == StorageProvider.ProviderType.AZURE_BLOB:
                if AzureBlobBackend is None:
                    logger.warning("Azure Blob backend not available - azure-storage-blob package not installed")
                    return None
                if hasattr(provider, "azure_config"):
                    return AzureBlobBackend(provider.azure_config)
        except Exception as e:
            logger.error(f"Failed to create backend for {provider.name}: {e}")
            return None

        return None

    def _get_backends_by_priority(self) -> list[StorageBackend]:
        """Get backends sorted by priority."""
        if not self._backends:
            self._load_backends()

        providers = StorageProvider.objects.filter(id__in=list(self._backends.keys()), is_enabled=True).order_by(
            "priority"
        )

        return [self._backends[str(p.id)] for p in providers if str(p.id) in self._backends]

    def get_backend(self, provider_id: Optional[str] = None) -> StorageBackend:
        """
        Get storage backend, with failover if primary fails.

        Args:
            provider_id: Optional specific provider ID

        Returns:
            StorageBackend instance

        Raises:
            StorageUnavailableError: If no healthy providers available
        """
        if not self._backends:
            self._load_backends()

        if provider_id:
            if provider_id not in self._backends:
                raise StorageUnavailableError(f"Provider {provider_id} not found")
            return self._backends[provider_id]

        # Try primary first
        if self._primary_id and self._primary_id in self._backends:
            backend = self._backends[self._primary_id]
            health = backend.health_check()
            if health.is_healthy:
                return backend

        # Failover to next healthy provider
        for backend in self._get_backends_by_priority():
            health = backend.health_check()
            if health.is_healthy:
                return backend

        raise StorageUnavailableError("No healthy storage providers available")

    def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        provider_id: Optional[str] = None,
    ) -> StorageResult:
        """
        Upload file with automatic retry and failover.

        Args:
            path: Object path/key
            file: File-like object
            content_type: MIME type
            metadata: Additional metadata
            provider_id: Optional specific provider

        Returns:
            StorageResult

        Raises:
            StorageUnavailableError: If all providers fail
        """
        backend = self.get_backend(provider_id)

        # Retry with exponential backoff
        for attempt in range(3):
            try:
                return backend.upload(path, file, content_type, metadata)
            except Exception as e:
                if attempt == 2:
                    # Last attempt failed - try failover if not using specific provider
                    if provider_id:
                        raise
                    # Try next provider
                    try:
                        next_backend = self.get_backend(None)
                        if next_backend != backend:
                            return next_backend.upload(path, file, content_type, metadata)
                    except StorageUnavailableError:
                        pass
                    raise StorageUnavailableError(f"Upload failed after retries: {e}") from e

                # Exponential backoff
                time.sleep(2**attempt)
                logger.warning(f"Upload attempt {attempt + 1} failed, retrying...")

        raise StorageUnavailableError("Upload failed after all retries")

    def download(self, path: str, provider_id: Optional[str] = None) -> bytes:
        """Download file with failover."""
        backend = self.get_backend(provider_id)

        try:
            return backend.download(path)
        except Exception as e:
            # Try failover if not using specific provider
            if not provider_id:
                try:
                    next_backend = self.get_backend(None)
                    if next_backend != backend:
                        return next_backend.download(path)
                except StorageUnavailableError:
                    pass
            raise StorageUnavailableError(f"Download failed: {e}") from e

    def delete(self, path: str, provider_id: Optional[str] = None) -> bool:
        """Delete file with failover."""
        backend = self.get_backend(provider_id)

        try:
            return backend.delete(path)
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def exists(self, path: str, provider_id: Optional[str] = None) -> bool:
        """Check if file exists."""
        backend = self.get_backend(provider_id)
        return backend.exists(path)

    def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET",
        provider_id: Optional[str] = None,
    ) -> str:
        """Generate presigned URL."""
        backend = self.get_backend(provider_id)
        return backend.get_presigned_url(path, expires_in, method)

    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
        provider_id: Optional[str] = None,
    ) -> list[StorageObject]:
        """List objects."""
        backend = self.get_backend(provider_id)
        return backend.list_objects(prefix, max_keys)

    def health_check(self, provider_id: Optional[str] = None) -> HealthCheckResult:
        """Check storage health."""
        try:
            backend = self.get_backend(provider_id)
            return backend.health_check()
        except StorageUnavailableError as e:
            return HealthCheckResult(
                is_healthy=False,
                message=str(e),
                error=str(e),
            )


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get singleton storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
