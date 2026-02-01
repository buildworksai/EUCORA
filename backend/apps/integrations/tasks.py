# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for background integration sync operations.
"""
import logging

from celery import shared_task
from django.utils import timezone

from apps.integrations.models import ExternalSystem, IntegrationSyncLog
from apps.integrations.services import get_integration_service

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=600,
    time_limit=660,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def sync_external_system(self, system_id: str):
    """
    Background task to sync data from external system.

    Args:
        system_id: UUID of ExternalSystem to sync

    Returns:
        Dict with sync results
    """
    try:
        system = ExternalSystem.objects.get(id=system_id)
    except ExternalSystem.DoesNotExist:
        logger.error(f"ExternalSystem with id {system_id} not found")
        return {"status": "failed", "error": "System not found"}

    if not system.is_enabled:
        logger.info(f"Skipping sync for disabled system: {system.name}")
        return {"status": "skipped", "reason": "System disabled"}

    # Create sync log entry
    sync_log = IntegrationSyncLog.objects.create(
        system=system,
        sync_started_at=timezone.now(),
        status=IntegrationSyncLog.SyncStatus.RUNNING,
        correlation_id=system.correlation_id,
    )

    try:
        # Get appropriate service
        service = get_integration_service(system.type)

        # Perform sync
        result = service.sync(system)

        # Update sync log
        sync_log.sync_completed_at = timezone.now()
        sync_log.status = IntegrationSyncLog.SyncStatus.SUCCESS
        sync_log.records_fetched = result.get("fetched", 0)
        sync_log.records_created = result.get("created", 0)
        sync_log.records_updated = result.get("updated", 0)
        sync_log.records_failed = result.get("failed", 0)
        sync_log.save()

        # Update system status
        system.last_sync_at = timezone.now()
        system.last_sync_status = "success"
        system.save(update_fields=["last_sync_at", "last_sync_status"])

        logger.info(
            f"Sync completed for {system.name}: "
            f"{sync_log.records_created} created, "
            f"{sync_log.records_updated} updated"
        )

        return {
            "status": "success",
            "records_fetched": sync_log.records_fetched,
            "records_created": sync_log.records_created,
            "records_updated": sync_log.records_updated,
        }

    except ValueError as e:
        # Service not found or configuration error
        sync_log.sync_completed_at = timezone.now()
        sync_log.status = IntegrationSyncLog.SyncStatus.FAILED
        sync_log.error_message = str(e)
        sync_log.error_details = {"error_type": "ValueError"}
        sync_log.save()

        system.last_sync_status = "failed"
        system.save(update_fields=["last_sync_status"])

        logger.error(f"Sync failed for {system.name}: {e}")
        return {"status": "failed", "error": str(e)}

    except Exception as e:
        # Other errors - retry with exponential backoff
        error_classification = "permanent"  # Default
        try:
            service = get_integration_service(system.type)
            error_classification = service._classify_error(e)
        except Exception as classification_error:
            logger.warning(f"Failed to classify error for {system.name}: {classification_error}")

        sync_log.sync_completed_at = timezone.now()
        sync_log.status = IntegrationSyncLog.SyncStatus.FAILED
        sync_log.error_message = str(e)
        sync_log.error_details = {
            "error_type": type(e).__name__,
            "error_classification": error_classification,
        }
        sync_log.save()

        system.last_sync_status = "failed"
        system.save(update_fields=["last_sync_status"])

        logger.error(f"Sync failed for {system.name}: {e}", exc_info=True)

        # Retry if transient error
        if error_classification == "transient":
            countdown = 60 * (2**self.request.retries)  # Exponential backoff
            logger.info(f"Retrying sync for {system.name} in {countdown} seconds")
            raise self.retry(exc=e, countdown=countdown)

        return {"status": "failed", "error": str(e)}


@shared_task(
    bind=True,
    max_retries=3,
    soft_time_limit=300,
    time_limit=330,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def sync_all_integrations(self):
    """
    Periodic task to sync all enabled integrations.

    This task is scheduled by Celery Beat to run periodically.
    """
    try:
        enabled_systems = ExternalSystem.objects.filter(is_enabled=True, is_demo=False)
        system_count = enabled_systems.count()

        logger.info(f"Starting sync for {system_count} enabled integrations")

        queued_count = 0
        failed_count = 0

        for system in enabled_systems:
            try:
                # Queue individual sync tasks
                sync_external_system.delay(str(system.id))
                queued_count += 1
            except Exception as e:
                logger.error(f"Failed to queue sync for system {system.id}: {e}", exc_info=True)
                failed_count += 1

        logger.info(
            f"Sync queueing completed: {queued_count} queued, {failed_count} failed",
            extra={"queued": queued_count, "failed": failed_count},
        )

        return {
            "status": "completed",
            "queued": queued_count,
            "failed": failed_count,
            "total": system_count,
        }
    except Exception as e:
        logger.error(f"sync_all_integrations failed: {e}", exc_info=True)
        raise
