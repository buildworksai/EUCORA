# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Prometheus metrics endpoint.

Exposes metrics at /api/v1/metrics/ for Prometheus scraping.
"""
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, REGISTRY
import logging

logger = logging.getLogger(__name__)


@require_http_methods(['GET'])
def metrics_endpoint(request):
    """
    Prometheus metrics endpoint.
    
    Returns all registered metrics in Prometheus text format.
    This endpoint should be scraped by Prometheus at regular intervals.
    
    Args:
        request: HTTP request
        
    Returns:
        HttpResponse with Prometheus format metrics
    """
    try:
        metrics_data = generate_latest(REGISTRY)
        return HttpResponse(
            metrics_data,
            content_type=CONTENT_TYPE_LATEST,
            charset='utf-8'
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}", exc_info=True)
        return HttpResponse(
            "Error generating metrics",
            status=500,
            content_type='text/plain'
        )
