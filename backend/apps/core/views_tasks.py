# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Task status API for querying Celery task state.

Provides endpoints to check the status of async tasks dispatched via Celery.
"""
from typing import Dict, Any, Optional
from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id: str) -> Response:
    """
    Get status of a Celery task.
    
    Args:
        task_id: Celery task ID (returned when task was dispatched)
    
    Returns:
        JSON response with task status:
        {
            "task_id": "...",
            "status": "PENDING" | "STARTED" | "SUCCESS" | "FAILURE" | "RETRY" | "REVOKED",
            "result": {...} | null,
            "error": "..." | null,
            "traceback": "..." | null,
            "progress": {...} | null
        }
    
    Status codes:
        200: Task found, status returned
        404: Task not found (may have expired from result backend)
    """
    try:
        result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': result.status,
            'result': None,
            'error': None,
            'traceback': None,
            'progress': None,
        }
        
        # Include result if task completed successfully
        if result.successful():
            response_data['result'] = result.result
        
        # Include error info if task failed
        elif result.failed():
            response_data['error'] = str(result.result) if result.result else 'Unknown error'
            response_data['traceback'] = result.traceback
        
        # Include progress info if available (for tasks that report progress)
        elif result.status == 'PROGRESS':
            response_data['progress'] = result.info
        
        # Include retry info
        elif result.status == 'RETRY':
            response_data['error'] = str(result.result) if result.result else 'Task is being retried'
        
        logger.debug(
            f'Task status queried: {task_id}',
            extra={
                'task_id': task_id,
                'status': result.status,
                'user': request.user.username if request.user else 'anonymous',
            }
        )
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(
            f'Error querying task status: {e}',
            extra={'task_id': task_id},
            exc_info=True,
        )
        return Response(
            {
                'task_id': task_id,
                'status': 'ERROR',
                'error': f'Failed to query task status: {str(e)}',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_task(request, task_id: str) -> Response:
    """
    Revoke (cancel) a Celery task.
    
    Args:
        task_id: Celery task ID to revoke
    
    Request body (optional):
        {
            "terminate": true,  // Send SIGTERM to worker process
            "signal": "SIGKILL" // Custom signal (default: SIGTERM)
        }
    
    Returns:
        JSON response indicating revocation status
    """
    try:
        result = AsyncResult(task_id)
        
        # Get options from request body
        terminate = request.data.get('terminate', False)
        signal = request.data.get('signal', 'SIGTERM')
        
        # Revoke the task
        result.revoke(terminate=terminate, signal=signal)
        
        logger.warning(
            f'Task revoked: {task_id}',
            extra={
                'task_id': task_id,
                'terminate': terminate,
                'signal': signal,
                'user': request.user.username if request.user else 'anonymous',
            }
        )
        
        return Response(
            {
                'task_id': task_id,
                'status': 'REVOKED',
                'message': f'Task {task_id} has been revoked',
            },
            status=status.HTTP_200_OK,
        )
        
    except Exception as e:
        logger.error(
            f'Error revoking task: {e}',
            extra={'task_id': task_id},
            exc_info=True,
        )
        return Response(
            {
                'task_id': task_id,
                'error': f'Failed to revoke task: {str(e)}',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_tasks(request) -> Response:
    """
    Get list of active Celery tasks.
    
    Query parameters:
        - queue: Filter by queue name (optional)
        - limit: Maximum number of tasks to return (default: 100)
    
    Returns:
        JSON response with active task information
    """
    try:
        from config.celery import app as celery_app
        
        # Get active tasks from all workers
        inspect = celery_app.control.inspect()
        
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        scheduled = inspect.scheduled() or {}
        
        # Combine all task info
        tasks = {
            'active': active,
            'reserved': reserved,
            'scheduled': scheduled,
            'summary': {
                'total_active': sum(len(v) for v in active.values()),
                'total_reserved': sum(len(v) for v in reserved.values()),
                'total_scheduled': sum(len(v) for v in scheduled.values()),
            }
        }
        
        logger.debug(
            'Active tasks queried',
            extra={
                'user': request.user.username if request.user else 'anonymous',
                'summary': tasks['summary'],
            }
        )
        
        return Response(tasks, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(
            f'Error querying active tasks: {e}',
            exc_info=True,
        )
        return Response(
            {'error': f'Failed to query active tasks: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
