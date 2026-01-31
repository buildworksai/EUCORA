# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
from django.apps import AppConfig


class KbTriageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.kb_triage"
    verbose_name = "KB & Triage Agent"
