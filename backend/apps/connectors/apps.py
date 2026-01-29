# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Connectors app configuration.
"""
from django.apps import AppConfig


class ConnectorsConfig(AppConfig):
    """Connectors app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.connectors"
    verbose_name = "EUCORA Connectors"
