# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Deployment Intents app configuration.
"""
from django.apps import AppConfig


class DeploymentIntentsConfig(AppConfig):
    """Deployment Intents app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.deployment_intents'
    verbose_name = 'EUCORA Deployment Intents'
