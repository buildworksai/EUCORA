# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Store app configuration.
"""
from django.apps import AppConfig


class EvidenceStoreConfig(AppConfig):
    """Evidence Store app configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.evidence_store'
    verbose_name = 'EUCORA Evidence Store'
