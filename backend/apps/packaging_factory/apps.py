# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django app configuration for packaging_factory.
"""
from django.apps import AppConfig


class PackagingFactoryConfig(AppConfig):
    """Configuration for packaging_factory app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.packaging_factory"
    verbose_name = "Packaging Factory"
