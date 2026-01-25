# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Event Store app configuration.
"""
from django.apps import AppConfig


class EventStoreConfig(AppConfig):
    """Event Store app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.event_store"
    verbose_name = "EUCORA Event Store"
