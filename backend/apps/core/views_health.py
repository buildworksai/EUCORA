# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Health and resilience status API endpoints.

Provides visibility into circuit breaker states and system health.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
import logging

from apps.core.circuit_breaker import (
    get_all_breaker_status,
    get_breaker,
    reset_breaker,
    CircuitBreakerOpen,
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_circuit_breaker_status(request) -> Response:
    """
    Get status of all circuit breakers.
    
    Returns:
        JSON response with circuit breaker states:
        {
            "servicenow": {
                "state": "closed" | "open" | "half-open",
                "fail_counter": 0,
                "fail_max": 5,
                "opened": false,
                "reset_timeout": 60
            },
            ...
        }
    """
    try:
        breaker_status = get_all_breaker_status()
        
        # Add summary
        response = {
            'breakers': breaker_status,
            'summary': {
                'total': len(breaker_status),
                'open': sum(1 for b in breaker_status.values() if b['opened']),
                'closed': sum(1 for b in breaker_status.values() if not b['opened']),
            }
        }
        
        return Response(response, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(
            f'Error querying circuit breaker status: {e}',
            exc_info=True,
        )
        return Response(
            {'error': f'Failed to query circuit breaker status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_single_breaker_status(request, service_name: str) -> Response:
    """
    Get status of a specific circuit breaker.
    
    Args:
        service_name: Name of the service (e.g., 'servicenow', 'intune')
    
    Returns:
        JSON response with circuit breaker state
    """
    try:
        breaker = get_breaker(service_name)
        
        return Response({
            'service': service_name,
            'state': breaker.state.name,
            'fail_counter': breaker.fail_counter,
            'fail_max': breaker.fail_max,
            'opened': breaker.opened,
            'reset_timeout': breaker.reset_timeout,
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            f'Error querying circuit breaker status: {e}',
            extra={'service': service_name},
            exc_info=True,
        )
        return Response(
            {'error': f'Failed to query circuit breaker status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_circuit_breaker(request, service_name: str) -> Response:
    """
    Reset a circuit breaker to closed state.
    
    Requires admin privileges. Use with caution.
    
    Args:
        service_name: Name of the service to reset
    
    Returns:
        JSON response indicating reset status
    """
    try:
        reset_breaker(service_name)
        
        logger.warning(
            f'Circuit breaker manually reset',
            extra={
                'service': service_name,
                'user': request.user.username if request.user else 'anonymous',
            }
        )
        
        return Response({
            'service': service_name,
            'status': 'reset',
            'message': f'Circuit breaker for {service_name} has been reset to closed state',
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(
            f'Error resetting circuit breaker: {e}',
            extra={'service': service_name},
            exc_info=True,
        )
        return Response(
            {'error': f'Failed to reset circuit breaker: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
