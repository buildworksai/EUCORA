# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
IAM Security app configuration.
"""
from django.apps import AppConfig


class IamSecurityConfig(AppConfig):
    """IAM Security Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.iam_security"
    verbose_name = "IAM Security"

    def ready(self) -> None:
        """Import signals when app is ready."""
        pass
