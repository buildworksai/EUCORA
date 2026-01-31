# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for DEX data synchronization.

Scheduled tasks for periodic sync of DEX metrics from 1E or mock provider.
"""
import asyncio
import logging

from celery import shared_task

from apps.integrations.dex.models import DEXProvider
from apps.integrations.dex.services.sync import DEXSyncService

logger = logging.getLogger(__name__)


@shared_task
def sync_dex_data():
    """
    Celery task to sync DEX data.

    Finds enabled provider and runs sync operation.
    """
    provider = DEXProvider.objects.filter(is_enabled=True).first()
    if not provider:
        logger.warning("No enabled DEX provider found, skipping sync")
        return

    try:
        service = DEXSyncService(provider)
        result = asyncio.run(service.sync())
        logger.info(
            f"DEX sync completed: {result.metrics_synced} metrics synced in {result.duration.total_seconds():.2f}s"
        )
        if result.errors:
            logger.warning(f"DEX sync had {len(result.errors)} errors")
        return {
            "status": "success",
            "metrics_synced": result.metrics_synced,
            "duration_seconds": result.duration.total_seconds(),
            "errors": result.errors,
        }
    except Exception as e:
        logger.error(f"DEX sync task failed: {e}", exc_info=True)
        raise
