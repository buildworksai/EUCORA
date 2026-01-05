# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Custom middleware for correlation ID injection and logging.
"""
import uuid
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(MiddlewareMixin):
    """
    Middleware to inject correlation_id into request and response.
    
    Correlation IDs enable end-to-end tracing across all system components:
    - Extracts X-Correlation-ID from request headers (if present)
    - Generates new UUID if not present
    - Injects into request object for use in views/services
    - Adds to response headers for client-side tracking
    - Adds to logging context for structured logs
    """
    
    def process_request(self, request):
        """Extract or generate correlation ID and inject into request."""
        # Extract from header or generate new UUID
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Inject into request object
        request.correlation_id = correlation_id
        
        # Create logger adapter with correlation ID context
        request.logger = logging.LoggerAdapter(
            logging.getLogger('apps'),
            {'correlation_id': correlation_id}
        )
        
        # Log request with correlation ID
        request.logger.info(
            f'{request.method} {request.path}',
            extra={
                'method': request.method,
                'path': request.path,
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
            }
        )
        
    def process_response(self, request, response):
        """Add correlation ID to response headers."""
        if hasattr(request, 'correlation_id'):
            response['X-Correlation-ID'] = request.correlation_id
        return response
