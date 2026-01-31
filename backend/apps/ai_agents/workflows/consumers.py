# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
WebSocket consumers for real-time workflow execution updates.

Note: Requires Django Channels to be installed and configured.
This is a placeholder implementation that can be activated when Channels is added.
"""
import json
import logging

logger = logging.getLogger(__name__)

# WebSocket consumer implementation
# This requires Django Channels to be installed:
# pip install channels channels-redis
#
# Then configure in settings.py:
# INSTALLED_APPS += ['channels']
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('127.0.0.1', 6379)],
#         },
#     },
# }
#
# And update asgi.py to use ProtocolTypeRouter

try:  # noqa: C901
    from channels.generic.websocket import AsyncWebsocketConsumer

    class WorkflowExecutionConsumer(AsyncWebsocketConsumer):
        """
        WebSocket consumer for workflow execution updates.

        Clients connect to: ws://host/ws/ai/executions/{execution_id}/
        """

        async def connect(self):
            """Handle WebSocket connection."""
            self.execution_id = self.scope["url_route"]["kwargs"]["execution_id"]
            self.room_group_name = f"workflow_execution_{self.execution_id}"

            # Join room group
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)

            await self.accept()

            logger.info(f"WebSocket connected for workflow execution {self.execution_id}")

        async def disconnect(self, close_code):
            """Handle WebSocket disconnection."""
            # Leave room group
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

            logger.info(f"WebSocket disconnected for workflow execution {self.execution_id}")

        async def receive(self, text_data):
            """Handle WebSocket message from client."""
            try:
                data = json.loads(text_data)
                message_type = data.get("type")

                if message_type == "ping":
                    await self.send(text_data=json.dumps({"type": "pong"}))
                else:
                    logger.warning(f"Unknown message type: {message_type}")

            except json.JSONDecodeError:
                logger.error("Invalid JSON received via WebSocket")

        async def workflow_step_update(self, event):
            """Send workflow step update to WebSocket."""
            await self.send(text_data=json.dumps(event["data"]))

        async def workflow_status_update(self, event):
            """Send workflow status update to WebSocket."""
            await self.send(text_data=json.dumps(event["data"]))

except ImportError:
    # Django Channels not installed - create stub class
    logger.warning("Django Channels not installed. WebSocket support disabled.")

    class WorkflowExecutionConsumer:
        """Stub consumer when Channels is not available."""


def broadcast_workflow_update(execution_id: str, update_type: str, data: dict) -> None:
    """
    Broadcast workflow update to connected WebSocket clients.

    Args:
        execution_id: Workflow execution ID
        update_type: Type of update ('step_update' or 'status_update')
        data: Update data to send
    """
    try:
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if channel_layer:
            group_name = f"workflow_execution_{execution_id}"
            channel_layer.group_send(
                group_name,
                {
                    "type": f"workflow_{update_type}",
                    "data": {
                        "execution_id": execution_id,
                        "update_type": update_type,
                        **data,
                    },
                },
            )
    except ImportError:
        # Channels not installed - silently skip
        pass
    except Exception as e:
        logger.error(f"Error broadcasting workflow update: {e}")
