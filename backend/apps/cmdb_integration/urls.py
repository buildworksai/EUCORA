# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for CMDB Integration API.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CMDBConnectionViewSet,
    CMDBDiscrepancyViewSet,
    CMDBReportsViewSet,
    CMDBSyncRecordViewSet,
    CMDBTableMappingViewSet,
    CMDBValidationRuleViewSet,
)

app_name = "cmdb_integration"

router = DefaultRouter()
router.register(r"connections", CMDBConnectionViewSet, basename="connection")
router.register(r"mappings", CMDBTableMappingViewSet, basename="mapping")
router.register(r"validation-rules", CMDBValidationRuleViewSet, basename="validation-rule")
router.register(r"sync", CMDBSyncRecordViewSet, basename="sync")
router.register(r"discrepancies", CMDBDiscrepancyViewSet, basename="discrepancy")
router.register(r"reports", CMDBReportsViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
]
