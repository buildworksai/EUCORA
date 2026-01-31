# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
WebSocket routing for workflow executions.

Requires Django Channels to be configured in asgi.py.
"""
from django.urls import re_path

try:
    from .consumers import WorkflowExecutionConsumer

    websocket_urlpatterns = [
        re_path(r"ws/ai/executions/(?P<execution_id>[0-9a-f-]+)/$", WorkflowExecutionConsumer.as_asgi()),
    ]
except ImportError:
    # Django Channels not installed - will be handled gracefully
    websocket_urlpatterns = []
