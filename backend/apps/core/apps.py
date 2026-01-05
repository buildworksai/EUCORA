# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core app configuration.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'EUCORA Core'
