# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CMDB Integration app configuration.
"""
from django.apps import AppConfig


class CmdbIntegrationConfig(AppConfig):
    """CMDB Integration Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cmdb_integration"
    verbose_name = "CMDB Integration"

    def ready(self) -> None:
        """Import signals when app is ready."""
        pass
