# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for deployment intent processing.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.deployment_intents.tasks.reconciliation_loop')
def reconciliation_loop():
    """
    Periodic reconciliation loop to detect drift between desired and actual state.
    
    Runs every hour to:
    1. Query execution plane state (Intune/Jamf/SCCM/etc.)
    2. Compare to desired deployment intents
    3. Emit drift events if mismatches found
    4. Trigger remediation workflows within policy constraints
    """
    from apps.deployment_intents.models import DeploymentIntent
    from apps.event_store.models import DeploymentEvent
    from apps.connectors.services import get_connector_service
    
    logger.info('Starting reconciliation loop')
    
    # Get active deployment intents
    active_intents = DeploymentIntent.objects.filter(
        status__in=['PENDING', 'IN_PROGRESS', 'COMPLETED']
    )
    
    drift_count = 0
    for intent in active_intents:
        try:
            # Query execution plane state
            connector_service = get_connector_service()
            health_result = connector_service.health_check(intent.execution_plane)
            
            if health_result['status'] != 'healthy':
                logger.warning(
                    f'Connector {intent.execution_plane} unhealthy, skipping reconciliation',
                    extra={'deployment_intent_id': intent.id}
                )
                continue
            
            # TODO: Implement actual state comparison logic
            # For now, log that reconciliation ran
            logger.debug(
                f'Reconciled deployment intent {intent.id}',
                extra={'deployment_intent_id': intent.id, 'execution_plane': intent.execution_plane}
            )
            
        except Exception as e:
            logger.error(
                f'Error during reconciliation for intent {intent.id}: {e}',
                extra={'deployment_intent_id': intent.id},
                exc_info=True
            )
    
    logger.info(f'Reconciliation loop completed. Processed {active_intents.count()} intents, found {drift_count} drift events')
    return {'processed': active_intents.count(), 'drift_count': drift_count}


@shared_task(name='apps.deployment_intents.tasks.deploy_to_connector', bind=True, max_retries=3, time_limit=300, soft_time_limit=270)
def deploy_to_connector(self, deployment_intent_id, connector_type):
    """
    Async task to deploy application to execution plane connector (Intune/Jamf/SCCM/Landscape/Ansible).
    
    Args:
        deployment_intent_id: UUID of deployment intent
        connector_type: Type of connector (intune, jamf, sccm, landscape, ansible)
    
    Returns:
        {'status': 'success' | 'failed', 'deployment_intent_id': ..., 'connector_type': ..., 'details': ...}
    """
    from apps.deployment_intents.models import DeploymentIntent
    from apps.connectors.services import get_connector_service
    from django.db import transaction
    
    try:
        deployment = DeploymentIntent.objects.select_related('submitter').get(id=deployment_intent_id)
    except DeploymentIntent.DoesNotExist:
        logger.error(f'Deployment intent not found: {deployment_intent_id}')
        return {'status': 'failed', 'error': 'Deployment intent not found', 'deployment_intent_id': str(deployment_intent_id)}
    
    try:
        # Get connector service
        connector_service = get_connector_service(connector_type)
        
        # Execute deployment
        result = connector_service.deploy(
            app_name=deployment.app_name,
            version=deployment.version,
            target_ring=deployment.target_ring,
            correlation_id=str(deployment.correlation_id),
        )
        
        # Update deployment status
        with transaction.atomic():
            deployment.status = DeploymentIntent.Status.DEPLOYING
            deployment.save()
        
        logger.info(
            f'Deployment to {connector_type} initiated',
            extra={
                'deployment_intent_id': str(deployment.correlation_id),
                'connector_type': connector_type,
                'result': result
            }
        )
        
        return {
            'status': 'success',
            'deployment_intent_id': str(deployment.correlation_id),
            'connector_type': connector_type,
            'details': result
        }
        
    except Exception as exc:
        logger.error(
            f'Failed to deploy to {connector_type}: {exc}',
            extra={'deployment_intent_id': str(deployment.correlation_id), 'connector_type': connector_type},
            exc_info=True
        )
        
        # Retry with exponential backoff (max 3 retries)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(name='apps.deployment_intents.tasks.execute_rollback', bind=True, max_retries=3, time_limit=300, soft_time_limit=270)
def execute_rollback(self, deployment_intent_id, connector_type):
    """
    Async task to rollback deployment from execution plane connector.
    
    Args:
        deployment_intent_id: UUID of deployment intent
        connector_type: Type of connector
    
    Returns:
        {'status': 'success' | 'failed', 'deployment_intent_id': ..., 'details': ...}
    """
    from apps.deployment_intents.models import DeploymentIntent
    from apps.connectors.services import get_connector_service
    from django.db import transaction
    
    try:
        deployment = DeploymentIntent.objects.select_related('submitter').get(id=deployment_intent_id)
    except DeploymentIntent.DoesNotExist:
        logger.error(f'Deployment intent not found for rollback: {deployment_intent_id}')
        return {'status': 'failed', 'error': 'Deployment intent not found'}
    
    try:
        connector_service = get_connector_service(connector_type)
        
        # Execute rollback
        result = connector_service.rollback(
            app_name=deployment.app_name,
            version=deployment.version,
            target_ring=deployment.target_ring,
            correlation_id=str(deployment.correlation_id),
        )
        
        # Update deployment status
        with transaction.atomic():
            deployment.status = DeploymentIntent.Status.ROLLED_BACK
            deployment.save()
        
        logger.info(
            f'Rollback from {connector_type} completed',
            extra={'deployment_intent_id': str(deployment.correlation_id), 'connector_type': connector_type}
        )
        
        return {
            'status': 'success',
            'deployment_intent_id': str(deployment.correlation_id),
            'connector_type': connector_type,
            'details': result
        }
        
    except Exception as exc:
        logger.error(
            f'Failed to rollback from {connector_type}: {exc}',
            extra={'deployment_intent_id': str(deployment.correlation_id), 'connector_type': connector_type},
            exc_info=True
        )
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
