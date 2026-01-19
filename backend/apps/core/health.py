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


def demo_readiness_check(request):
    """
    Demo readiness check for customer demos.
    
    Returns 200 if demo data exists and demo mode is enabled.
    Used to verify system is ready for customer demonstrations.
    """
    checks = {
        'demo_mode_enabled': False,
        'demo_data_exists': False,
        'demo_data_counts': {},
        'status': 'not_ready',
    }
    
    try:
        # Check demo mode
        from apps.core.utils import get_demo_mode_enabled
        checks['demo_mode_enabled'] = get_demo_mode_enabled()
        
        # Check demo data
        from apps.core.demo_data import demo_data_stats
        stats = demo_data_stats()
        total = sum(stats.values())
        checks['demo_data_exists'] = total > 0
        checks['demo_data_counts'] = stats
        
        # Determine status
        if checks['demo_mode_enabled'] and checks['demo_data_exists']:
            checks['status'] = 'ready'
            status_code = 200
        elif checks['demo_data_exists'] and not checks['demo_mode_enabled']:
            checks['status'] = 'data_exists_but_demo_mode_disabled'
            checks['message'] = 'Demo data exists but demo mode is disabled. Enable it via /admin/demo-data'
            status_code = 200  # Still return 200, but with warning
        elif not checks['demo_data_exists']:
            checks['status'] = 'no_demo_data'
            checks['message'] = 'No demo data found. Seed data via /admin/demo-data or management command'
            status_code = 200  # Still return 200, but with warning
        else:
            checks['status'] = 'unknown'
            status_code = 200
            
    except Exception as e:
        logger.error(f'Demo readiness check failed: {e}', exc_info=True)
        checks['status'] = 'error'
        checks['error'] = str(e)
        status_code = 503
    
    return JsonResponse(checks, status=status_code)

