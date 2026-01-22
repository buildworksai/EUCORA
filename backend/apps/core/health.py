# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Health check endpoints for Kubernetes liveness and readiness probes.

Provides comprehensive health checks for all external dependencies:
- Database connectivity and query latency
- Redis cache connectivity and latency
- Celery worker availability
- MinIO object store connectivity
- External service circuit breaker status
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import logging
import time

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


def check_database_health():
    """
    Check database connectivity and query latency.
    
    Returns:
        dict with 'status', 'latency_ms'
    """
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        latency = int((time.time() - start) * 1000)
        return {
            'status': 'healthy',
            'latency_ms': latency,
        }
    except Exception as e:
        logger.error(f'Database health check failed: {e}', exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e)[:100],
        }


def check_redis_health():
    """
    Check Redis connectivity and ping latency.
    
    Returns:
        dict with 'status', 'latency_ms'
    """
    try:
        start = time.time()
        cache.set('health_check_redis', 'ok', 10)
        result = cache.get('health_check_redis')
        latency = int((time.time() - start) * 1000)
        
        if result == 'ok':
            return {
                'status': 'healthy',
                'latency_ms': latency,
            }
        else:
            return {
                'status': 'unhealthy',
                'error': 'Cache get failed',
            }
    except Exception as e:
        logger.error(f'Redis health check failed: {e}', exc_info=True)
        return {
            'status': 'unhealthy',
            'error': str(e)[:100],
        }


def check_celery_health():
    """
    Check Celery worker availability.
    
    Returns:
        dict with 'status', 'active_workers', 'active_tasks'
    """
    try:
        # Use Celery app from django-celery-beat configuration
        from django.conf import settings
        from celery import Celery
        from celery.app.control import Inspect
        
        # Get Celery app from configuration
        celery_app = Celery()
        celery_app.config_from_object('django.conf:settings', namespace='CELERY')
        
        inspector = Inspect(app=celery_app)
        
        # Get active workers and tasks
        active_workers = inspector.active()
        if not active_workers:
            return {
                'status': 'degraded',
                'active_workers': 0,
                'active_tasks': 0,
                'message': 'No Celery workers available',
            }
        
        active_task_count = sum(len(tasks) for tasks in active_workers.values())
        
        return {
            'status': 'healthy',
            'active_workers': len(active_workers),
            'active_tasks': active_task_count,
        }
    except Exception as e:
        logger.error(f'Celery health check failed: {e}', exc_info=True)
        return {
            'status': 'degraded',
            'error': str(e)[:100],
        }


def check_minio_health():
    """
    Check MinIO object store connectivity.
    
    Returns:
        dict with 'status', 'latency_ms'
    """
    try:
        from minio import Minio
        from django.conf import settings
        
        minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        
        start = time.time()
        # List buckets to test connectivity
        minio_client.list_buckets()
        latency = int((time.time() - start) * 1000)
        
        return {
            'status': 'healthy',
            'latency_ms': latency,
        }
    except ImportError:
        # MinIO not installed, mark as degraded
        logger.warning('MinIO client not installed')
        return {
            'status': 'degraded',
            'error': 'MinIO client not installed',
        }
    except Exception as e:
        logger.error(f'MinIO health check failed: {e}', exc_info=True)
        return {
            'status': 'degraded',
            'error': str(e)[:100],
        }


def check_circuit_breaker_health():
    """
    Check circuit breaker status summary.
    
    Returns:
        dict with 'status', 'open_count', 'total'
    """
    try:
        from apps.core.circuit_breaker import get_all_breaker_status
        
        breaker_status = get_all_breaker_status()
        total = len(breaker_status)
        open_count = sum(1 for b in breaker_status.values() if b.get('opened', False))
        
        return {
            'status': 'healthy' if open_count == 0 else 'degraded',
            'open_count': open_count,
            'total': total,
        }
    except Exception as e:
        logger.error(f'Circuit breaker health check failed: {e}', exc_info=True)
        return {
            'status': 'degraded',
            'error': str(e)[:100],
        }


def comprehensive_health_check(request):
    """
    Comprehensive health check endpoint.
    
    Verifies all external dependencies and returns detailed status.
    Used for operational visibility and health monitoring.
    
    Returns:
        JSON response with status, timestamp, and detailed checks
        Status codes:
        - 200: All healthy
        - 503: One or more checks degraded/unhealthy
    """
    import json
    from datetime import datetime, timezone
    
    checks = {
        'database': check_database_health(),
        'redis': check_redis_health(),
        'celery': check_celery_health(),
        'minio': check_minio_health(),
        'circuit_breakers': check_circuit_breaker_health(),
    }
    
    # Determine overall status
    statuses = [c.get('status', 'unknown') for c in checks.values()]
    if 'unhealthy' in statuses:
        overall_status = 'unhealthy'
        status_code = 503
    elif 'degraded' in statuses:
        overall_status = 'degraded'
        status_code = 503
    else:
        overall_status = 'healthy'
        status_code = 200
    
    response = {
        'status': overall_status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': checks,
    }
    
    return JsonResponse(response, status=status_code)


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

