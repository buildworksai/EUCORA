# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
from django.apps import AppConfig


class PlanningAgentConfig(AppConfig):
    """Planning Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.planning_agent"
    verbose_name = "Planning Agent"
