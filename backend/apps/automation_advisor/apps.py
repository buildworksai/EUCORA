# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Automation Advisor app configuration.
"""
from django.apps import AppConfig


class AutomationAdvisorConfig(AppConfig):
    """Automation Advisor Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.automation_advisor"
    verbose_name = "Automation Advisor"

    def ready(self) -> None:
        """Import signals when app is ready."""
