# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Django app configuration for DEX integration."""
from django.apps import AppConfig


class DEXConfig(AppConfig):
    """Configuration for DEX integration app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations.dex"
    verbose_name = "1E DEX Integration"

    def ready(self):
        """Import signals when app is ready."""
        try:
            import apps.integrations.dex.signals  # noqa: F401
        except ImportError:
            pass
