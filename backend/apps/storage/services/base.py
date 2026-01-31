# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Base storage backend interface.

All storage backends must implement this interface.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Optional


@dataclass
class StorageResult:
    """Result of storage operation."""

    path: str
    size: int
    etag: Optional[str] = None
    metadata: Optional[dict] = None


@dataclass
class StorageObject:
    """Storage object metadata."""

    path: str
    size: int
    last_modified: Optional[str] = None
    etag: Optional[str] = None


@dataclass
class HealthCheckResult:
    """Result of health check."""

    is_healthy: bool
    message: str
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(
        self,
        path: str,
        file: BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> StorageResult:
        """
        Upload file to storage.

        Args:
            path: Object path/key
            file: File-like object to upload
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            StorageResult with path, size, etag
        """

    @abstractmethod
    def download(self, path: str) -> bytes:
        """
        Download file from storage.

        Args:
            path: Object path/key

        Returns:
            File contents as bytes
        """

    @abstractmethod
    def delete(self, path: str) -> bool:
        """
        Delete file from storage.

        Args:
            path: Object path/key

        Returns:
            True if deleted, False if not found
        """

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check if file exists.

        Args:
            path: Object path/key

        Returns:
            True if exists, False otherwise
        """

    @abstractmethod
    def get_presigned_url(
        self,
        path: str,
        expires_in: int = 3600,
        method: str = "GET",
    ) -> str:
        """
        Generate presigned URL for direct access.

        Args:
            path: Object path/key
            expires_in: Expiration time in seconds
            method: HTTP method (GET, PUT, DELETE)

        Returns:
            Presigned URL string
        """

    @abstractmethod
    def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[StorageObject]:
        """
        List objects in storage.

        Args:
            prefix: Prefix to filter objects
            max_keys: Maximum number of objects to return

        Returns:
            List of StorageObject
        """

    @abstractmethod
    def health_check(self) -> HealthCheckResult:
        """
        Check storage health.

        Returns:
            HealthCheckResult with status and details
        """
