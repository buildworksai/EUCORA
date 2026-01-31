# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Knowledge app configuration.
"""

from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    """Knowledge app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.knowledge"
    verbose_name = "Knowledge"
