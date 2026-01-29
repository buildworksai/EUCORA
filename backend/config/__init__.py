# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django configuration package for EUCORA Control Plane.

This module ensures Celery is loaded when Django starts.
Also initializes observability (distributed tracing, metrics).
"""
import os

from apps.core.observability import init_metrics, init_tracing

from .celery import app as celery_app

__all__ = ("celery_app",)

# Initialize observability (tracing and metrics)
if os.getenv("OTEL_ENABLED", "true").lower() == "true":
    try:
        init_tracing("eucora-control-plane")
        init_metrics("eucora-control-plane")
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to initialize observability: {str(e)}")
