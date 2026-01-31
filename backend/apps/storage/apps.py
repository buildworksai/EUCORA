# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django app configuration for Storage.
"""
from django.apps import AppConfig


class StorageConfig(AppConfig):
    """Configuration for Storage app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.storage"
    verbose_name = "Storage"
