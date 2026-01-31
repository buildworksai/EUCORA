# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Request Coordination app configuration.
"""
from django.apps import AppConfig


class RequestCoordinationConfig(AppConfig):
    """Request Coordination Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.request_coordination"
    verbose_name = "Request Coordination"

    def ready(self) -> None:
        """Import signals when app is ready."""
        pass
