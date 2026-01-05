# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow URL configuration.
"""
from django.urls import path
from . import views

app_name = 'cab_workflow'

urlpatterns = [
    path('pending/', views.list_pending_approvals, name='pending'),
    path('approvals/', views.list_approvals, name='list'),
    path('<uuid:correlation_id>/approve', views.approve_deployment, name='approve'),
    path('<uuid:correlation_id>/reject', views.reject_deployment, name='reject'),
]
