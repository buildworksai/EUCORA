# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Discovery Agent app configuration.
"""
from django.apps import AppConfig


class DiscoveryAgentConfig(AppConfig):
    """Discovery Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.discovery_agent"
    verbose_name = "Discovery Agent"

    def ready(self) -> None:
        """Import signals when app is ready."""
        pass
