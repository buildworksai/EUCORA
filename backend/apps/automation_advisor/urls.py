# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Automation Advisor.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    AutomationAnalysisViewSet,
    AutomationCandidateViewSet,
    AutomationReportsViewSet,
    ROIConfigurationViewSet,
    TaskPatternViewSet,
)

app_name = "automation_advisor"

router = DefaultRouter()
router.register(r"patterns", TaskPatternViewSet, basename="pattern")
router.register(r"candidates", AutomationCandidateViewSet, basename="candidate")
router.register(r"analyses", AutomationAnalysisViewSet, basename="analysis")
router.register(r"roi-config", ROIConfigurationViewSet, basename="roi-config")
router.register(r"reports", AutomationReportsViewSet, basename="report")

urlpatterns = router.urls
