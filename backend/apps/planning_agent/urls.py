# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Planning Agent.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    BlastRadiusAnalysisViewSet,
    ChangeFreezePeriodViewSet,
    DeploymentPlanViewSet,
    DeploymentWindowViewSet,
    PlanningGenerateViewSet,
    PlanningReportsViewSet,
    RingAssignmentViewSet,
    RingDeviceViewSet,
    RollbackPlanViewSet,
)

router = DefaultRouter()
router.register(r"plans", DeploymentPlanViewSet, basename="deployment-plan")
router.register(r"rings", RingAssignmentViewSet, basename="ring-assignment")
router.register(r"devices", RingDeviceViewSet, basename="ring-device")
router.register(r"windows", DeploymentWindowViewSet, basename="deployment-window")
router.register(r"freezes", ChangeFreezePeriodViewSet, basename="change-freeze")
router.register(r"blast-radius", BlastRadiusAnalysisViewSet, basename="blast-radius")
router.register(r"rollback", RollbackPlanViewSet, basename="rollback-plan")
router.register(r"generate", PlanningGenerateViewSet, basename="planning-generate")
router.register(r"reports", PlanningReportsViewSet, basename="planning-reports")

urlpatterns = router.urls
