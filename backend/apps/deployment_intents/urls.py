# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Deployment Intents URL configuration.
"""
from django.urls import path

from . import views

app_name = "deployment_intents"

urlpatterns = [
    path("", views.create_deployment, name="create"),
    path("list", views.list_deployments, name="list"),
    path("applications", views.list_applications_with_versions, name="applications"),
    path("<uuid:correlation_id>/", views.get_deployment, name="get"),
]
