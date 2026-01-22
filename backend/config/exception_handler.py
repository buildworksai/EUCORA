# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Custom DRF exception handler for error sanitization.

Sanitizes error responses to prevent exposure of internal details:
- No stack traces in client responses
- No SQL queries or database details
- No file paths or system information
- Always includes correlation_id for log lookup

Server-side logging includes full error context for debugging.
"""
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that sanitizes error responses.
    
    Never exposes:
    - Stack traces
    - SQL queries or table names
    - File paths
    - Internal variable values
    - Database connection strings
    - API keys or tokens
    
    Always exposes:
    - Correlation ID (for log lookup)
    - HTTP status code
    - User-friendly error message
    - Field validation errors (for 400 status)
    
    Args:
        exc: Exception instance
        context: Context dict with request, view, etc.
    
    Returns:
        Response with sanitized error details
    """
    
    # Extract correlation_id from request
    request = context.get('request')
    correlation_id = getattr(request, 'correlation_id', None) if request else None
    
    # Call the default exception handler first
    response = drf_exception_handler(exc, context)
    
    if response is None:
        # Unhandled exception - log fully, return generic 500
        logger.exception(
            'Unhandled exception',
            extra={'correlation_id': correlation_id},
            exc_info=True,
        )
        response = Response(
            {
                'error': 'Internal server error',
                'correlation_id': correlation_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return response
    
    # Sanitize the response based on status code
    status_code = response.status_code
    
    if status_code >= 500:
        # Server errors: generic message, log fully
        logger.error(
            f'{exc.__class__.__name__}: {str(exc)[:200]}',
            extra={'correlation_id': correlation_id},
            exc_info=True,
        )
        
        response.data = {
            'error': 'Internal server error',
            'correlation_id': correlation_id,
        }
    
    elif status_code >= 400:
        # Client errors: keep validation details but sanitize
        logger.warning(
            f'{exc.__class__.__name__}: {str(exc)[:200]}',
            extra={'correlation_id': correlation_id},
        )
        
        # Keep validation details for 400/422 but sanitize others
        if status_code in (400, 422):
            # For validation errors, keep fields but add correlation_id
            if isinstance(response.data, dict):
                response.data['correlation_id'] = correlation_id
            else:
                # If it's not a dict (shouldn't happen), wrap it
                response.data = {
                    'errors': response.data,
                    'correlation_id': correlation_id,
                }
        else:
            # 401, 403, 404, etc. - use generic message
            response.data = {
                'error': response.data.get('detail', f'Error (HTTP {status_code})'),
                'correlation_id': correlation_id,
            }
    
    else:
        # 2xx responses - add correlation_id if not present
        if 'correlation_id' not in response.data and isinstance(response.data, dict):
            response.data['correlation_id'] = correlation_id
    
    return response
