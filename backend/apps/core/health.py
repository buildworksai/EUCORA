# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Health check endpoints for Kubernetes liveness and readiness probes.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


def liveness_check(request):
    """
    Kubernetes liveness probe.
    
    Returns 200 if the application is running (even if degraded).
    Kubernetes will restart the pod if this fails.
    """
    return JsonResponse({'status': 'alive'}, status=200)


def readiness_check(request):
    """
    Kubernetes readiness probe.
    
    Returns 200 only if the application is ready to serve traffic:
    - Database connection works
    - Redis cache works
    - Critical services available
    
    Kubernetes will stop sending traffic if this fails.
    """
    checks = {
        'database': False,
        'cache': False,
        'status': 'degraded',
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            checks['database'] = True
    except Exception as e:
        logger.error(f'Database health check failed: {e}')
        checks['database'] = False
    
    # Check Redis cache
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            checks['cache'] = True
    except Exception as e:
        logger.error(f'Cache health check failed: {e}')
        checks['cache'] = False
    
    # Determine overall status
    if checks['database'] and checks['cache']:
        checks['status'] = 'healthy'
        status_code = 200
    else:
        checks['status'] = 'degraded'
        status_code = 503  # Service Unavailable
    
    return JsonResponse(checks, status=status_code)

