# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Change Communications app configuration.
"""
from django.apps import AppConfig


class ChangeCommunicationsConfig(AppConfig):
    """Change Communications Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.change_communications"
    verbose_name = "Change Communications"

    def ready(self) -> None:
        """Import signals when app is ready."""
