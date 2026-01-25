# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for task status API endpoints.

Verifies:
- Task status querying
- Task revocation
- Active task listing
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class TestGetTaskStatus(APITestCase):
    """Test get_task_status endpoint."""

    def setUp(self):
        """Set up test client and user."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("apps.core.views_tasks.AsyncResult")
    def test_get_task_status_pending(self, mock_async_result):
        """Should return PENDING status for new task."""
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        mock_result.result = None
        mock_async_result.return_value = mock_result

        response = self.client.get("/api/v1/admin/tasks/test-task-id/status")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["task_id"] == "test-task-id"
        assert response.data["status"] == "PENDING"

    @patch("apps.core.views_tasks.AsyncResult")
    def test_get_task_status_success(self, mock_async_result):
        """Should return SUCCESS status with result."""
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = {"data": "test"}
        mock_async_result.return_value = mock_result

        response = self.client.get("/api/v1/admin/tasks/test-task-id/status")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "SUCCESS"
        assert response.data["result"] == {"data": "test"}

    @patch("apps.core.views_tasks.AsyncResult")
    def test_get_task_status_failure(self, mock_async_result):
        """Should return FAILURE status with error."""
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.result = Exception("Test error")
        mock_result.traceback = "Test traceback"
        mock_async_result.return_value = mock_result

        response = self.client.get("/api/v1/admin/tasks/test-task-id/status")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "FAILURE"
        assert "Test error" in response.data["error"]

    def test_get_task_status_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()

        response = self.client.get("/api/v1/admin/tasks/test-task-id/status")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRevokeTask(APITestCase):
    """Test revoke_task endpoint."""

    def setUp(self):
        """Set up test client and user."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user, created = User.objects.get_or_create(username="testuser2", defaults={"email": "test2@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("apps.core.views_tasks.AsyncResult")
    def test_revoke_task(self, mock_async_result):
        """Should revoke a task."""
        mock_result = MagicMock()
        mock_async_result.return_value = mock_result

        response = self.client.post("/api/v1/admin/tasks/test-task-id/revoke")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "REVOKED"
        mock_result.revoke.assert_called_once()

    @patch("apps.core.views_tasks.AsyncResult")
    def test_revoke_task_with_terminate(self, mock_async_result):
        """Should pass terminate option."""
        mock_result = MagicMock()
        mock_async_result.return_value = mock_result

        response = self.client.post(
            "/api/v1/admin/tasks/test-task-id/revoke", data={"terminate": True, "signal": "SIGKILL"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        mock_result.revoke.assert_called_once_with(terminate=True, signal="SIGKILL")


class TestGetActiveTasks(APITestCase):
    """Test get_active_tasks endpoint."""

    def setUp(self):
        """Set up test client and user."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user, created = User.objects.get_or_create(username="testuser3", defaults={"email": "test3@example.com"})

        if created:

            self.user.set_password("testpass123")

            self.user.save()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("apps.core.views_tasks.celery_app")
    def test_get_active_tasks(self, mock_celery_app):
        """Should return active tasks."""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {"worker1": []}
        mock_inspect.reserved.return_value = {"worker1": []}
        mock_inspect.scheduled.return_value = {"worker1": []}
        mock_celery_app.control.inspect.return_value = mock_inspect

        response = self.client.get("/api/v1/admin/tasks/active")

        assert response.status_code == status.HTTP_200_OK
        assert "active" in response.data
        assert "summary" in response.data
