# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
from django.apps import AppConfig


class SLAGovernanceConfig(AppConfig):
    """SLA Governance Agent app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sla_governance"
    verbose_name = "SLA Governance Agent"
