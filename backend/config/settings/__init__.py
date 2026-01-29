# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
EUCORA Control Plane settings module.

Automatically loads the correct settings based on DJANGO_SETTINGS_MODULE environment variable.
"""
import os

# Default to development settings if not specified
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
