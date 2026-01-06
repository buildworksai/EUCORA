# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django configuration package for EUCORA Control Plane.

This module ensures Celery is loaded when Django starts.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)

