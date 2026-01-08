# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery tasks for demo data operations.
"""
from celery import shared_task
import logging
from apps.core.demo_data import seed_demo_data

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='apps.core.tasks.seed_demo_data_task')
def seed_demo_data_task(
    self,
    assets: int = 50000,
    applications: int = 5000,
    deployments: int = 10000,
    users: int = 1000,
    events: int = 100000,
    clear_existing: bool = False,
    batch_size: int = 1000,
):
    """
    Background task to seed demo data.
    
    Args:
        assets: Number of assets to create
        applications: Number of applications to create
        deployments: Number of deployments to create
        users: Number of users to create
        events: Number of events to create
        clear_existing: Whether to clear existing demo data first
        batch_size: Batch size for bulk operations
    
    Returns:
        Dict with seed results
    """
    try:
        logger.info(
            f'Starting demo data seed task: assets={assets}, applications={applications}, '
            f'deployments={deployments}, users={users}, events={events}, clear_existing={clear_existing}'
        )
        
        results = seed_demo_data(
            assets=assets,
            applications=applications,
            deployments=deployments,
            users=users,
            events=events,
            clear_existing=clear_existing,
            batch_size=batch_size,
        )
        
        logger.info(f'Demo data seed task completed successfully: {results}')
        return {'status': 'success', 'counts': results}
    except Exception as e:
        logger.error(f'Error in demo data seed task: {e}', exc_info=True)
        raise  # Re-raise to trigger Celery retry mechanism
