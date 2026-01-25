# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for AI Agents.
"""
import logging
import uuid

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.utils import exempt_csrf_in_debug, get_demo_mode_enabled
from apps.event_store.models import DeploymentEvent

from .models import AIAgentTask, AIAgentType, AIConversation, AIMessage, AIModelProvider
from .services import get_ai_agent_service
from .tasks import process_ai_conversation

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_providers(request):
    """List all configured AI model providers."""
    # Only Platform Admins can see provider details
    # For now, allow authenticated users (can be restricted later with permissions)

    providers = AIModelProvider.objects.all().order_by("provider_type", "model_name")

    return Response(
        {
            "providers": [
                {
                    "id": str(p.id),
                    "provider_type": p.provider_type,
                    "display_name": p.display_name,
                    "model_name": p.model_name,
                    "is_active": p.is_active,
                    "is_default": p.is_default,
                    # Never expose actual API keys - just indicate if configured
                    "key_configured": bool(p.api_key_dev or p.key_vault_ref),
                    "endpoint_url": p.endpoint_url if p.endpoint_url else None,
                    "max_tokens": p.max_tokens,
                    "temperature": p.temperature,
                }
                for p in providers
            ]
        }
    )


@exempt_csrf_in_debug
@api_view(["POST"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def configure_provider(request):
    """Configure an AI model provider (Platform Admin only)."""
    # Platform Admin permission check (Platform Admin role required)
    if not settings.DEBUG and not request.user.has_perm("ai_agents.change_aimodelprovider"):
        return Response(
            {"error": "Platform Admin permission required to configure AI providers"}, status=status.HTTP_403_FORBIDDEN
        )

    provider_type = request.data.get("provider_type")
    api_key = request.data.get("api_key", "")
    model_name = request.data.get("model_name")
    display_name = request.data.get("display_name", provider_type)

    if not provider_type or not model_name:
        return Response({"error": "provider_type and model_name are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if provider already exists
    existing_provider = AIModelProvider.objects.filter(provider_type=provider_type, model_name=model_name).first()

    # If setting as default, unset other defaults
    is_default = request.data.get("is_default", False)
    if is_default:
        AIModelProvider.objects.filter(is_default=True).update(is_default=False)

    # Prepare update defaults - only update api_key if provided (non-empty)
    update_defaults = {
        "display_name": display_name,
        "is_active": True,
        "is_default": is_default,
        "endpoint_url": request.data.get("endpoint_url"),
        "max_tokens": request.data.get("max_tokens", 4096),
        "temperature": request.data.get("temperature", 0.7),
    }

    # Only update API key if a new one is provided (non-empty)
    # If empty and provider exists, keep existing key
    if api_key:
        update_defaults["api_key_dev"] = api_key  # DEV ONLY: Store key directly in DB
    elif not existing_provider:
        # New provider requires API key
        return Response(
            {"error": "api_key is required for new provider configurations"}, status=status.HTTP_400_BAD_REQUEST
        )
    # If existing_provider and api_key is empty, we keep the existing key (don't update it)

    # Store API key directly in database (DEV ONLY)
    # In production: use key_vault_ref with proper secrets management
    provider, created = AIModelProvider.objects.update_or_create(
        provider_type=provider_type, model_name=model_name, defaults=update_defaults
    )

    # Clear provider cache to pick up new key
    service = get_ai_agent_service()
    cache_key = f"{provider_type}_{model_name}"
    if cache_key in service._provider_cache:
        del service._provider_cache[cache_key]

    # Log audit event to event store
    correlation_id = uuid.uuid4()
    DeploymentEvent.objects.create(
        correlation_id=correlation_id,
        event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,  # Using for AI provider config
        event_data={
            "action": "ai_provider_configured",
            "provider_type": provider_type,
            "model_name": model_name,
            "display_name": display_name,
            "is_default": is_default,
            "created": created,
        },
        actor=request.user.username,
        is_demo=get_demo_mode_enabled(),
    )

    logger.info(
        f"User {request.user.username} configured AI provider: {provider_type}/{model_name}",
        extra={"correlation_id": str(correlation_id), "provider_type": provider_type},
    )

    return Response(
        {
            "success": True,
            "created": created,
            "provider": {
                "id": str(provider.id),
                "provider_type": provider.provider_type,
                "display_name": provider.display_name,
                "model_name": provider.model_name,
                "is_active": provider.is_active,
                "is_default": provider.is_default,
                "key_configured": bool(provider.api_key_dev or provider.key_vault_ref),
                "endpoint_url": provider.endpoint_url,
                "max_tokens": provider.max_tokens,
                "temperature": provider.temperature,
            },
        }
    )


@exempt_csrf_in_debug
@api_view(["DELETE"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def delete_provider(request, provider_id):
    """Delete an AI model provider configuration."""
    try:
        provider = AIModelProvider.objects.get(id=provider_id)
        provider_name = f"{provider.provider_type}/{provider.model_name}"

        # Clear from cache
        service = get_ai_agent_service()
        cache_key = f"{provider.provider_type}_{provider.model_name}"
        if cache_key in service._provider_cache:
            del service._provider_cache[cache_key]

        # Delete the provider
        provider.delete()

        logger.info(f"User {request.user.username} deleted AI provider: {provider_name}")

        return Response({"success": True, "message": f"Provider {provider_name} deleted successfully"})
    except AIModelProvider.DoesNotExist:
        return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting provider: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf_in_debug
@api_view(["DELETE"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def delete_provider_by_type(request, provider_type):
    """Delete all AI model providers of a specific type."""
    try:
        providers = AIModelProvider.objects.filter(provider_type=provider_type)
        count = providers.count()

        if count == 0:
            return Response(
                {"error": f"No providers found for type: {provider_type}"}, status=status.HTTP_404_NOT_FOUND
            )

        # Clear from cache
        service = get_ai_agent_service()
        for provider in providers:
            cache_key = f"{provider.provider_type}_{provider.model_name}"
            if cache_key in service._provider_cache:
                del service._provider_cache[cache_key]

        # Delete all providers of this type
        providers.delete()

        logger.info(f"User {request.user.username} deleted {count} AI provider(s) of type: {provider_type}")

        return Response({"success": True, "message": f"Deleted {count} provider(s) of type {provider_type}"})
    except Exception as e:
        logger.error(f"Error deleting providers: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf_in_debug
@api_view(["POST"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def ask_amani(request):
    """Ask Amani - General AI assistant endpoint."""
    user_message = request.data.get("message")
    conversation_id = request.data.get("conversation_id")
    context = request.data.get("context", {})

    if not user_message:
        return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

    # In DEBUG mode, allow unauthenticated users (for demo/testing)
    # Use a default demo user if not authenticated
    user = request.user if request.user.is_authenticated else None
    if not user and settings.DEBUG:
        from django.contrib.auth.models import User

        user, _ = User.objects.get_or_create(username="demo", defaults={"email": "demo@eucora.com", "is_staff": True})

    if not user:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # Queue async task for LLM processing
        task_result = process_ai_conversation.delay(str(conversation_id), user_message)

        logger.info(
            f"AI conversation task queued for processing",
            extra={"conversation_id": str(conversation_id), "task_id": task_result.id},
        )

        return Response(
            {
                "status": "processing",
                "conversation_id": str(conversation_id),
                "task_id": task_result.id,
                "message": "Your message is being processed. Check conversation history for response.",
            }
        )
    except Exception as e:
        logger.error(f"Error in ask_amani: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf_in_debug
@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def get_conversation(request, conversation_id):
    """Get conversation history."""
    try:
        # In DEBUG mode, allow unauthenticated users (for demo/testing)
        # Use a default demo user if not authenticated
        user = request.user if request.user.is_authenticated else None
        if not user and settings.DEBUG:
            from django.contrib.auth.models import User

            user, _ = User.objects.get_or_create(
                username="demo", defaults={"email": "demo@eucora.com", "is_staff": True}
            )

        if not user:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        service = get_ai_agent_service()
        messages = service.get_conversation_history(conversation_id, user)

        return Response({"conversation_id": conversation_id, "messages": messages})
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@exempt_csrf_in_debug
@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def list_conversations(request):
    """List user's conversations."""
    agent_type = request.query_params.get("agent_type")

    try:
        # In DEBUG mode, allow unauthenticated users (for demo/testing)
        # Use a default demo user if not authenticated
        user = request.user if request.user.is_authenticated else None
        if not user and settings.DEBUG:
            from django.contrib.auth.models import User

            user, _ = User.objects.get_or_create(
                username="demo", defaults={"email": "demo@eucora.com", "is_staff": True}
            )

        if not user:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

        service = get_ai_agent_service()
        conversations = service.list_user_conversations(user, agent_type)

        return Response({"conversations": conversations})
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def agent_stats(request):
    """Get AI agent statistics."""
    try:
        if request.user.is_authenticated:
            active_tasks = AIAgentTask.objects.filter(
                initiated_by=request.user, status__in=["pending", "in_progress", "awaiting_approval"]
            ).count()

            awaiting_approval = AIAgentTask.objects.filter(
                initiated_by=request.user, status="awaiting_approval"
            ).count()

            completed_today = AIAgentTask.objects.filter(
                initiated_by=request.user, status="completed", updated_at__date=timezone.now().date()
            ).count()

            # Calculate tokens used (rough estimate)
            today_messages = AIMessage.objects.filter(
                conversation__user=request.user, created_at__date=timezone.now().date(), role="assistant"
            )
            tokens_used = sum(msg.token_count for msg in today_messages)
        else:
            # Anonymous users get zeros
            active_tasks = 0
            awaiting_approval = 0
            completed_today = 0
            tokens_used = 0

        return Response(
            {
                "active_tasks": active_tasks,
                "awaiting_approval": awaiting_approval,
                "completed_today": completed_today,
                "tokens_used": tokens_used // 1000,  # Return in thousands
            }
        )
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_tasks(request):
    """List AI agent tasks."""
    status_filter = request.query_params.get("status")

    queryset = (
        AIAgentTask.objects.filter(initiated_by=request.user)
        if request.user.is_authenticated
        else AIAgentTask.objects.none()
    )

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    tasks = queryset.order_by("-created_at")[:50]

    return Response(
        {
            "tasks": [
                {
                    "id": str(task.id),
                    "agent_type": task.agent_type,
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "input_data": task.input_data,
                    "output_data": task.output_data,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "correlation_id": str(task.correlation_id),
                    "initiated_by": task.initiated_by.username if task.initiated_by else None,
                    "approved_by": task.approved_by.username if task.approved_by else None,
                }
                for task in tasks
            ]
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def list_pending_approvals(request):
    """List all AI agent tasks pending human approval."""
    # Users see their own tasks pending approval
    # Admins/Staff can see all pending approvals
    # Anonymous users see no approvals
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        queryset = AIAgentTask.objects.filter(status="awaiting_approval")
    elif request.user.is_authenticated:
        queryset = AIAgentTask.objects.filter(initiated_by=request.user, status="awaiting_approval")
    else:
        # Anonymous users get empty list
        queryset = AIAgentTask.objects.none()

    tasks = queryset.order_by("-created_at")[:100]

    return Response(
        {
            "pending_approvals": [
                {
                    "id": str(task.id),
                    "agent_type": task.agent_type,
                    "agent_type_display": dict(AIAgentType.choices).get(task.agent_type, task.agent_type),
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "input_data": task.input_data,
                    "output_data": task.output_data,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "correlation_id": str(task.correlation_id),
                    "initiated_by": (
                        {
                            "username": task.initiated_by.username,
                            "email": task.initiated_by.email,
                            "name": f"{task.initiated_by.first_name} {task.initiated_by.last_name}".strip()
                            or task.initiated_by.username,
                        }
                        if task.initiated_by
                        else None
                    ),
                }
                for task in tasks
            ],
            "total_count": queryset.count(),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_task(request, task_id):
    """Get detailed information about a specific AI agent task."""
    try:
        task = AIAgentTask.objects.get(id=task_id)

        # Check permissions - user can see their own tasks, admins can see all
        if task.initiated_by != request.user and not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "You do not have permission to view this task"}, status=status.HTTP_403_FORBIDDEN)

        return Response(
            {
                "task": {
                    "id": str(task.id),
                    "agent_type": task.agent_type,
                    "agent_type_display": dict(AIAgentType.choices).get(task.agent_type, task.agent_type),
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "input_data": task.input_data,
                    "output_data": task.output_data,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "correlation_id": str(task.correlation_id),
                    "initiated_by": (
                        {
                            "username": task.initiated_by.username,
                            "email": task.initiated_by.email,
                            "name": f"{task.initiated_by.first_name} {task.initiated_by.last_name}".strip()
                            or task.initiated_by.username,
                        }
                        if task.initiated_by
                        else None
                    ),
                    "approved_by": (
                        {
                            "username": task.approved_by.username,
                            "email": task.approved_by.email,
                            "name": f"{task.approved_by.first_name} {task.approved_by.last_name}".strip()
                            or task.approved_by.username,
                        }
                        if task.approved_by
                        else None
                    ),
                }
            }
        )
    except AIAgentTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approve_task(request, task_id):
    """Approve an AI agent task for execution."""
    try:
        task = AIAgentTask.objects.get(id=task_id)

        # Only tasks awaiting approval can be approved
        if task.status != "awaiting_approval":
            return Response(
                {"error": f"Task is not awaiting approval. Current status: {task.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check permissions - only staff/admins can approve tasks
        # (In production, this would check specific CAB approval permissions)
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "You do not have permission to approve tasks"}, status=status.HTTP_403_FORBIDDEN)

        # Get approval comment if provided
        comment = request.data.get("comment", "")

        # Update task status
        task.status = "approved"
        task.approved_by = request.user
        task.output_data = {
            **task.output_data,
            "approval": {
                "approved_by": request.user.username,
                "approved_at": timezone.now().isoformat(),
                "comment": comment,
            },
        }
        task.save()

        # Audit log
        logger.info(
            f"User {request.user.username} approved AI task: {task.id} ({task.title})",
            extra={
                "correlation_id": str(task.correlation_id),
                "task_id": str(task.id),
                "approved_by": request.user.username,
            },
        )

        return Response(
            {
                "success": True,
                "message": "Task approved successfully",
                "task": {
                    "id": str(task.id),
                    "status": task.status,
                    "approved_by": request.user.username,
                    "approved_at": timezone.now().isoformat(),
                },
            }
        )

    except AIAgentTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error approving task: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reject_task(request, task_id):
    """Reject an AI agent task."""
    try:
        task = AIAgentTask.objects.get(id=task_id)

        # Only tasks awaiting approval can be rejected
        if task.status != "awaiting_approval":
            return Response(
                {"error": f"Task is not awaiting approval. Current status: {task.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check permissions - only staff/admins can reject tasks
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({"error": "You do not have permission to reject tasks"}, status=status.HTTP_403_FORBIDDEN)

        # Get rejection reason
        reason = request.data.get("reason", "No reason provided")

        # Update task status
        task.status = "rejected"
        task.approved_by = request.user  # Also track who rejected
        task.output_data = {
            **task.output_data,
            "rejection": {
                "rejected_by": request.user.username,
                "rejected_at": timezone.now().isoformat(),
                "reason": reason,
            },
        }
        task.save()

        # Audit log
        logger.info(
            f"User {request.user.username} rejected AI task: {task.id} ({task.title})",
            extra={
                "correlation_id": str(task.correlation_id),
                "task_id": str(task.id),
                "rejected_by": request.user.username,
                "reason": reason,
            },
        )

        return Response(
            {
                "success": True,
                "message": "Task rejected",
                "task": {
                    "id": str(task.id),
                    "status": task.status,
                    "rejected_by": request.user.username,
                    "rejected_at": timezone.now().isoformat(),
                    "reason": reason,
                },
            }
        )

    except AIAgentTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error rejecting task: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_task_revision(request, task_id):
    """
    Request revision/feedback for an AI agent task.

    This allows users to provide feedback to improve the AI recommendation
    instead of simply approving or rejecting it. The AI will generate a
    revised recommendation based on the feedback.
    """
    try:
        task = AIAgentTask.objects.get(id=task_id)

        # Only tasks awaiting approval can have revision requested
        if task.status not in ["awaiting_approval", "revision_requested"]:
            return Response(
                {"error": f"Task is not awaiting feedback. Current status: {task.status}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Get feedback from request
        feedback = request.data.get("feedback", "")
        if not feedback.strip():
            return Response(
                {"error": "Feedback is required when requesting revision"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Build revision history
        revisions = task.output_data.get("revisions", [])
        revision_number = len(revisions) + 1

        new_revision = {
            "revision_number": revision_number,
            "requested_by": request.user.username,
            "requested_at": timezone.now().isoformat(),
            "feedback": feedback,
            "original_recommendation": task.description,
            "status": "pending_ai_response",
        }
        revisions.append(new_revision)

        # Update task status and output data
        task.status = "revision_requested"
        task.output_data = {
            **task.output_data,
            "revisions": revisions,
            "last_feedback": {
                "by": request.user.username,
                "at": timezone.now().isoformat(),
                "feedback": feedback,
            },
        }
        task.save()

        # Now, trigger AI to generate revised recommendation
        # This integrates with the Amani service to refine the suggestion
        try:
            service = get_ai_agent_service()

            # Build a refinement prompt
            refinement_context = {
                "task_id": str(task.id),
                "task_type": "revision_request",
                "original_recommendation": task.description,
                "user_feedback": feedback,
                "revision_number": revision_number,
            }

            # Ask AI to refine based on feedback
            refinement_message = f"""The user has requested a revision to my previous recommendation.

**Original Recommendation:**
{task.description}

**User Feedback:**
{feedback}

Please provide an improved recommendation that addresses the user's feedback. Consider their corrections and suggestions carefully."""

            result = service.ask_amani_sync(
                user_message=refinement_message,
                conversation_id=str(task.conversation.id) if task.conversation else None,
                context=refinement_context,
                user=request.user,
            )

            if "error" not in result:
                # Update task with revised recommendation
                revised_recommendation = result.get("response", "")

                # Update the last revision with AI response
                revisions[-1]["ai_response"] = revised_recommendation
                revisions[-1]["responded_at"] = timezone.now().isoformat()
                revisions[-1]["status"] = "ai_responded"

                # Update task description with revised recommendation
                task.description = revised_recommendation
                task.status = "awaiting_approval"  # Ready for review again
                task.output_data = {
                    **task.output_data,
                    "revisions": revisions,
                    "last_revision": {
                        "number": revision_number,
                        "original": new_revision["original_recommendation"],
                        "feedback": feedback,
                        "revised": revised_recommendation,
                    },
                }
                task.save()

                # Audit log
                logger.info(
                    f"User {request.user.username} requested revision for AI task: {task.id}. AI responded with revision.",
                    extra={
                        "correlation_id": str(task.correlation_id),
                        "task_id": str(task.id),
                        "revision_number": revision_number,
                        "requested_by": request.user.username,
                    },
                )

                return Response(
                    {
                        "success": True,
                        "message": "Revision generated successfully",
                        "task": {
                            "id": str(task.id),
                            "status": task.status,
                            "title": task.title,
                            "description": task.description,  # Now contains revised recommendation
                            "revision_number": revision_number,
                            "original_recommendation": new_revision["original_recommendation"],
                            "revised_recommendation": revised_recommendation,
                            "feedback": feedback,
                        },
                    }
                )
            else:
                # AI failed to generate revision, but feedback is recorded
                logger.warning(
                    f"AI failed to generate revision for task {task.id}: {result.get('error')}",
                    extra={
                        "correlation_id": str(task.correlation_id),
                        "task_id": str(task.id),
                    },
                )

                return Response(
                    {
                        "success": True,
                        "message": "Feedback recorded. AI revision generation pending.",
                        "task": {
                            "id": str(task.id),
                            "status": task.status,
                            "revision_number": revision_number,
                            "feedback": feedback,
                            "ai_status": "pending",
                        },
                    }
                )

        except Exception as ai_error:
            logger.error(f"Error generating AI revision: {ai_error}", exc_info=True)
            # Feedback is still saved even if AI fails
            return Response(
                {
                    "success": True,
                    "message": "Feedback recorded. AI revision will be generated when service is available.",
                    "task": {
                        "id": str(task.id),
                        "status": task.status,
                        "revision_number": revision_number,
                        "feedback": feedback,
                        "ai_status": "pending",
                    },
                }
            )

    except AIAgentTask.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error requesting revision: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_task_from_message(request):
    """
    Create an AI agent task from a chat message that requires approval.
    This is called when the AI suggests an action that needs human approval.
    """
    try:
        title = request.data.get("title")
        description = request.data.get("description")
        agent_type = request.data.get("agent_type", "amani")
        task_type = request.data.get("task_type", "ai_recommendation")
        input_data = request.data.get("input_data", {})
        output_data = request.data.get("output_data", {})
        conversation_id = request.data.get("conversation_id")

        if not title or not description:
            return Response({"error": "title and description are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Link to conversation if provided
        conversation = None
        if conversation_id:
            try:
                conversation = AIConversation.objects.get(id=conversation_id)
            except AIConversation.DoesNotExist:
                pass

        # Create the task
        task = AIAgentTask.objects.create(
            agent_type=agent_type,
            initiated_by=request.user,
            conversation=conversation,
            title=title,
            description=description,
            task_type=task_type,
            input_data=input_data,
            output_data=output_data,
            status="awaiting_approval",
        )

        # Audit log
        logger.info(
            f"User {request.user.username} created AI task requiring approval: {task.id} ({task.title})",
            extra={
                "correlation_id": str(task.correlation_id),
                "task_id": str(task.id),
                "agent_type": agent_type,
            },
        )

        return Response(
            {
                "success": True,
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "task_type": task.task_type,
                    "agent_type": task.agent_type,
                    "agent_type_display": dict(AIAgentType.choices).get(task.agent_type, task.agent_type),
                    "status": task.status,
                    "input_data": task.input_data,
                    "output_data": task.output_data,
                    "correlation_id": str(task.correlation_id),
                    "created_at": task.created_at.isoformat(),
                    "initiated_by": {
                        "username": request.user.username,
                        "email": request.user.email,
                        "name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    },
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        logger.error(f"Error creating task: {e}", exc_info=True)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
