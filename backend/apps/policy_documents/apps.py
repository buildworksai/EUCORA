# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Documents app configuration.
"""

from django.apps import AppConfig


class PolicyDocumentsConfig(AppConfig):
    """Policy Documents app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.policy_documents"
    verbose_name = "Policy Documents"
