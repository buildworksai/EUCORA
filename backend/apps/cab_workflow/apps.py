# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow app configuration.
"""
from django.apps import AppConfig


class CABWorkflowConfig(AppConfig):
    """CAB Workflow app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cab_workflow"
    verbose_name = "EUCORA CAB Workflow"
