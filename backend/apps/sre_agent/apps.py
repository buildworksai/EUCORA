# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
from django.apps import AppConfig


class SreAgentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sre_agent"
    verbose_name = "SRE Agent"
