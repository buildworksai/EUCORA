# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Documentation Agent app configuration.
"""
from django.apps import AppConfig


class DocumentationAgentConfig(AppConfig):
    """Documentation Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documentation_agent"
    verbose_name = "Documentation Agent"

    def ready(self) -> None:
        """Import signals when app is ready."""
