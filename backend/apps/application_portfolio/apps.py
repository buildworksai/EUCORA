# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Django app configuration for Application Portfolio."""
from django.apps import AppConfig


class ApplicationPortfolioConfig(AppConfig):
    """Configuration for the Application Portfolio app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.application_portfolio"
    verbose_name = "Application Portfolio"

    def ready(self) -> None:
        """Import signals when app is ready."""
        pass  # Add signal imports here when needed
