# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Discovery Agent API.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DiscoveryDashboardViewSet,
    DiscoveryReportViewSet,
    DiscoveryRunViewSet,
    DiscoverySourceViewSet,
    LicenseGapViewSet,
    NormalizedApplicationViewSet,
    PatchGapViewSet,
)

app_name = "discovery_agent"

router = DefaultRouter()
router.register(r"sources", DiscoverySourceViewSet, basename="source")
router.register(r"runs", DiscoveryRunViewSet, basename="run")
router.register(r"applications", NormalizedApplicationViewSet, basename="application")
router.register(r"license-gaps", LicenseGapViewSet, basename="license-gap")
router.register(r"patch-gaps", PatchGapViewSet, basename="patch-gap")
router.register(r"reports", DiscoveryReportViewSet, basename="report")
router.register(r"dashboard", DiscoveryDashboardViewSet, basename="dashboard")

urlpatterns = [
    path("", include(router.urls)),
]
