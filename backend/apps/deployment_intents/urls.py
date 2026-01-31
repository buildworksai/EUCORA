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
    # Stack API endpoints (E6)
    path("stack/applications/", views.stack_applications, name="stack-applications"),
    path(
        "stack/applications/<str:app_id>/dependencies/", views.stack_application_dependencies, name="stack-dependencies"
    ),
    path("stack/events/", views.stack_events, name="stack-events"),
    # Deployment action endpoints (E6)
    path("stack/deployments/<uuid:correlation_id>/promote/", views.promote_deployment, name="promote-deployment"),
    path("stack/deployments/<uuid:correlation_id>/pause/", views.pause_deployment, name="pause-deployment"),
    path("stack/deployments/<uuid:correlation_id>/resume/", views.resume_deployment, name="resume-deployment"),
    path("stack/deployments/<uuid:correlation_id>/rollback/", views.rollback_deployment, name="rollback-deployment"),
    path("stack/deployments/<uuid:correlation_id>/cancel/", views.cancel_deployment, name="cancel-deployment"),
]
