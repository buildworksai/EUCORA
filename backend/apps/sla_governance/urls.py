# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for SLA Governance Agent.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    KPIDefinitionViewSet,
    KPIMeasurementViewSet,
    ServiceCatalogItemViewSet,
    SLABreachViewSet,
    SLAComplianceViewSet,
    SLADefinitionViewSet,
    SLAKPILinkViewSet,
    SLAParseRequestViewSet,
    SLAReportsViewSet,
    SLATargetViewSet,
    SLATemplateViewSet,
)

router = DefaultRouter()
router.register(r"services", ServiceCatalogItemViewSet, basename="service-catalog")
router.register(r"slas", SLADefinitionViewSet, basename="sla-definition")
router.register(r"targets", SLATargetViewSet, basename="sla-target")
router.register(r"kpis", KPIDefinitionViewSet, basename="kpi-definition")
router.register(r"kpi-links", SLAKPILinkViewSet, basename="sla-kpi-link")
router.register(r"measurements", KPIMeasurementViewSet, basename="kpi-measurement")
router.register(r"compliance", SLAComplianceViewSet, basename="sla-compliance")
router.register(r"breaches", SLABreachViewSet, basename="sla-breach")
router.register(r"templates", SLATemplateViewSet, basename="sla-template")
router.register(r"parse-request", SLAParseRequestViewSet, basename="sla-parse")
router.register(r"reports", SLAReportsViewSet, basename="sla-reports")

urlpatterns = router.urls
