# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django app configuration for ai_strategy.
"""
from django.apps import AppConfig


class AiStrategyConfig(AppConfig):
    """Configuration for ai_strategy app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ai_strategy"
    verbose_name = "AI Strategy"
