# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ASGI config for EUCORA Control Plane.

Exposes the ASGI callable as a module-level variable named ``application``.
Supports async views and WebSocket connections via Django Channels.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import routing after Django setup
# Try to configure WebSocket support if channels is installed
try:
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.security.websocket import AllowedHostsOriginValidator

    from apps.ai_agents.workflows.routing import websocket_urlpatterns

    application = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            "websocket": AllowedHostsOriginValidator(
                URLRouter(websocket_urlpatterns),
            ),
        }
    )
except ImportError:
    # Fallback if Channels or WebSocket routing not available
    # App will work without WebSocket support
    application = django_asgi_app
