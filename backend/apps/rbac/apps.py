# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django app configuration for RBAC.
"""
from django.apps import AppConfig


class RbacConfig(AppConfig):
    """Configuration for RBAC app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rbac"
    verbose_name = "RBAC"
