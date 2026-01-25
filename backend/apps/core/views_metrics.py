# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Prometheus metrics endpoint.

Exposes metrics at /api/v1/metrics/ for Prometheus scraping.
"""
import logging
import os

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, CollectorRegistry, generate_latest
from prometheus_client.multiprocess import MultiProcessCollector

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
def metrics_endpoint(request):
    """
    Prometheus metrics endpoint.

    Returns all registered metrics in Prometheus text format.
    This endpoint should be scraped by Prometheus at regular intervals.

    Supports both single-process and multiprocess modes:
    - Single process (development): Uses default REGISTRY
    - Multiprocess (production): Uses PROMETHEUS_MULTIPROC_DIR if set

    Args:
        request: HTTP request

    Returns:
        HttpResponse with Prometheus format metrics
    """
    try:
        # Check if multiprocess mode is enabled
        prometheus_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")

        if prometheus_multiproc_dir and os.path.isdir(prometheus_multiproc_dir):
            # Multiprocess mode - aggregate metrics from all worker processes
            registry = CollectorRegistry()
            MultiProcessCollector(registry)
            metrics_data = generate_latest(registry)
        else:
            # Single process mode - use default registry
            metrics_data = generate_latest(REGISTRY)

        return HttpResponse(metrics_data, content_type=CONTENT_TYPE_LATEST, charset="utf-8")
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}", exc_info=True)
        return HttpResponse("Error generating metrics", status=500, content_type="text/plain")
