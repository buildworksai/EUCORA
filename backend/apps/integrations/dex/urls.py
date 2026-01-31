# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""URL routing for DEX integration API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.integrations.dex.views import (
    DEXAggregateMetricsViewSet,
    DEXDashboardViewSet,
    DEXDeviceMetricsViewSet,
    DEXProviderViewSet,
    GreenITViewSet,
)

router = DefaultRouter()
router.register(r"provider", DEXProviderViewSet, basename="dex-provider")
router.register(r"metrics", DEXDeviceMetricsViewSet, basename="dex-metrics")
router.register(r"aggregates", DEXAggregateMetricsViewSet, basename="dex-aggregates")
router.register(r"dashboard", DEXDashboardViewSet, basename="dex-dashboard")
router.register(r"green-it", GreenITViewSet, basename="dex-green-it")

app_name = "dex"

urlpatterns = [
    path("", include(router.urls)),
]
