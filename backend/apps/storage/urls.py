# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""URL configuration for Storage API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StorageHealthView, StorageProviderViewSet

app_name = "storage"

router = DefaultRouter()
router.register(r"providers", StorageProviderViewSet, basename="provider")

urlpatterns = [
    path("health/", StorageHealthView.as_view(), name="health"),
    path("", include(router.urls)),
]
