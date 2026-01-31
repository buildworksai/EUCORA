# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Policy Documents app.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.policy_documents.views import DocumentCategoryViewSet, PolicyDocumentViewSet

router = DefaultRouter()
router.register(r"categories", DocumentCategoryViewSet, basename="document-category")
router.register(r"", PolicyDocumentViewSet, basename="policy-document")

app_name = "policy_documents"

urlpatterns = [
    path("", include(router.urls)),
]
