# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django app configuration for license_management.
"""
from django.apps import AppConfig


class LicenseManagementConfig(AppConfig):
    """Configuration for license_management app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.license_management"
    verbose_name = "License Management"
