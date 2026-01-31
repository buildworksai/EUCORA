# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Knowledge app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.knowledge.views import EmbeddingConfigViewSet, KnowledgeSearchViewSet

router = DefaultRouter()
router.register(r"config", EmbeddingConfigViewSet, basename="embedding-config")
router.register(r"search", KnowledgeSearchViewSet, basename="knowledge-search")

app_name = "knowledge"

urlpatterns = [
    path("", include(router.urls)),
]
