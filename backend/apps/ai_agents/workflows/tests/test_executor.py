# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for WorkflowExecutor service.
"""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.ai_agents.models import AIAgentType
from apps.ai_agents.workflows.executor import WorkflowExecutor
from apps.ai_agents.workflows.models import WorkflowDefinition, WorkflowExecution


class WorkflowExecutorTest(TestCase):
    """Test WorkflowExecutor service."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.workflow_def = WorkflowDefinition.objects.create(
            agent_type=AIAgentType.PACKAGING_AGENT,
            name="Test Workflow",
            description="Test workflow",
            steps=[
                {
                    "name": "Step 1",
                    "type": "ai_action",
                    "description": "First step",
                    "instructions": "Do something",
                    "task": "Complete step",
                }
            ],
            required_policies=["application"],
            risk_level="R1",
        )

    @patch("apps.ai_agents.workflows.executor.PolicyContextRetriever")
    @patch("apps.ai_agents.workflows.executor.get_ai_agent_service")
    def test_start_workflow(self, mock_service, mock_retriever_class):
        """Test starting a workflow execution."""
        # Mock policy retriever
        mock_retriever = Mock()
        mock_retriever.get_context.return_value = []
        mock_retriever_class.return_value = mock_retriever

        # Mock AI service
        mock_provider = AsyncMock()
        mock_provider.chat = AsyncMock(return_value="Test response")
        mock_provider.count_tokens = Mock(return_value=100)
        mock_ai_service = Mock()
        mock_ai_service.get_provider.return_value = mock_provider
        mock_service.return_value = mock_ai_service

        executor = WorkflowExecutor(policy_retriever=mock_retriever)

        # Start workflow
        execution = asyncio.run(
            executor.start_workflow(
                workflow=self.workflow_def,
                user=self.user,
                input_data={"package_name": "test"},
            )
        )

        self.assertIsNotNone(execution)
        self.assertEqual(execution.workflow, self.workflow_def)
        self.assertEqual(execution.initiated_by, self.user)
        self.assertEqual(execution.status, WorkflowExecution.Status.COMPLETED)

    @patch("apps.ai_agents.workflows.executor.PolicyContextRetriever")
    def test_approve_step(self, mock_retriever_class):
        """Test approving a workflow step."""
        mock_retriever = Mock()
        mock_retriever.get_context.return_value = []
        mock_retriever_class.return_value = mock_retriever

        executor = WorkflowExecutor(policy_retriever=mock_retriever)

        execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.AWAITING_APPROVAL,
        )

        # Approve step
        updated_execution = asyncio.run(
            executor.approve_step(execution=execution, approver=self.user, notes="Approved")
        )

        self.assertEqual(updated_execution.approved_by, self.user)
        self.assertIsNotNone(updated_execution.approved_at)

    @patch("apps.ai_agents.workflows.executor.PolicyContextRetriever")
    def test_reject_step(self, mock_retriever_class):
        """Test rejecting a workflow step."""
        mock_retriever = Mock()
        mock_retriever.get_context.return_value = []
        mock_retriever_class.return_value = mock_retriever

        executor = WorkflowExecutor(policy_retriever=mock_retriever)

        execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.AWAITING_APPROVAL,
        )

        # Reject step
        updated_execution = asyncio.run(
            executor.reject_step(execution=execution, rejector=self.user, reason="Not approved")
        )

        self.assertEqual(updated_execution.status, WorkflowExecution.Status.REJECTED)
        self.assertEqual(updated_execution.rejection_reason, "Not approved")
