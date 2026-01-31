# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for workflow API endpoints.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai_agents.models import AIAgentType
from apps.ai_agents.workflows.models import WorkflowDefinition, WorkflowExecution


class WorkflowAPITest(TestCase):
    """Test workflow API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass")
        self.client.force_authenticate(user=self.user)

        self.workflow_def = WorkflowDefinition.objects.create(
            agent_type=AIAgentType.PACKAGING_AGENT,
            name="Test Workflow",
            description="Test workflow",
            steps=[{"name": "Step 1", "type": "ai_action"}],
            required_policies=["application"],
            risk_level="R2",
        )

    def test_list_workflows(self):
        """Test listing workflow definitions."""
        response = self.client.get("/api/v1/ai/workflows/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data or [])

    def test_get_workflow_detail(self):
        """Test getting workflow definition detail."""
        response = self.client.get(f"/api/v1/ai/workflows/{self.workflow_def.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.workflow_def.id))

    def test_list_executions(self):
        """Test listing workflow executions."""
        WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.RUNNING,
        )

        response = self.client.get("/api/v1/ai/executions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_execution_detail(self):
        """Test getting workflow execution detail."""
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.RUNNING,
        )

        response = self.client.get(f"/api/v1/ai/executions/{execution.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(execution.id))

    def test_cancel_execution(self):
        """Test cancelling workflow execution."""
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.RUNNING,
        )

        response = self.client.post(f"/api/v1/ai/executions/{execution.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        execution.refresh_from_db()
        self.assertEqual(execution.status, WorkflowExecution.Status.CANCELLED)
