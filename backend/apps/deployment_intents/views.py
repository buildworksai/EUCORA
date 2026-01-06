# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Deployment Intent views for orchestration.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import DeploymentIntent, RingDeployment
from apps.policy_engine.services import calculate_risk_score
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_deployment(request):
    """
    Create deployment intent with risk assessment.
    
    POST /api/v1/deployments/
    Body: {
        "app_name": "...",
        "version": "...",
        "target_ring": "LAB",
        "evidence_pack": {...}
    }
    """
    app_name = request.data.get('app_name')
    version = request.data.get('version')
    target_ring = request.data.get('target_ring')
    evidence_pack = request.data.get('evidence_pack', {})
    
    if not all([app_name, version, target_ring]):
        return Response(
            {'error': 'app_name, version, and target_ring are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate risk score
    try:
        risk_result = calculate_risk_score(evidence_pack, request.correlation_id)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Create deployment intent
    deployment = DeploymentIntent.objects.create(
        app_name=app_name,
        version=version,
        target_ring=target_ring,
        evidence_pack_id=request.correlation_id,
        risk_score=risk_result['risk_score'],
        requires_cab_approval=risk_result['requires_cab_approval'],
        status=DeploymentIntent.Status.AWAITING_CAB if risk_result['requires_cab_approval'] else DeploymentIntent.Status.APPROVED,
        submitter=request.user,
    )
    
    logger.info(
        f'Deployment intent created: {deployment.correlation_id}',
        extra={'correlation_id': str(deployment.correlation_id), 'risk_score': risk_result['risk_score']}
    )
    
    return Response({
        'correlation_id': str(deployment.correlation_id),
        'status': deployment.status,
        'risk_score': risk_result['risk_score'],
        'requires_cab_approval': risk_result['requires_cab_approval'],
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_deployments(request):
    """
    List deployment intents with filters.
    
    GET /api/v1/deployments/?status=PENDING&ring=LAB
    """
    queryset = DeploymentIntent.objects.all()
    
    # Filters
    status_filter = request.query_params.get('status')
    ring_filter = request.query_params.get('ring')
    
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if ring_filter:
        queryset = queryset.filter(target_ring=ring_filter)
    
    deployments = [{
        'correlation_id': str(d.correlation_id),
        'app_name': d.app_name,
        'version': d.version,
        'target_ring': d.target_ring,
        'status': d.status,
        'risk_score': d.risk_score,
        'created_at': d.created_at.isoformat(),
    } for d in queryset[:100]]  # Limit to 100
    
    return Response({'deployments': deployments})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deployment(request, correlation_id):
    """
    Get deployment intent details.
    
    GET /api/v1/deployments/{correlation_id}/
    """
    try:
        deployment = DeploymentIntent.objects.get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({'error': 'Deployment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'correlation_id': str(deployment.correlation_id),
        'app_name': deployment.app_name,
        'version': deployment.version,
        'target_ring': deployment.target_ring,
        'status': deployment.status,
        'risk_score': deployment.risk_score,
        'requires_cab_approval': deployment.requires_cab_approval,
        'submitter': deployment.submitter.username,
        'created_at': deployment.created_at.isoformat(),
    })
