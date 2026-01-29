# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for packaging factory.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PackagingPipelineViewSet

router = DefaultRouter()
router.register(r"pipelines", PackagingPipelineViewSet, basename="packaging-pipeline")

urlpatterns = [
    path("", include(router.urls)),
]
