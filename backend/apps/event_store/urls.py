# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Event Store URL configuration.
"""
from django.urls import path
from . import views

app_name = 'event_store'

urlpatterns = [
    path('', views.log_event, name='log'),
    path('list', views.list_events, name='list'),
]
