# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core admin endpoints.
"""
from django.urls import path
from .views_demo import (
    demo_data_stats_view,
    seed_demo_data_view,
    clear_demo_data_view,
    demo_mode_view,
    csrf_token_view,
)

urlpatterns = [
    path('demo-data-stats', demo_data_stats_view, name='demo-data-stats'),
    path('seed-demo-data', seed_demo_data_view, name='seed-demo-data'),
    path('clear-demo-data', clear_demo_data_view, name='clear-demo-data'),
    path('demo-mode', demo_mode_view, name='demo-mode'),
    path('csrf-token', csrf_token_view, name='csrf-token'),
]
