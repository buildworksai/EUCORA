# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Deployment Intent views for orchestration.
"""
from collections import defaultdict
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import DeploymentIntent, RingDeployment
from apps.policy_engine.services import calculate_risk_score
from apps.core.utils import apply_demo_filter, get_demo_mode_enabled
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
        is_demo=get_demo_mode_enabled(),
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
    queryset = apply_demo_filter(DeploymentIntent.objects.all(), request)
    
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
@permission_classes([AllowAny])
def list_applications_with_versions(request):
    """
    Return application-centric view of deployments grouped by version.

    GET /api/v1/deployments/applications
    Optional query params:
      - app_name: case-insensitive contains filter
      - status: filter by deployment status
      - ring: filter by target ring
    """
    queryset = apply_demo_filter(DeploymentIntent.objects.all(), request)

    status_filter = request.query_params.get('status')
    ring_filter = request.query_params.get('ring')
    app_filter = request.query_params.get('app_name')

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if ring_filter:
        queryset = queryset.filter(target_ring=ring_filter)
    if app_filter:
        queryset = queryset.filter(app_name__icontains=app_filter)

    # Order newest-first within each app to compute latest version reliably
    queryset = queryset.order_by('app_name', '-created_at')

    applications = {}

    for deployment in queryset:
        app_entry = applications.get(deployment.app_name)
        if not app_entry:
            app_entry = {
                'app_name': deployment.app_name,
                'latest_version': deployment.version,
                'deployment_count': 0,
                'versions': {},
            }
            applications[deployment.app_name] = app_entry

        version_entry = app_entry['versions'].get(deployment.version)
        if not version_entry:
            version_entry = {
                'version': deployment.version,
                'latest_created_at': deployment.created_at,
                'deployments': [],
            }
            app_entry['versions'][deployment.version] = version_entry

        version_entry['deployments'].append({
            'correlation_id': str(deployment.correlation_id),
            'target_ring': deployment.target_ring,
            'status': deployment.status,
            'risk_score': deployment.risk_score,
            'requires_cab_approval': deployment.requires_cab_approval,
            'created_at': deployment.created_at.isoformat(),
        })

        app_entry['deployment_count'] += 1

    application_list = []
    for app_data in applications.values():
        versions = list(app_data['versions'].values())
        versions.sort(key=lambda v: v['latest_created_at'], reverse=True)

        application_list.append({
            'app_name': app_data['app_name'],
            'latest_version': app_data['latest_version'],
            'deployment_count': app_data['deployment_count'],
            'versions': [
                {
                    'version': version['version'],
                    'latest_created_at': version['latest_created_at'].isoformat(),
                    'deployments': version['deployments'],
                }
                for version in versions
            ],
        })

    application_list.sort(key=lambda app: app['app_name'].lower())

    return Response({'applications': application_list})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_deployment(request, correlation_id):
    """
    Get deployment intent details.
    
    GET /api/v1/deployments/{correlation_id}/
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
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
