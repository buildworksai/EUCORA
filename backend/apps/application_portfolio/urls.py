# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Application Portfolio URL configuration.

Registers all API endpoints for the application portfolio module.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ApplicationDependencyViewSet,
    ApplicationHealthViewSet,
    ApplicationVersionViewSet,
    ApplicationViewSet,
    DeploymentIntentViewSet,
    DeploymentMetricViewSet,
    PackageArtifactViewSet,
    PortfolioSummaryViewSet,
    PublisherViewSet,
)

router = DefaultRouter()
router.register(r"publishers", PublisherViewSet, basename="publisher")
router.register(r"applications", ApplicationViewSet, basename="application")
router.register(r"versions", ApplicationVersionViewSet, basename="version")
router.register(r"artifacts", PackageArtifactViewSet, basename="artifact")
router.register(r"deployments", DeploymentIntentViewSet, basename="deployment")
router.register(r"metrics", DeploymentMetricViewSet, basename="metric")
router.register(r"health", ApplicationHealthViewSet, basename="health")
router.register(r"dependencies", ApplicationDependencyViewSet, basename="dependency")
router.register(r"summary", PortfolioSummaryViewSet, basename="summary")

app_name = "application_portfolio"

urlpatterns = [
    path("", include(router.urls)),
]
