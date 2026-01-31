# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL routing for Portfolio Management API.

Registers DRF routers for all portfolio management endpoints.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.portfolio_management.views import (
    ApplicationManagerPerformanceViewSet,
    ApplicationOwnershipViewSet,
    LicenseTrueUpForecastViewSet,
    PackagingRequestViewSet,
    PortfolioViewSet,
)

router = DefaultRouter()

# Portfolio Management endpoints
router.register(r"portfolios", PortfolioViewSet, basename="portfolio")
router.register(r"ownerships", ApplicationOwnershipViewSet, basename="ownership")
router.register(r"performance", ApplicationManagerPerformanceViewSet, basename="performance")
router.register(r"forecasts", LicenseTrueUpForecastViewSet, basename="forecast")
router.register(r"packaging-requests", PackagingRequestViewSet, basename="packaging-request")

urlpatterns = [
    path("", include(router.urls)),
]
