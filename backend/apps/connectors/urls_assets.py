# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Assets URL configuration (without prefix) for clean /api/v1/assets/ paths.
"""
from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.list_assets, name='list'),
    path('<str:asset_id>/', views.get_asset, name='detail'),
]
