# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""URL configuration for agent management."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AgentDeploymentStatusViewSet, AgentTaskViewSet, AgentTelemetryViewSet, AgentViewSet

router = DefaultRouter()
router.register(r"agents", AgentViewSet, basename="agent")
router.register(r"tasks", AgentTaskViewSet, basename="agent-task")
router.register(r"telemetry", AgentTelemetryViewSet, basename="agent-telemetry")
router.register(r"deployments", AgentDeploymentStatusViewSet, basename="agent-deployment")

urlpatterns = [
    path("", include(router.urls)),
]
