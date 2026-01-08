# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for background integration sync operations.
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging
from apps.integrations.models import ExternalSystem, IntegrationSyncLog
from apps.integrations.services import get_integration_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
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
        logger.error(f'ExternalSystem with id {system_id} not found')
        return {'status': 'failed', 'error': 'System not found'}
    
    if not system.is_enabled:
        logger.info(f'Skipping sync for disabled system: {system.name}')
        return {'status': 'skipped', 'reason': 'System disabled'}
    
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
        sync_log.records_fetched = result.get('fetched', 0)
        sync_log.records_created = result.get('created', 0)
        sync_log.records_updated = result.get('updated', 0)
        sync_log.records_failed = result.get('failed', 0)
        sync_log.save()
        
        # Update system status
        system.last_sync_at = timezone.now()
        system.last_sync_status = 'success'
        system.save(update_fields=['last_sync_at', 'last_sync_status'])
        
        logger.info(
            f'Sync completed for {system.name}: '
            f'{sync_log.records_created} created, '
            f'{sync_log.records_updated} updated'
        )
        
        return {
            'status': 'success',
            'records_fetched': sync_log.records_fetched,
            'records_created': sync_log.records_created,
            'records_updated': sync_log.records_updated,
        }
    
    except ValueError as e:
        # Service not found or configuration error
        sync_log.sync_completed_at = timezone.now()
        sync_log.status = IntegrationSyncLog.SyncStatus.FAILED
        sync_log.error_message = str(e)
        sync_log.error_details = {'error_type': 'ValueError'}
        sync_log.save()
        
        system.last_sync_status = 'failed'
        system.save(update_fields=['last_sync_status'])
        
        logger.error(f'Sync failed for {system.name}: {e}')
        return {'status': 'failed', 'error': str(e)}
    
    except Exception as e:
        # Other errors - retry with exponential backoff
        error_classification = 'permanent'  # Default
        try:
            service = get_integration_service(system.type)
            error_classification = service._classify_error(e)
        except:
            pass
        
        sync_log.sync_completed_at = timezone.now()
        sync_log.status = IntegrationSyncLog.SyncStatus.FAILED
        sync_log.error_message = str(e)
        sync_log.error_details = {
            'error_type': type(e).__name__,
            'error_classification': error_classification,
        }
        sync_log.save()
        
        system.last_sync_status = 'failed'
        system.save(update_fields=['last_sync_status'])
        
        logger.error(f'Sync failed for {system.name}: {e}', exc_info=True)
        
        # Retry if transient error
        if error_classification == 'transient':
            countdown = 60 * (2 ** self.request.retries)  # Exponential backoff
            logger.info(f'Retrying sync for {system.name} in {countdown} seconds')
            raise self.retry(exc=e, countdown=countdown)
        
        return {'status': 'failed', 'error': str(e)}


@shared_task
def sync_all_integrations():
    """
    Periodic task to sync all enabled integrations.
    
    This task is scheduled by Celery Beat to run periodically.
    """
    enabled_systems = ExternalSystem.objects.filter(is_enabled=True, is_demo=False)
    
    logger.info(f'Starting sync for {enabled_systems.count()} enabled integrations')
    
    for system in enabled_systems:
        # Queue individual sync tasks
        sync_external_system.delay(str(system.id))
    
    return {'status': 'queued', 'count': enabled_systems.count()}

