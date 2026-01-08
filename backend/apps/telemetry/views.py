# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Telemetry views for health checks and metrics.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
import logging
import random

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Docker/Kubernetes.
    
    GET /api/v1/health/
    
    Returns:
        200: {"status": "healthy", "checks": {...}}
        503: {"status": "unhealthy", "checks": {...}}
    """
    checks = {}
    overall_healthy = True
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = {'status': 'healthy'}
    except Exception as e:
        checks['database'] = {'status': 'unhealthy', 'error': str(e)}
        overall_healthy = False
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            checks['cache'] = {'status': 'healthy'}
        else:
            checks['cache'] = {'status': 'unhealthy', 'error': 'Cache read/write failed'}
            overall_healthy = False
    except Exception as e:
        checks['cache'] = {'status': 'unhealthy', 'error': str(e)}
        overall_healthy = False
    
    # Application info
    checks['application'] = {
        'name': settings.EUCORA_BRANDING['APPLICATION_NAME'],
        'organization': settings.EUCORA_BRANDING['ORGANIZATION'],
        'version': '1.0.0',
    }
    
    response_data = {
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'checks': checks,
    }
    
    response_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(response_data, status=response_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness check for Kubernetes.
    
    GET /api/v1/health/ready
    
    Returns:
        200: {"status": "ready", "checks": {...}}
        503: {"status": "not_ready", "checks": {...}}
    """
    # Duplicate health check logic to avoid double-wrapping DRF Request
    checks = {}
    overall_healthy = True
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = {'status': 'healthy'}
    except Exception as e:
        checks['database'] = {'status': 'unhealthy', 'error': str(e)}
        overall_healthy = False
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        cache_value = cache.get('health_check')
        if cache_value == 'ok':
            checks['cache'] = {'status': 'healthy'}
        else:
            checks['cache'] = {'status': 'unhealthy', 'error': 'Cache read/write failed'}
            overall_healthy = False
    except Exception as e:
        checks['cache'] = {'status': 'unhealthy', 'error': str(e)}
        overall_healthy = False
    
    # Application info
    checks['application'] = {
        'name': settings.EUCORA_BRANDING['APPLICATION_NAME'],
        'organization': settings.EUCORA_BRANDING['ORGANIZATION'],
        'version': '1.0.0',
    }
    
    response_data = {
        'status': 'ready' if overall_healthy else 'not_ready',
        'checks': checks,
    }
    
    response_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(response_data, status=response_status)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness check for Kubernetes.
    
    GET /api/v1/health/live
    
    Returns:
        200: {"status": "alive"}
    """
    return Response({'status': 'alive'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def compliance_stats(request):
    """
    Get compliance statistics from seeded assets.
    
    GET /api/v1/health/compliance-stats
    
    Returns compliance metrics aggregated from assets:
    - Overall compliance score
    - Vulnerability distribution (mock for now)
    - OS distribution
    - Compliance trend over time (mock for now)
    """
    from apps.core.utils import apply_demo_filter
    from apps.connectors.models import Asset
    
    # Get assets with demo filter
    assets = apply_demo_filter(Asset.objects.all(), request)
    active_assets = assets.filter(status='Active')
    
    # Overall compliance score (average of active assets)
    avg_compliance = active_assets.aggregate(avg=Avg('compliance_score'))['avg'] or 0
    
    # OS distribution
    os_distribution = list(
        assets.values('os')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Format OS distribution for frontend
    os_dist_data = []
    os_colors = {
        'Windows 11': '#0078D7',
        'Windows 10': '#00BCF2',
        'macOS Sonoma': '#FF3B30',
        'macOS Ventura': '#FF3B30',
        'macOS': '#FF3B30',
        'Ubuntu 22.04': '#E95420',
        'Ubuntu': '#E95420',
        'Windows Server 2022': '#0078D7',
        'RHEL 9': '#EE0000',
        'RHEL': '#EE0000',
        'iOS 17': '#000000',
        'iOS 16': '#000000',
        'iOS': '#000000',
        'Android 14': '#3DDC84',
        'Android 13': '#3DDC84',
        'Android': '#3DDC84',
    }
    for os_item in os_distribution[:10]:  # Top 10 OS
        os_name = os_item['os']
        os_dist_data.append({
            'name': os_name,
            'value': os_item['count'],
            'color': os_colors.get(os_name, '#888888'),
        })
    
    # Calculate compliance trend using asset creation dates to simulate historical progression
    # Assets created earlier had lower compliance, newer assets have higher compliance
    compliance_trend = []
    weeks_back = 8
    
    # Calculate base score from oldest assets (simulating starting point)
    oldest_assets = active_assets.order_by('created_at')[:max(1, active_assets.count() // 4)]
    base_score = oldest_assets.aggregate(avg=Avg('compliance_score'))['avg'] if oldest_assets.exists() else avg_compliance - 5
    
    # Ensure base_score is reasonable
    base_score = max(60, min(95, base_score))
    
    # Calculate trend showing gradual improvement over time
    for i in range(weeks_back):
        week_start = timezone.now() - timedelta(days=(weeks_back - i) * 7)
        
        # Simulate gradual improvement: earlier weeks have lower scores
        # Progress from base_score to current avg_compliance
        progress = i / (weeks_back - 1) if weeks_back > 1 else 1.0
        week_score = base_score + (avg_compliance - base_score) * progress
        
        # Add some realistic variation (±2 points) to make it more dynamic
        variation = random.uniform(-2.0, 2.0)
        week_score = max(60, min(100, week_score + variation))
        
        # For the most recent week, use actual current average
        if i == weeks_back - 1:
            week_score = avg_compliance
        
        compliance_trend.append({
            'date': week_start.strftime('%b %d'),
            'score': round(week_score, 1),
        })
    
    # Vulnerability distribution - aggregate from evidence packs
    from apps.evidence_store.models import EvidencePack
    
    evidence_packs = apply_demo_filter(EvidencePack.objects.all(), request)
    
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for pack in evidence_packs:
        scan_results = pack.vulnerability_scan_results or {}
        if isinstance(scan_results, dict):
            critical_count += scan_results.get('critical', 0)
            high_count += scan_results.get('high', 0)
            medium_count += scan_results.get('medium', 0)
            low_count += scan_results.get('low', 0)
    
    vulnerability_data = [
        {'name': 'Critical', 'value': critical_count, 'color': '#E74C3C'},
        {'name': 'High', 'value': high_count, 'color': '#F39C12'},
        {'name': 'Medium', 'value': medium_count, 'color': '#F1C40F'},
        {'name': 'Low', 'value': low_count, 'color': '#3498DB'},
    ]
    
    # Policy conflicts - count deployments with high risk scores that require CAB approval
    from apps.deployment_intents.models import DeploymentIntent
    
    high_risk_deployments = apply_demo_filter(
        DeploymentIntent.objects.filter(requires_cab_approval=True, status__in=['PENDING', 'AWAITING_CAB', 'REJECTED']),
        request
    )
    policy_conflicts = high_risk_deployments.count()
    
    # Pending updates - count deployments in pending states
    pending_deployments = apply_demo_filter(
        DeploymentIntent.objects.filter(status__in=['PENDING', 'AWAITING_CAB', 'APPROVED']),
        request
    )
    pending_updates = pending_deployments.count()
    
    return Response({
        'overall_compliance': round(avg_compliance, 1),
        'critical_vulnerabilities': vulnerability_data[0]['value'],  # Critical count from vulnerability_data
        'policy_conflicts': policy_conflicts,
        'pending_updates': pending_updates,
        'compliance_trend': compliance_trend,
        'vulnerability_data': vulnerability_data,
        'os_distribution': os_dist_data,
        'total_assets': assets.count(),
        'active_assets': active_assets.count(),
    })
