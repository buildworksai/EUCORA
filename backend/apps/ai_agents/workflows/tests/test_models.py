# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for workflow models.
"""
from django.contrib.auth.models import User
from django.test import TestCase

from apps.ai_agents.models import AIAgentType
from apps.ai_agents.workflows.models import WorkflowDefinition, WorkflowExecution, WorkflowStep


class WorkflowDefinitionModelTest(TestCase):
    """Test WorkflowDefinition model."""

    def setUp(self):
        self.workflow_def = WorkflowDefinition.objects.create(
            agent_type=AIAgentType.PACKAGING_AGENT,
            name="Test Workflow",
            description="Test workflow description",
            steps=[
                {"name": "Step 1", "type": "ai_action", "description": "First step"},
                {"name": "Step 2", "type": "approval_gate", "description": "Second step"},
            ],
            required_policies=["application", "security"],
            risk_level="R2",
        )

    def test_workflow_definition_creation(self):
        """Test workflow definition can be created."""
        self.assertEqual(self.workflow_def.agent_type, AIAgentType.PACKAGING_AGENT)
        self.assertEqual(self.workflow_def.name, "Test Workflow")
        self.assertEqual(len(self.workflow_def.steps), 2)
        self.assertEqual(self.workflow_def.risk_level, "R2")

    def test_workflow_definition_str(self):
        """Test workflow definition string representation."""
        self.assertIn("Test Workflow", str(self.workflow_def))
        self.assertIn("packaging", str(self.workflow_def))


class WorkflowExecutionModelTest(TestCase):
    """Test WorkflowExecution model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.workflow_def = WorkflowDefinition.objects.create(
            agent_type=AIAgentType.PACKAGING_AGENT,
            name="Test Workflow",
            description="Test",
            steps=[{"name": "Step 1", "type": "ai_action"}],
            risk_level="R2",
        )

    def test_workflow_execution_creation(self):
        """Test workflow execution can be created."""
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            input_data={"package_name": "test-package"},
            status=WorkflowExecution.Status.PENDING,
        )
        self.assertEqual(execution.workflow, self.workflow_def)
        self.assertEqual(execution.initiated_by, self.user)
        self.assertEqual(execution.status, WorkflowExecution.Status.PENDING)
        self.assertIsNotNone(execution.correlation_id)

    def test_workflow_execution_str(self):
        """Test workflow execution string representation."""
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.RUNNING,
        )
        self.assertIn("Test Workflow", str(execution))
        self.assertIn("running", str(execution))


class WorkflowStepModelTest(TestCase):
    """Test WorkflowStep model."""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.workflow_def = WorkflowDefinition.objects.create(
            agent_type=AIAgentType.PACKAGING_AGENT,
            name="Test Workflow",
            description="Test",
            steps=[{"name": "Step 1", "type": "ai_action"}],
            risk_level="R2",
        )
        self.execution = WorkflowExecution.objects.create(
            workflow=self.workflow_def,
            initiated_by=self.user,
            status=WorkflowExecution.Status.RUNNING,
        )

    def test_workflow_step_creation(self):
        """Test workflow step can be created."""
        step = WorkflowStep.objects.create(
            execution=self.execution,
            step_index=0,
            name="Step 1",
            description="First step",
            step_type="ai_action",
            status=WorkflowStep.Status.PENDING,
        )
        self.assertEqual(step.execution, self.execution)
        self.assertEqual(step.step_index, 0)
        self.assertEqual(step.status, WorkflowStep.Status.PENDING)

    def test_workflow_step_duration(self):
        """Test workflow step duration calculation."""
        from datetime import timedelta

        from django.utils import timezone

        step = WorkflowStep.objects.create(
            execution=self.execution,
            step_index=0,
            name="Step 1",
            description="First step",
            step_type="ai_action",
            status=WorkflowStep.Status.COMPLETED,
            started_at=timezone.now() - timedelta(seconds=30),
            completed_at=timezone.now(),
        )
        duration = step.duration_seconds
        self.assertIsNotNone(duration)
        self.assertAlmostEqual(duration, 30, delta=1)

    def test_workflow_step_str(self):
        """Test workflow step string representation."""
        step = WorkflowStep.objects.create(
            execution=self.execution,
            step_index=0,
            name="Step 1",
            description="First step",
            step_type="ai_action",
            status=WorkflowStep.Status.COMPLETED,
        )
        self.assertIn("Step 1", str(step))
        self.assertIn("completed", str(step))
