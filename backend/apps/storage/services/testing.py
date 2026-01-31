# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Storage connection testing service.

Provides comprehensive connection testing for storage providers.
"""
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from .storage import get_storage_service

try:
    from ..models import StorageProvider
except ImportError:
    # For type hints
    pass


@dataclass
class ConnectionTestResult:
    """Result of connection test."""

    success: bool
    message: str
    tests: list["TestResult"]
    latency_ms: Optional[float] = None


@dataclass
class TestResult:
    """Result of individual test."""

    name: str
    success: bool
    message: str
    latency_ms: Optional[float] = None


class StorageConnectionTester:
    """Test storage provider connections."""

    def __init__(self):
        """Initialize connection tester."""
        self.storage_service = get_storage_service()

    def test_connection(self, provider: "StorageProvider") -> ConnectionTestResult:
        """
        Run comprehensive connection test.

        Tests:
        1. Basic connectivity
        2. Authentication
        3. Bucket/container access
        4. Write permission
        5. Read permission
        6. Delete permission

        Args:
            provider: StorageProvider to test

        Returns:
            ConnectionTestResult with all test results
        """
        start_time = time.time()
        tests = []

        # Test 1: Basic connectivity
        tests.append(self._test_connectivity(provider))

        if not tests[-1].success:
            latency_ms = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                message="Basic connectivity failed",
                tests=tests,
                latency_ms=latency_ms,
            )

        # Test 2: Authentication
        tests.append(self._test_authentication(provider))

        if not tests[-1].success:
            latency_ms = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                message="Authentication failed",
                tests=tests,
                latency_ms=latency_ms,
            )

        # Test 3: Bucket/container access
        tests.append(self._test_bucket_access(provider))

        # Test 4: Write permission
        tests.append(self._test_write_permission(provider))

        # Test 5: Read permission
        tests.append(self._test_read_permission(provider))

        # Test 6: Delete permission
        tests.append(self._test_delete_permission(provider))

        latency_ms = (time.time() - start_time) * 1000
        success = all(t.success for t in tests)

        return ConnectionTestResult(
            success=success,
            message="All tests passed" if success else "Some tests failed",
            tests=tests,
            latency_ms=latency_ms,
        )

    def _test_connectivity(self, provider: "StorageProvider") -> TestResult:
        """Test basic connectivity."""
        start_time = time.time()
        try:
            backend = self.storage_service._create_backend(provider)
            if backend is None:
                return TestResult(
                    name="Connectivity",
                    success=False,
                    message="Failed to create backend",
                )

            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Connectivity",
                success=True,
                message="Connection established",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Connectivity",
                success=False,
                message=f"Connection failed: {str(e)}",
                latency_ms=latency_ms,
            )

    def _test_authentication(self, provider: "StorageProvider") -> TestResult:
        """Test authentication."""
        start_time = time.time()
        try:
            backend = self.storage_service._create_backend(provider)
            if backend is None:
                return TestResult(
                    name="Authentication",
                    success=False,
                    message="Backend not created",
                )

            # Try health check (requires auth)
            health = backend.health_check()
            latency_ms = (time.time() - start_time) * 1000

            return TestResult(
                name="Authentication",
                success=health.is_healthy,
                message=health.message,
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Authentication",
                success=False,
                message=f"Authentication failed: {str(e)}",
                latency_ms=latency_ms,
            )

    def _test_bucket_access(self, provider: "StorageProvider") -> TestResult:
        """Test bucket/container access."""
        start_time = time.time()
        try:
            backend = self.storage_service._create_backend(provider)
            if backend is None:
                return TestResult(
                    name="Bucket Access",
                    success=False,
                    message="Backend not created",
                )

            # Try listing objects (requires bucket access)
            backend.list_objects(prefix="", max_keys=1)
            latency_ms = (time.time() - start_time) * 1000

            return TestResult(
                name="Bucket Access",
                success=True,
                message="Bucket/container accessible",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Bucket Access",
                success=False,
                message=f"Bucket access failed: {str(e)}",
                latency_ms=latency_ms,
            )

    def _test_write_permission(self, provider: "StorageProvider") -> TestResult:
        """Test write permission."""
        start_time = time.time()
        test_path = f"_eucora_test_{uuid.uuid4().hex[:8]}.txt"
        test_content = b"EUCORA connection test"

        try:
            backend = self.storage_service._create_backend(provider)
            if backend is None:
                return TestResult(
                    name="Write Permission",
                    success=False,
                    message="Backend not created",
                )

            from io import BytesIO

            result = backend.upload(  # noqa: F841
                path=test_path,
                file=BytesIO(test_content),
                content_type="text/plain",
            )

            latency_ms = (time.time() - start_time) * 1000

            # Cleanup will happen in delete test
            return TestResult(
                name="Write Permission",
                success=True,
                message=f"Write successful (path: {test_path})",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Write Permission",
                success=False,
                message=f"Write failed: {str(e)}",
                latency_ms=latency_ms,
            )

    def _test_read_permission(self, provider: "StorageProvider") -> TestResult:
        """Test read permission."""
        start_time = time.time()
        # Find test file from write test
        test_path = None
        try:
            backend = self.storage_service._create_backend(provider)
            if backend is None:
                return TestResult(
                    name="Read Permission",
                    success=False,
                    message="Backend not created",
                )

            # List test files
            objects = backend.list_objects(prefix="_eucora_test_", max_keys=10)
            if not objects:
                return TestResult(
                    name="Read Permission",
                    success=False,
                    message="No test file found (write test may have failed)",
                )

            test_path = objects[0].path
            data = backend.download(test_path)  # noqa: F841

            latency_ms = (time.time() - start_time) * 1000

            return TestResult(
                name="Read Permission",
                success=True,
                message=f"Read successful (path: {test_path})",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Read Permission",
                success=False,
                message=f"Read failed: {str(e)}",
                latency_ms=latency_ms,
            )

    def _test_delete_permission(self, provider: "StorageProvider") -> TestResult:
        """Test delete permission and cleanup test files."""
        start_time = time.time()
        try:
            backend = self.storage_service._create_backend(provider)
            if backend is None:
                return TestResult(
                    name="Delete Permission",
                    success=False,
                    message="Backend not created",
                )

            # Find and delete test files
            objects = backend.list_objects(prefix="_eucora_test_", max_keys=10)
            deleted_count = 0

            for obj in objects:
                if backend.delete(obj.path):
                    deleted_count += 1

            latency_ms = (time.time() - start_time) * 1000

            return TestResult(
                name="Delete Permission",
                success=True,
                message=f"Delete successful (cleaned up {deleted_count} test files)",
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return TestResult(
                name="Delete Permission",
                success=False,
                message=f"Delete failed: {str(e)}",
                latency_ms=latency_ms,
            )
