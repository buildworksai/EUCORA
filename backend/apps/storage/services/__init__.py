# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Storage services package.

Provides lazy imports for storage backends to avoid import errors
when optional dependencies (boto3, azure-storage-blob) are not installed.
"""
import logging

logger = logging.getLogger(__name__)

# Base classes - always available
from .base import HealthCheckResult, StorageBackend, StorageObject, StorageResult  # noqa: E402

# Core service - always available
from .storage import StorageService, StorageUnavailableError, get_storage_service  # noqa: E402
from .testing import ConnectionTestResult, StorageConnectionTester, TestResult  # noqa: E402

# Lazy imports for backend implementations
# These only fail when actually instantiated, not at module import time
MinIOBackend = None
AWSS3Backend = None
AzureBlobBackend = None

try:
    from .minio import MinIOBackend
except ImportError as e:
    logger.warning(f"MinIO backend not available: {e}")

try:
    from .s3 import AWSS3Backend
except ImportError as e:
    logger.warning(f"AWS S3 backend not available: {e}")

try:
    from .azure import AzureBlobBackend
except ImportError as e:
    logger.warning(f"Azure Blob backend not available: {e}")

__all__ = [
    "StorageBackend",
    "StorageResult",
    "StorageObject",
    "HealthCheckResult",
    "MinIOBackend",
    "AWSS3Backend",
    "AzureBlobBackend",
    "StorageService",
    "StorageUnavailableError",
    "get_storage_service",
    "StorageConnectionTester",
    "ConnectionTestResult",
    "TestResult",
]
