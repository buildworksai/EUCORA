# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Integrations app configuration.
"""
from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    """Integrations app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.integrations'
    verbose_name = 'EUCORA Integrations'

