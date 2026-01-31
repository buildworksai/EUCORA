# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for IAM Security.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    AnomalyDetectionViewSet,
    DetectionRuleViewSet,
    IdentityProviderViewSet,
    PermissionChangeViewSet,
    SecurityActionsViewSet,
    SecurityAlertViewSet,
    SecurityReportsViewSet,
    SignInEventViewSet,
)

app_name = "iam_security"

router = DefaultRouter()
router.register(r"providers", IdentityProviderViewSet, basename="provider")
router.register(r"sign-ins", SignInEventViewSet, basename="sign-in")
router.register(r"permission-changes", PermissionChangeViewSet, basename="permission-change")
router.register(r"anomalies", AnomalyDetectionViewSet, basename="anomaly")
router.register(r"rules", DetectionRuleViewSet, basename="rule")
router.register(r"alerts", SecurityAlertViewSet, basename="alert")
router.register(r"actions", SecurityActionsViewSet, basename="action")
router.register(r"reports", SecurityReportsViewSet, basename="report")

urlpatterns = router.urls
