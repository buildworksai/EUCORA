# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Telemetry URL configuration.
"""
from django.urls import path
from . import views

app_name = 'telemetry'

urlpatterns = [
    path('', views.health_check, name='health'),
    path('ready', views.readiness_check, name='readiness'),
    path('live', views.liveness_check, name='liveness'),
    path('compliance-stats', views.compliance_stats, name='compliance-stats'),
]
