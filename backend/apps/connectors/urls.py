# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Connectors URL configuration.
"""
from django.urls import path

from . import views

app_name = "connectors"

urlpatterns = [
    path("assets/", views.list_assets, name="assets"),
    path("assets/<str:asset_id>/", views.get_asset, name="asset-detail"),
    path("connectors/", views.list_connectors, name="connectors-list"),
    path("connectors/<str:connector_type>/health", views.health_check, name="health"),
    path("connectors/<str:connector_type>/deploy", views.deploy, name="deploy"),
]
