# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Celery configuration for EUCORA Control Plane.

Handles async task processing for:
- Evidence pack generation
- Risk score calculations
- Connector operations (deploy, health check)
- Reconciliation loops
"""
import os
from celery import Celery
from django.conf import settings

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('eucora')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Task routing configuration
app.conf.task_routes = {
    'apps.evidence_store.tasks.*': {'queue': 'evidence'},
    'apps.policy_engine.tasks.*': {'queue': 'policy'},
    'apps.connectors.tasks.*': {'queue': 'connectors'},
    'apps.deployment_intents.tasks.*': {'queue': 'deployment'},
}

# Task result backend
app.conf.result_backend = settings.CACHES['default']['LOCATION']

# Task serialization
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Timezone
app.conf.timezone = 'UTC'
app.conf.enable_utc = True

# Task execution settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'reconciliation-loop': {
        'task': 'apps.deployment_intents.tasks.reconciliation_loop',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-events': {
        'task': 'apps.event_store.tasks.cleanup_old_events',
        'schedule': 86400.0,  # Daily
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f'Request: {self.request!r}')

