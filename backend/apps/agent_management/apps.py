# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Agent Management application configuration.
"""
from django.apps import AppConfig


class AgentManagementConfig(AppConfig):
    """Configuration for agent management app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.agent_management"
    verbose_name = "Agent Management"

    def ready(self):
        """Import signal handlers when app is ready."""
        # Import signals if any
        pass
