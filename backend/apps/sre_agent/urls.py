# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for SRE Agent API.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    HealthCheckResultViewSet,
    HealthEndpointViewSet,
    MonitoringPlatformViewSet,
    RunbookExecutionViewSet,
    RunbookViewSet,
    SelfHealingExecutionViewSet,
    SelfHealingRuleViewSet,
    SLODefinitionViewSet,
    SLOMetricViewSet,
    SREReportsViewSet,
)

router = DefaultRouter()
router.register(r"monitoring-platforms", MonitoringPlatformViewSet, basename="monitoring-platform")
router.register(r"health-endpoints", HealthEndpointViewSet, basename="health-endpoint")
router.register(r"health-check-results", HealthCheckResultViewSet, basename="health-check-result")
router.register(r"slos", SLODefinitionViewSet, basename="slo-definition")
router.register(r"slo-metrics", SLOMetricViewSet, basename="slo-metric")
router.register(r"self-healing-rules", SelfHealingRuleViewSet, basename="self-healing-rule")
router.register(r"self-healing-executions", SelfHealingExecutionViewSet, basename="self-healing-execution")
router.register(r"runbooks", RunbookViewSet, basename="runbook")
router.register(r"runbook-executions", RunbookExecutionViewSet, basename="runbook-execution")
router.register(r"reports", SREReportsViewSet, basename="sre-reports")

urlpatterns = router.urls
