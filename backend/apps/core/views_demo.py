# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Admin demo data endpoints.
"""
from django.conf import settings
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from apps.core.demo_data import seed_demo_data, clear_demo_data, demo_data_stats
from apps.core.utils import get_demo_mode_enabled, set_demo_mode_enabled

# In development, allow any user (including unauthenticated) to access demo data endpoints
# In production, require IsAdminUser
DEMO_DATA_PERMISSION = AllowAny if settings.DEBUG else IsAdminUser

# In development, exempt CSRF for these API views to allow mock auth
# DRF's @api_view handles CSRF, but SessionAuthentication still enforces it
# This exemption allows unauthenticated requests in development
if settings.DEBUG:
    # Apply csrf_exempt to all views in development
    def exempt_csrf(view_func):
        return csrf_exempt(view_func)
else:
    def exempt_csrf(view_func):
        return view_func


@exempt_csrf
@api_view(['GET'])
@permission_classes([DEMO_DATA_PERMISSION])
def demo_data_stats_view(request):
    """
    Get demo data stats.

    GET /api/v1/admin/demo-data-stats
    """
    try:
        return Response({
            'counts': demo_data_stats(),
            'demo_mode_enabled': get_demo_mode_enabled(),
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@exempt_csrf
@api_view(['POST'])
@permission_classes([DEMO_DATA_PERMISSION])
def seed_demo_data_view(request):
    """
    Seed demo data (runs asynchronously via Celery for large datasets).

    POST /api/v1/admin/seed-demo-data
    
    For large datasets (>1000 assets), this operation runs in the background.
    Use the demo-data-stats endpoint to check progress.
    """
    import logging
    from apps.core.tasks import seed_demo_data_task
    
    logger = logging.getLogger(__name__)
    
    try:
        payload = request.data or {}
        clear_existing = payload.get('clear_existing', False)
        if isinstance(clear_existing, str):
            clear_existing = clear_existing.lower() in ['true', '1', 'yes']

        assets = int(payload.get('assets', 50000))
        applications = int(payload.get('applications', 5000))
        deployments = int(payload.get('deployments', 10000))
        users = int(payload.get('users', 1000))
        events = int(payload.get('events', 100000))
        batch_size = int(payload.get('batch_size', 1000))
        
        # For small datasets, run synchronously for immediate feedback
        # For large datasets, run asynchronously to avoid timeouts
        total_items = assets + applications + deployments + events
        use_async = total_items > 5000
        
        if use_async:
            logger.info(
                f'Queueing async demo data seed task: assets={assets}, applications={applications}, '
                f'deployments={deployments}, users={users}, events={events}, clear_existing={clear_existing}'
            )
            
            # Queue the task
            task = seed_demo_data_task.delay(
                assets=assets,
                applications=applications,
                deployments=deployments,
                users=users,
                events=events,
                clear_existing=bool(clear_existing),
                batch_size=batch_size,
            )
            
            return Response({
                'status': 'queued',
                'message': 'Demo data seeding started in background. Check demo-data-stats endpoint for progress.',
                'task_id': str(task.id),
            }, status=status.HTTP_202_ACCEPTED)
        else:
            # Run synchronously for small datasets
            logger.info(
                f'Starting synchronous demo data seed: assets={assets}, applications={applications}, '
                f'deployments={deployments}, users={users}, events={events}, clear_existing={clear_existing}'
            )
            
            results = seed_demo_data(
                assets=assets,
                applications=applications,
                deployments=deployments,
                users=users,
                events=events,
                clear_existing=bool(clear_existing),
                batch_size=batch_size,
            )

            logger.info(f'Demo data seed completed successfully: {results}')
            return Response({'status': 'success', 'counts': results}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f'Error seeding demo data: {e}', exc_info=True)
        return Response(
            {'status': 'error', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@exempt_csrf
@api_view(['DELETE'])
@permission_classes([DEMO_DATA_PERMISSION])
def clear_demo_data_view(request):
    """
    Clear demo data only.

    DELETE /api/v1/admin/clear-demo-data
    """
    results = clear_demo_data()
    return Response({'status': 'success', 'counts': results}, status=status.HTTP_200_OK)


@exempt_csrf
@api_view(['GET', 'POST'])
@permission_classes([DEMO_DATA_PERMISSION])
def demo_mode_view(request):
    """
    Get or set demo mode.

    GET /api/v1/admin/demo-mode
    POST /api/v1/admin/demo-mode { "enabled": true }
    """
    try:
        if request.method == 'POST':
            enabled = request.data.get('enabled', False)
            if isinstance(enabled, str):
                enabled = enabled.lower() in ['true', '1', 'yes']
            current = set_demo_mode_enabled(enabled)
            return Response({'demo_mode_enabled': current})

        return Response({'demo_mode_enabled': get_demo_mode_enabled()})
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@exempt_csrf
@api_view(['GET'])
@permission_classes([DEMO_DATA_PERMISSION])
def csrf_token_view(request):
    """
    Get CSRF token for frontend requests.
    
    GET /api/v1/admin/csrf-token
    """
    token = get_token(request)
    return Response({'csrf_token': token})
