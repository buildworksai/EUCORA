# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Event Store views for audit trail.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .models import DeploymentEvent
from apps.core.utils import apply_demo_filter, get_demo_mode_enabled
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_events(request):
    """
    List deployment events with filters.
    
    GET /api/v1/events/?correlation_id=...&event_type=...
    """
    queryset = apply_demo_filter(DeploymentEvent.objects.all(), request)
    
    # Filters
    correlation_id = request.query_params.get('correlation_id')
    event_type = request.query_params.get('event_type')
    
    if correlation_id:
        queryset = queryset.filter(correlation_id=correlation_id)
    if event_type:
        queryset = queryset.filter(event_type=event_type)
    
    events = [{
        'id': e.id,
        'correlation_id': str(e.correlation_id),
        'event_type': e.event_type,
        'event_data': e.event_data,
        'actor': e.actor,
        'created_at': e.created_at.isoformat(),
    } for e in queryset[:100]]  # Limit to 100
    
    return Response({'events': events})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_event(request):
    """
    Log deployment event (append-only).
    
    POST /api/v1/events/
    Body: {
        "correlation_id": "...",
        "event_type": "DEPLOYMENT_CREATED",
        "event_data": {...}
    }
    """
    event = DeploymentEvent.objects.create(
        correlation_id=request.data.get('correlation_id'),
        event_type=request.data.get('event_type'),
        event_data=request.data.get('event_data', {}),
        actor=request.user.username,
        is_demo=get_demo_mode_enabled(),
    )
    
    logger.info(
        f'Event logged: {event.event_type}',
        extra={'correlation_id': str(event.correlation_id), 'event_type': event.event_type}
    )
    
    return Response({'id': event.id, 'created_at': event.created_at.isoformat()})
