# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core admin and utility endpoints.
"""
from django.urls import path
from .views_demo import (
    demo_data_stats_view,
    seed_demo_data_view,
    clear_demo_data_view,
    demo_mode_view,
    csrf_token_view,
)
from .views_tasks import (
    get_task_status,
    revoke_task,
    get_active_tasks,
)
from .views_health import (
    get_circuit_breaker_status,
    get_single_breaker_status,
    reset_circuit_breaker,
)

urlpatterns = [
    # Demo data management
    path('demo-data-stats', demo_data_stats_view, name='demo-data-stats'),
    path('seed-demo-data', seed_demo_data_view, name='seed-demo-data'),
    path('clear-demo-data', clear_demo_data_view, name='clear-demo-data'),
    path('demo-mode', demo_mode_view, name='demo-mode'),
    path('csrf-token', csrf_token_view, name='csrf-token'),
    
    # Task status API (Celery async task monitoring)
    path('tasks/<str:task_id>/status', get_task_status, name='task-status'),
    path('tasks/<str:task_id>/revoke', revoke_task, name='task-revoke'),
    path('tasks/active', get_active_tasks, name='tasks-active'),
    
    # Circuit breaker / resilience monitoring
    path('health/circuit-breakers', get_circuit_breaker_status, name='circuit-breakers'),
    path('health/circuit-breakers/<str:service_name>', get_single_breaker_status, name='circuit-breaker-detail'),
    path('health/circuit-breakers/<str:service_name>/reset', reset_circuit_breaker, name='circuit-breaker-reset'),
]
