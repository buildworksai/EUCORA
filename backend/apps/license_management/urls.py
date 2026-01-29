# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""URL configuration for license_management API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AssignmentViewSet,
    ConsumptionSignalViewSet,
    ConsumptionSnapshotViewSet,
    EntitlementViewSet,
    ImportJobViewSet,
    IngestSignalView,
    LicenseAlertViewSet,
    LicensePoolViewSet,
    LicenseSKUViewSet,
    LicenseSummaryView,
    ReconcileView,
    ReconciliationRunViewSet,
    VendorViewSet,
)

app_name = "license_management"

router = DefaultRouter()
router.register(r"vendors", VendorViewSet, basename="vendor")
router.register(r"skus", LicenseSKUViewSet, basename="sku")
router.register(r"entitlements", EntitlementViewSet, basename="entitlement")
router.register(r"pools", LicensePoolViewSet, basename="pool")
router.register(r"assignments", AssignmentViewSet, basename="assignment")
router.register(r"signals", ConsumptionSignalViewSet, basename="signal")
router.register(r"snapshots", ConsumptionSnapshotViewSet, basename="snapshot")
router.register(r"reconciliation-runs", ReconciliationRunViewSet, basename="reconciliation-run")
router.register(r"alerts", LicenseAlertViewSet, basename="alert")
router.register(r"imports", ImportJobViewSet, basename="import")

urlpatterns = [
    path("summary/", LicenseSummaryView.as_view(), name="summary"),
    path("reconcile/", ReconcileView.as_view(), name="reconcile"),
    path("ingest/", IngestSignalView.as_view(), name="ingest"),
    path("", include(router.urls)),
]
