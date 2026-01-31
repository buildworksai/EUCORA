# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for KB & Triage Agent API.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    IncidentPatternViewSet,
    KBTriageReportsViewSet,
    KnowledgeArticleViewSet,
    KnowledgeSourceViewSet,
    TriageFeedbackViewSet,
    TriageRequestViewSet,
)

router = DefaultRouter()
router.register(r"sources", KnowledgeSourceViewSet, basename="knowledge-source")
router.register(r"articles", KnowledgeArticleViewSet, basename="knowledge-article")
router.register(r"triage", TriageRequestViewSet, basename="triage-request")
router.register(r"feedback", TriageFeedbackViewSet, basename="triage-feedback")
router.register(r"patterns", IncidentPatternViewSet, basename="incident-pattern")
router.register(r"reports", KBTriageReportsViewSet, basename="kb-triage-reports")

urlpatterns = router.urls
