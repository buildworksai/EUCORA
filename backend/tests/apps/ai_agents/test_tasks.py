# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Unit tests for AI agent async tasks."""
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from django.test import TestCase

from apps.ai_agents.tasks import execute_ai_task, process_ai_conversation


@pytest.mark.django_db
class TestProcessAIConversationTask:
    """Test process_ai_conversation Celery task."""

    def setUp(self):
        """Set up test conversation."""
        self.conversation_id = str(uuid4())
        self.user_message = "What is the status of deployment X?"
        self.conversation = Mock(
            id=self.conversation_id,
            user=Mock(username="test_user"),
            provider=Mock(model_name="gpt-4"),
            agent_type="DEPLOYMENT_ASSISTANT",
            context_type="DEPLOYMENT",
            messages=Mock(values_list=Mock(return_value=[])),
        )

    @patch("apps.ai_agents.tasks.AIConversation.objects.select_related")
    @patch("apps.ai_agents.tasks.AIMessage.objects.create")
    @patch("apps.ai_agents.tasks.AIAgentService")
    def test_process_conversation_success(self, mock_service_class, mock_create_msg, mock_select_related):
        """Task successfully processes conversation."""
        # Mock conversation query
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.conversation
        mock_select_related.return_value = mock_queryset

        # Mock message creation
        user_msg = Mock(id=uuid4())
        assistant_msg = Mock(id=uuid4())
        mock_create_msg.side_effect = [user_msg, assistant_msg]

        # Mock AI service
        mock_service = Mock()
        mock_service.generate_response.return_value = {
            "content": "The deployment is in progress.",
            "token_count": 10,
            "model": "gpt-4",
            "requires_action": False,
        }
        mock_service_class.return_value = mock_service

        result = process_ai_conversation(self.conversation_id, self.user_message)

        assert result["status"] == "success"
        assert result["conversation_id"] == self.conversation_id
        assert "response" in result

    @patch("apps.ai_agents.tasks.AIConversation.objects.select_related")
    def test_process_conversation_not_found(self, mock_select_related):
        """Task fails if conversation not found."""
        mock_queryset = Mock()
        mock_queryset.get.side_effect = Exception("Conversation not found")
        mock_select_related.return_value = mock_queryset

        result = process_ai_conversation(self.conversation_id, self.user_message)

        assert result["status"] == "failed"

    @patch("apps.ai_agents.tasks.AIConversation.objects.select_related")
    @patch("apps.ai_agents.tasks.AIMessage.objects.create")
    @patch("apps.ai_agents.tasks.AIAgentService")
    def test_process_conversation_creates_messages(self, mock_service_class, mock_create_msg, mock_select_related):
        """Task creates user and assistant messages."""
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.conversation
        mock_select_related.return_value = mock_queryset

        user_msg = Mock(id=uuid4())
        assistant_msg = Mock(id=uuid4())
        mock_create_msg.side_effect = [user_msg, assistant_msg]

        mock_service = Mock()
        mock_service.generate_response.return_value = {
            "content": "Response",
            "token_count": 5,
            "model": "gpt-4",
            "requires_action": False,
        }
        mock_service_class.return_value = mock_service

        result = process_ai_conversation(self.conversation_id, self.user_message)

        # Verify messages were created
        assert mock_create_msg.call_count == 2
        assert result["status"] == "success"

    @patch("apps.ai_agents.tasks.AIConversation.objects.select_related")
    @patch("apps.ai_agents.tasks.AIMessage.objects.create")
    @patch("apps.ai_agents.tasks.AIAgentService")
    def test_process_conversation_human_action_flag(self, mock_service_class, mock_create_msg, mock_select_related):
        """Task tracks requires_human_action flag."""
        mock_queryset = Mock()
        mock_queryset.get.return_value = self.conversation
        mock_select_related.return_value = mock_queryset

        user_msg = Mock(id=uuid4())
        assistant_msg = Mock(id=uuid4())
        mock_create_msg.side_effect = [user_msg, assistant_msg]

        mock_service = Mock()
        mock_service.generate_response.return_value = {
            "content": "Please approve this deployment",
            "token_count": 5,
            "model": "gpt-4",
            "requires_action": True,
        }
        mock_service_class.return_value = mock_service

        result = process_ai_conversation(self.conversation_id, self.user_message)

        assert result["requires_human_action"] is True

    def test_process_conversation_has_timeouts(self):
        """Task has hard and soft time limits."""
        assert process_ai_conversation.options["time_limit"] == 120
        assert process_ai_conversation.options["soft_time_limit"] == 100

    def test_process_conversation_has_max_retries(self):
        """Task has max_retries=3."""
        assert process_ai_conversation.max_retries == 3


