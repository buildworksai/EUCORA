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
import logging

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
    return Response({'status': 'alive'})
