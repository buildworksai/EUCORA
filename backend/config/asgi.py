# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ASGI config for EUCORA Control Plane.

Exposes the ASGI callable as a module-level variable named ``application``.
Supports async views and WebSocket connections (future).
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_asgi_application()