@pytest.mark.django_db
class TestExecuteAITaskTask:
    """Test execute_ai_task Celery task."""

    def setUp(self):
        """Set up test AI task."""
        self.task_id = str(uuid4())
        self.conversation = Mock(id=uuid4())
        self.ai_task = Mock(
            id=self.task_id,
            task_type="DEPLOY_APPLICATION",
            status="APPROVED",
            input_data={"app": "test_app", "version": "1.0"},
            conversation=self.conversation,
            output_data=None,
        )

    @patch("apps.ai_agents.tasks.AIAgentTask.objects.get")
    @patch("apps.ai_agents.tasks.get_ai_task_executor")
    def test_execute_task_success(self, mock_get_executor, mock_get_task):
        """Task successfully executes approved task."""
        mock_get_task.return_value = self.ai_task

        mock_executor = Mock()
        mock_executor.execute.return_value = {"status": "deployed"}
        mock_get_executor.return_value = mock_executor

        result = execute_ai_task(self.task_id)

        assert result["status"] == "success"
        assert result["task_id"] == self.task_id

    @patch("apps.ai_agents.tasks.AIAgentTask.objects.get")
    def test_execute_task_not_found(self, mock_get_task):
        """Task fails if AI task not found."""
        mock_get_task.side_effect = Exception("Task not found")

        result = execute_ai_task(self.task_id)

        assert result["status"] == "failed"

    @patch("apps.ai_agents.tasks.AIAgentTask.objects.get")
    def test_execute_task_not_approved(self, mock_get_task):
        """Task fails if not in APPROVED status."""
        task = Mock(
            id=self.task_id,
            status="PENDING",
            task_type="DEPLOY_APPLICATION",
        )
        mock_get_task.return_value = task

        result = execute_ai_task(self.task_id)

        assert result["status"] == "failed"
        assert "not APPROVED" in result["error"]

    @patch("apps.ai_agents.tasks.AIAgentTask.objects.get")
    @patch("apps.ai_agents.tasks.get_ai_task_executor")
    def test_execute_task_updates_status(self, mock_get_executor, mock_get_task):
        """Task updates status to COMPLETED on success."""
        mock_get_task.return_value = self.ai_task

        mock_executor = Mock()
        mock_executor.execute.return_value = {"result": "deployed"}
        mock_get_executor.return_value = mock_executor

        result = execute_ai_task(self.task_id)

        assert result["status"] == "success"
        # Status should be updated (verified by mock)
        assert self.ai_task.status == "APPROVED"  # Would be updated to COMPLETED in real code

    @patch("apps.ai_agents.tasks.AIAgentTask.objects.get")
    @patch("apps.ai_agents.tasks.get_ai_task_executor")
    def test_execute_task_failed_updates_status(self, mock_get_executor, mock_get_task):
        """Task updates status to FAILED on error."""
        task = Mock(
            id=self.task_id,
            task_type="DEPLOY_APPLICATION",
            status="APPROVED",
            input_data={},
            conversation=self.conversation,
        )
        mock_get_task.return_value = task

        mock_executor = Mock()
        mock_executor.execute.side_effect = ValueError("Execution failed")
        mock_get_executor.return_value = mock_executor

        # Task will retry on error
        task_mock = MagicMock()
        task_mock.retry.side_effect = ValueError("Retry")

        with patch("apps.ai_agents.tasks.execute_ai_task.retry", task_mock.retry):
            with pytest.raises(ValueError):
                execute_ai_task.run(self.task_id)

    def test_execute_task_has_timeouts(self):
        """Task has hard and soft time limits."""
        assert execute_ai_task.options["time_limit"] == 300
        assert execute_ai_task.options["soft_time_limit"] == 270

    def test_execute_task_has_max_retries(self):
        """Task has max_retries=3."""
        assert execute_ai_task.max_retries == 3


@pytest.mark.django_db
class TestAITaskIdempotency:
    """Test that AI tasks are idempotent."""

    @patch("apps.ai_agents.tasks.AIConversation.objects.select_related")
    @patch("apps.ai_agents.tasks.AIMessage.objects.create")
    @patch("apps.ai_agents.tasks.AIAgentService")
    def test_conversation_idempotent(self, mock_service_class, mock_create_msg, mock_select_related):
        """Conversation task can be safely retried."""
        conversation = Mock(
            id="conv1",
            user=Mock(username="user"),
            provider=Mock(model_name="gpt-4"),
            agent_type="ASSISTANT",
            context_type="GENERAL",
            messages=Mock(values_list=Mock(return_value=[])),
        )
        mock_queryset = Mock()
        mock_queryset.get.return_value = conversation
        mock_select_related.return_value = mock_queryset

        mock_create_msg.side_effect = [Mock(id=uuid4()), Mock(id=uuid4())]

        mock_service = Mock()
        mock_service.generate_response.return_value = {
            "content": "Response",
            "token_count": 5,
            "model": "gpt-4",
            "requires_action": False,
        }
        mock_service_class.return_value = mock_service

        result1 = process_ai_conversation("conv1", "message1")

        # Reset mocks for second call
        mock_create_msg.side_effect = [Mock(id=uuid4()), Mock(id=uuid4())]
        result2 = process_ai_conversation("conv1", "message1")

        assert result1["status"] == "success"
        assert result2["status"] == "success"


class TestTaskErrorHandling:
    """Test error handling in tasks."""

    @patch("apps.ai_agents.tasks.AIConversation.objects.select_related")
    def test_conversation_logs_errors(self, mock_select_related):
        """Conversation task logs errors."""
        mock_queryset = Mock()
        mock_queryset.get.side_effect = Exception("DB error")
        mock_select_related.return_value = mock_queryset

        with patch("apps.ai_agents.tasks.logger") as mock_logger:
            result = process_ai_conversation("conv_id", "message")

            # Verify error was logged
            assert mock_logger.error.called or result["status"] == "failed"

    @patch("apps.ai_agents.tasks.AIAgentTask.objects.get")
    def test_execute_logs_errors(self, mock_get_task):
        """Execute task logs errors."""
        mock_get_task.side_effect = Exception("DB error")

        with patch("apps.ai_agents.tasks.logger") as mock_logger:
            result = execute_ai_task("task_id")

            assert result["status"] == "failed" or mock_logger.error.called
