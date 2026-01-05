# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Telemetry app configuration.
"""
from django.apps import AppConfig


class TelemetryConfig(AppConfig):
    """Telemetry app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.telemetry'
    verbose_name = 'EUCORA Telemetry'
