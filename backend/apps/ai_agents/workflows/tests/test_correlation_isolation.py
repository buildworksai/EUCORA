# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for correlation ID isolation in workflow executions.

MANDATORY: All Django apps must have correlation ID isolation tests.
"""
from django.contrib.auth.models import User
from django.test import TestCase

from apps.ai_agents.models import AIAgentType
from apps.ai_agents.workflows.models import WorkflowDefinition, WorkflowExecution


class WorkflowCorrelationIsolationTest(TestCase):
    """Test correlation ID isolation for workflow executions."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.workflow_def = WorkflowDefinition.objects.create(
            agent_type=AIAgentType.PACKAGING_AGENT,
            name="Test Workflow",
            description="Test",
            steps=[{"name": "Step 1", "type": "ai_action"}],
            risk_level="R2",
        )

    def test_correlation_id_uniqueness(self):
        """Test that each execution has a unique correlation ID."""
        execution1 = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.PENDING,
        )
        execution2 = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.PENDING,
        )

        self.assertNotEqual(execution1.correlation_id, execution2.correlation_id)

    def test_correlation_id_filtering(self):
        """Test filtering executions by correlation ID."""
        execution1 = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.PENDING,
        )
        _execution2 = WorkflowExecution.objects.create(  # noqa: F841
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.PENDING,
        )

        # Filter by correlation_id
        filtered = WorkflowExecution.objects.filter(correlation_id=execution1.correlation_id)
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first(), execution1)
