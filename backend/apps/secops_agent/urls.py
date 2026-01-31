# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for SecOps Agent API.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    ComplianceBaselineViewSet,
    ComplianceCheckViewSet,
    RemediationPlanViewSet,
    SecOpsReportsViewSet,
    SecurityAlertViewSet,
    SIEMConnectionViewSet,
    VulnerabilityInstanceViewSet,
    VulnerabilityScannerViewSet,
    VulnerabilityViewSet,
)

router = DefaultRouter()
router.register(r"scanners", VulnerabilityScannerViewSet, basename="vulnerability-scanner")
router.register(r"vulnerabilities", VulnerabilityViewSet, basename="vulnerability")
router.register(r"instances", VulnerabilityInstanceViewSet, basename="vulnerability-instance")
router.register(r"remediation-plans", RemediationPlanViewSet, basename="remediation-plan")
router.register(r"siem", SIEMConnectionViewSet, basename="siem-connection")
router.register(r"alerts", SecurityAlertViewSet, basename="security-alert")
router.register(r"compliance-baselines", ComplianceBaselineViewSet, basename="compliance-baseline")
router.register(r"compliance-checks", ComplianceCheckViewSet, basename="compliance-check")
router.register(r"reports", SecOpsReportsViewSet, basename="secops-reports")

urlpatterns = router.urls
