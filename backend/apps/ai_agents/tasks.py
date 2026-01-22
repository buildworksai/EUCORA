# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for AI agent processing.

All AI recommendations require human approval before execution.
Tasks are asynchronous to prevent blocking API requests on LLM calls.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.ai_agents.tasks.process_ai_conversation', bind=True, max_retries=3, time_limit=120, soft_time_limit=100)
def process_ai_conversation(self, conversation_id, user_message):
    """
    Async task to process AI conversation and generate response.
    
    Prevents blocking API requests while waiting for LLM response.
    
    Args:
        conversation_id: UUID of AIConversation
        user_message: User's input message
    
    Returns:
        {'status': 'success' | 'failed', 'conversation_id': ..., 'message_id': ..., 'response': ...}
    """
    from apps.ai_agents.models import AIConversation, AIMessage
    from apps.ai_agents.services import AIAgentService
    
    try:
        conversation = AIConversation.objects.select_related('user', 'provider').get(id=conversation_id)
    except AIConversation.DoesNotExist:
        logger.error(f'Conversation not found: {conversation_id}')
        return {'status': 'failed', 'error': 'Conversation not found'}
    
    try:
        # Create user message record
        user_msg = AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.USER,
            content=user_message,
            token_count=len(user_message.split()),  # Rough estimate
        )
        
        # Get AI service and generate response
        service = AIAgentService(conversation.provider, conversation.agent_type)
        response = service.generate_response(
            messages=list(conversation.messages.values_list('role', 'content')),
            system_context=conversation.context_type
        )
        
        # Create assistant message record
        assistant_msg = AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.ASSISTANT,
            content=response['content'],
            token_count=response.get('token_count', len(response['content'].split())),
            model_used=response.get('model', conversation.provider.model_name),
            requires_human_action=response.get('requires_action', False),
        )
        
        logger.info(
            f'AI conversation processed successfully',
            extra={
                'conversation_id': str(conversation_id),
                'agent_type': conversation.agent_type,
                'message_id': str(assistant_msg.id)
            }
        )
        
        return {
            'status': 'success',
            'conversation_id': str(conversation_id),
            'message_id': str(assistant_msg.id),
            'response': response['content'],
            'requires_human_action': response.get('requires_action', False),
        }
        
    except Exception as exc:
        logger.error(
            f'Failed to process AI conversation: {exc}',
            extra={'conversation_id': str(conversation_id)},
            exc_info=True
        )
        
        # Retry with exponential backoff (max 3 retries)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(name='apps.ai_agents.tasks.execute_ai_task', bind=True, max_retries=3, time_limit=300, soft_time_limit=270)
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
        logger.error(f'AI task not found: {task_id}')
        return {'status': 'failed', 'error': 'Task not found'}
    
    if task.status != AIAgentTask.TaskStatus.APPROVED:
        logger.warning(
            f'AI task not approved for execution: {task_id}',
            extra={'task_id': str(task_id), 'status': task.status}
        )
        return {'status': 'failed', 'error': f'Task status is {task.status}, not APPROVED'}
    
    try:
        # Get executor for this task type
        executor = get_ai_task_executor(task.task_type)
        
        # Execute task
        result = executor.execute(task.input_data, task.conversation)
        
        # Update task status
        task.status = AIAgentTask.TaskStatus.COMPLETED
        task.output_data = result
        task.save()
        
        logger.info(
            f'AI task executed successfully',
            extra={'task_id': str(task_id), 'task_type': task.task_type}
        )
        
        return {
            'status': 'success',
            'task_id': str(task_id),
            'result': result,
        }
        
    except Exception as exc:
        logger.error(
            f'Failed to execute AI task: {exc}',
            extra={'task_id': str(task_id), 'task_type': task.task_type},
            exc_info=True
        )
        
        # Update task status to failed
        task.status = AIAgentTask.TaskStatus.FAILED
        task.save()
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
