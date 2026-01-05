# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Store URL configuration.
"""
from django.urls import path
from . import views

app_name = 'evidence_store'

urlpatterns = [
    path('', views.upload_evidence_pack, name='upload'),
    path('<uuid:correlation_id>/', views.get_evidence_pack, name='get'),
]
