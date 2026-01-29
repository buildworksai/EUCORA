# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for agent management.

Periodic tasks for:
- Agent health monitoring
- Stale task timeouts
- Offline queue processing
"""
from celery import shared_task

from .services import AgentManagementService


@shared_task
def check_agent_health():
    """
    Check agent health and mark offline agents.

    Runs every 5 minutes via Celery Beat.
    """
    service = AgentManagementService()
    return service.check_agent_health()


@shared_task
def timeout_stale_tasks():
    """
    Timeout tasks that have been running too long.

    Runs every 10 minutes via Celery Beat.
    """
    service = AgentManagementService()
    return service.timeout_stale_tasks()
