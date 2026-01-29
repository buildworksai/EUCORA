# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for integrations app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.integrations import views

router = DefaultRouter()
router.register(r"integrations", views.ExternalSystemViewSet, basename="integration")
router.register(r"integration-sync-logs", views.IntegrationSyncLogViewSet, basename="integration-sync-log")

urlpatterns = [
    path("api/v1/", include(router.urls)),
]
