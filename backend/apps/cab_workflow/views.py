# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow views for approval workflows.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import CABApproval
from apps.deployment_intents.models import DeploymentIntent
from django.utils import timezone
from apps.core.utils import apply_demo_filter
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_deployment(request, correlation_id):
    """
    Approve deployment intent.
    
    POST /api/v1/cab/{correlation_id}/approve
    Body: {"comments": "...", "conditions": [...]}
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({'error': 'Deployment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    comments = request.data.get('comments', '')
    conditions = request.data.get('conditions', [])
    
    # Create or update CAB approval
    approval, created = CABApproval.objects.get_or_create(
        deployment_intent=deployment,
        defaults={
            'decision': CABApproval.Decision.APPROVED if not conditions else CABApproval.Decision.CONDITIONAL,
            'approver': request.user,
            'comments': comments,
            'conditions': conditions,
            'reviewed_at': timezone.now(),
            'is_demo': deployment.is_demo,
        }
    )
    
    if not created:
        approval.decision = CABApproval.Decision.APPROVED if not conditions else CABApproval.Decision.CONDITIONAL
        approval.approver = request.user
        approval.comments = comments
        approval.conditions = conditions
        approval.reviewed_at = timezone.now()
        approval.save()
    
    # Update deployment status
    deployment.status = DeploymentIntent.Status.APPROVED
    deployment.save()
    
    logger.info(
        f'Deployment approved: {correlation_id}',
        extra={'correlation_id': str(correlation_id), 'approver': request.user.username}
    )
    
    return Response({'message': 'Deployment approved', 'decision': approval.decision})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_deployment(request, correlation_id):
    """
    Reject deployment intent.
    
    POST /api/v1/cab/{correlation_id}/reject
    Body: {"comments": "..."}
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({'error': 'Deployment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    comments = request.data.get('comments', '')
    
    # Create or update CAB approval
    approval, created = CABApproval.objects.get_or_create(
        deployment_intent=deployment,
        defaults={
            'decision': CABApproval.Decision.REJECTED,
            'approver': request.user,
            'comments': comments,
            'reviewed_at': timezone.now(),
            'is_demo': deployment.is_demo,
        }
    )
    
    if not created:
        approval.decision = CABApproval.Decision.REJECTED
        approval.approver = request.user
        approval.comments = comments
        approval.reviewed_at = timezone.now()
        approval.save()
    
    # Update deployment status
    deployment.status = DeploymentIntent.Status.REJECTED
    deployment.save()
    
    logger.info(
        f'Deployment rejected: {correlation_id}',
        extra={'correlation_id': str(correlation_id), 'approver': request.user.username}
    )
    
    return Response({'message': 'Deployment rejected'})


@api_view(['GET'])
@permission_classes([AllowAny])
def list_pending_approvals(request):
    """
    List pending CAB approvals.
    
    GET /api/v1/cab/pending/
    Query params: ?decision=PENDING (optional filter)
    """
    decision_filter = request.query_params.get('decision', 'PENDING')
    
    # Get deployments awaiting CAB approval
    deployments = apply_demo_filter(DeploymentIntent.objects.filter(
        status=DeploymentIntent.Status.AWAITING_CAB,
        requires_cab_approval=True
    ), request)
    
    approvals = []
    for deployment in deployments:
        # Get or create CAB approval record
        approval, _ = CABApproval.objects.get_or_create(
            deployment_intent=deployment,
            defaults={'decision': CABApproval.Decision.PENDING, 'is_demo': deployment.is_demo}
        )
        
        if approval.decision == decision_filter:
            approvals.append({
                'id': approval.id,
                'deployment_intent': str(deployment.correlation_id),
                'correlation_id': str(deployment.correlation_id),
                'decision': approval.decision,
                'approver': approval.approver.username if approval.approver else None,
                'comments': approval.comments,
                'conditions': approval.conditions,
                'submitted_at': approval.submitted_at.isoformat(),
                'reviewed_at': approval.reviewed_at.isoformat() if approval.reviewed_at else None,
                'app_name': deployment.app_name,
                'version': deployment.version,
                'risk_score': deployment.risk_score or 0,
            })
    
    return Response({'approvals': approvals})


@api_view(['GET'])
@permission_classes([AllowAny])  # Allow unauthenticated for demo mode
def list_approvals(request):
    """
    List all CAB approvals with optional filter.
    
    GET /api/v1/cab/approvals/?decision=APPROVED
    """
    decision_filter = request.query_params.get('decision')
    
    queryset = apply_demo_filter(CABApproval.objects.select_related('deployment_intent', 'approver').all(), request)
    
    if decision_filter:
        queryset = queryset.filter(decision=decision_filter)
    
    approvals = [{
        'id': approval.id,
        'deployment_intent': str(approval.deployment_intent.correlation_id),
        'correlation_id': str(approval.deployment_intent.correlation_id),
        'decision': approval.decision,
        'approver': approval.approver.username if approval.approver else None,
        'comments': approval.comments,
        'conditions': approval.conditions,
        'submitted_at': approval.submitted_at.isoformat(),
        'reviewed_at': approval.reviewed_at.isoformat() if approval.reviewed_at else None,
        'app_name': approval.deployment_intent.app_name,
        'version': approval.deployment_intent.version,
        'risk_score': approval.deployment_intent.risk_score or 0,
    } for approval in queryset.order_by('-reviewed_at', '-submitted_at')[:200]]  # Limit to 200, order by most recent
    
    return Response({'approvals': approvals})
