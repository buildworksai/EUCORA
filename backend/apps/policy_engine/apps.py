# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine app configuration.
"""
from django.apps import AppConfig


class PolicyEngineConfig(AppConfig):
    """Policy Engine app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.policy_engine'
    verbose_name = 'EUCORA Policy Engine'
