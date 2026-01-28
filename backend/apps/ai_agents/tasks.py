# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for AI agent processing.

All AI recommendations require human approval before execution.
Tasks are asynchronous to prevent blocking API requests on LLM calls.
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="apps.ai_agents.tasks.process_ai_conversation", bind=True, max_retries=3, time_limit=120, soft_time_limit=100
)
def process_ai_conversation(self, conversation_id, user_message, user_id=None):
    """
    Async task to process AI conversation and generate response.

    Prevents blocking API requests while waiting for LLM response.
    Delegates to AIAgentService.ask_amani_sync() which handles provider
    setup, conversation history, system prompts, and message persistence.

    Args:
        conversation_id: UUID string of AIConversation (must exist in DB)
        user_message: User's input message
        user_id: ID of the requesting User (int or str)

    Returns:
        {'status': 'success' | 'failed', 'conversation_id': ..., 'response': ...}
    """
    from django.contrib.auth.models import User

    from apps.ai_agents.services import get_ai_agent_service

    try:
        # Resolve the user who initiated the conversation
        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User not found for id={user_id}, falling back to demo user")

        # Use the service layer which handles provider setup, conversation
        # history, system prompts, and message persistence correctly.
        service = get_ai_agent_service()
        result = service.ask_amani_sync(
            user_message=user_message,
            conversation_id=conversation_id,
            user=user,
        )

        if "error" in result:
            logger.error(
                f"AI service returned error: {result['error']}",
                extra={"conversation_id": conversation_id},
            )
            return {
                "status": "failed",
                "conversation_id": conversation_id,
                "error": result["error"],
            }

        logger.info(
            "AI conversation processed successfully",
            extra={
                "conversation_id": result.get("conversation_id", conversation_id),
            },
        )

        return {
            "status": "success",
            "conversation_id": result.get("conversation_id", conversation_id),
            "response": result.get("response", ""),
            "requires_human_action": result.get("requires_human_action", False),
        }

    except Exception as exc:
        logger.error(
            f"Failed to process AI conversation: {exc}", extra={"conversation_id": conversation_id}, exc_info=True
        )

        # Retry with exponential backoff (max 3 retries)
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(name="apps.ai_agents.tasks.execute_ai_task", bind=True, max_retries=3, time_limit=300, soft_time_limit=270)
def execute_ai_task(self, task_id):
    """
    Async task to execute AI-generated recommendations that have been approved.

    Only executes after human approval. Tracks all actions for audit trail.

    Args:
        task_id: UUID of AIAgentTask

    Returns:
        {'status': 'success' | 'failed', 'task_id': ..., 'result': ...}
    """
    from apps.ai_agents.models import AIAgentTask
    from apps.ai_agents.services import get_ai_task_executor

    try:
        task = AIAgentTask.objects.get(id=task_id)
    except AIAgentTask.DoesNotExist:
        logger.error(f"AI task not found: {task_id}")
        return {"status": "failed", "error": "Task not found"}

    if task.status != AIAgentTask.TaskStatus.APPROVED:
        logger.warning(
            f"AI task not approved for execution: {task_id}", extra={"task_id": str(task_id), "status": task.status}
        )
        return {"status": "failed", "error": f"Task status is {task.status}, not APPROVED"}

    try:
        # Get executor for this task type
        executor = get_ai_task_executor(task.task_type)

        # Execute task
        result = executor.execute(task.input_data, task.conversation)

        # Update task status
        task.status = AIAgentTask.TaskStatus.COMPLETED
        task.output_data = result
        task.save()

        logger.info("AI task executed successfully", extra={"task_id": str(task_id), "task_type": task.task_type})

        return {
            "status": "success",
            "task_id": str(task_id),
            "result": result,
        }

    except Exception as exc:
        logger.error(
            f"Failed to execute AI task: {exc}",
            extra={"task_id": str(task_id), "task_type": task.task_type},
            exc_info=True,
        )

        # Update task status to failed
        task.status = AIAgentTask.TaskStatus.FAILED
        task.save()

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)
