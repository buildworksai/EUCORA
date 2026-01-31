# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Documentation Agent.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    CodeAnalysisViewSet,
    CodeRepositoryViewSet,
    DocumentationGenerationViewSet,
    DocumentationTemplateViewSet,
    DocumentedModuleViewSet,
    GeneratedDocumentViewSet,
)

app_name = "documentation_agent"

router = DefaultRouter()
router.register(r"repositories", CodeRepositoryViewSet, basename="repository")
router.register(r"analyses", CodeAnalysisViewSet, basename="analysis")
router.register(r"modules", DocumentedModuleViewSet, basename="module")
router.register(r"documents", GeneratedDocumentViewSet, basename="document")
router.register(r"templates", DocumentationTemplateViewSet, basename="template")
router.register(r"generate", DocumentationGenerationViewSet, basename="generation")

urlpatterns = router.urls
