# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for license_management API views."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.license_management.models import (
    AlertSeverity,
    AlertType,
    Assignment,
    AssignmentStatus,
    ConsumptionSignal,
    ConsumptionSnapshot,
    Entitlement,
    EntitlementStatus,
    LicenseAlert,
    LicenseModelType,
    LicensePool,
    LicenseSKU,
    PrincipalType,
    ReconciliationRun,
    ReconciliationStatus,
    ScopeType,
    Vendor,
)

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username="testuser", password="testpass123")


@pytest.fixture
def vendor(db):
    """Create a test vendor."""
    return Vendor.objects.create(
        name="Microsoft",
        vendor_code="MSFT",
        contact_email="licensing@microsoft.com",
    )


@pytest.fixture
def sku(db, vendor):
    """Create a test SKU."""
    return LicenseSKU.objects.create(
        vendor=vendor,
        sku_code="M365-E5",
        name="Microsoft 365 E5",
        license_model_type=LicenseModelType.USER_SUBSCRIPTION,
    )


@pytest.fixture
def entitlement(db, sku, user):
    """Create a test entitlement."""
    return Entitlement.objects.create(
        sku=sku,
        contract_ref="CONTRACT-001",
        quantity=100,
        effective_date=timezone.now().date(),
        expiry_date=(timezone.now() + timedelta(days=365)).date(),
        created_by=user,
        status=EntitlementStatus.ACTIVE,
    )


@pytest.fixture
def pool(db, sku):
    """Create a test license pool."""
    return LicensePool.objects.create(
        sku=sku,
        name="IT Department Pool",
        scope_type=ScopeType.BUSINESS_UNIT,
        scope_id="IT",
        allocated_quantity=50,
    )


@pytest.fixture
def assignment(db, pool, user):
    """Create a test assignment."""
    return Assignment.objects.create(
        pool=pool,
        principal_type=PrincipalType.USER,
        principal_id="user@example.com",
        principal_name="Test User",
        assigned_by=user,
        status=AssignmentStatus.ACTIVE,
    )


class TestLicenseSummaryView:
    """Tests for LicenseSummaryView."""

    def test_get_summary_unauthenticated(self, api_client):
        """Test unauthenticated access is denied."""
        url = reverse("license_management:summary")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_summary_empty(self, authenticated_client):
        """Test summary with no data."""
        url = reverse("license_management:summary")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_entitled"] == 0
        assert response.data["health_status"] == "healthy"

    def test_get_summary_with_data(self, authenticated_client, entitlement, pool):
        """Test summary with license data."""
        pool.consumed_quantity = 25
        pool.save()

        url = reverse("license_management:summary")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_entitled"] == 100
        assert response.data["total_allocated"] == 50


class TestVendorViewSet:
    """Tests for VendorViewSet."""

    def test_list_vendors(self, authenticated_client, vendor):
        """Test listing vendors."""
        url = reverse("license_management:vendor-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Microsoft"

    def test_create_vendor(self, authenticated_client):
        """Test creating a vendor."""
        url = reverse("license_management:vendor-list")
        data = {
            "name": "Adobe",
            "vendor_code": "ADBE",
            "contact_email": "licensing@adobe.com",
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Vendor.objects.filter(vendor_code="ADBE").exists()

    def test_retrieve_vendor(self, authenticated_client, vendor):
        """Test retrieving a vendor."""
        url = reverse("license_management:vendor-detail", kwargs={"pk": vendor.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Microsoft"

    def test_update_vendor(self, authenticated_client, vendor):
        """Test updating a vendor."""
        url = reverse("license_management:vendor-detail", kwargs={"pk": vendor.id})
        data = {"name": "Microsoft Corporation", "vendor_code": "MSFT"}
        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        vendor.refresh_from_db()
        assert vendor.name == "Microsoft Corporation"

    def test_filter_vendors_by_active(self, authenticated_client, vendor):
        """Test filtering vendors by active status."""
        Vendor.objects.create(name="Inactive", vendor_code="INAC", is_active=False)

        url = reverse("license_management:vendor-list") + "?is_active=true"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


class TestLicenseSKUViewSet:
    """Tests for LicenseSKUViewSet."""

    def test_list_skus(self, authenticated_client, sku):
        """Test listing SKUs."""
        url = reverse("license_management:sku-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_create_sku(self, authenticated_client, vendor):
        """Test creating a SKU."""
        url = reverse("license_management:sku-list")
        data = {
            "vendor": vendor.id,
            "sku_code": "O365-E3",
            "name": "Office 365 E3",
            "license_model_type": LicenseModelType.USER_SUBSCRIPTION,
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_filter_skus_by_vendor(self, authenticated_client, sku, vendor):
        """Test filtering SKUs by vendor."""
        url = reverse("license_management:sku-list") + f"?vendor={vendor.id}"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_sku_consumption_action(self, authenticated_client, sku, user):
        """Test SKU consumption history action."""
        # Create a snapshot
        run = ReconciliationRun.objects.create(triggered_by=user)
        ConsumptionSnapshot.objects.create(
            sku=sku,
            reconciliation_run=run,
            entitled_quantity=100,
            allocated_quantity=50,
            consumed_quantity=25,
            available_quantity=25,
            utilization_percent=Decimal("50.0"),
        )

        url = reverse("license_management:sku-consumption", kwargs={"pk": sku.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1


class TestEntitlementViewSet:
    """Tests for EntitlementViewSet."""

    def test_list_entitlements(self, authenticated_client, entitlement):
        """Test listing entitlements."""
        url = reverse("license_management:entitlement-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_create_entitlement(self, authenticated_client, sku):
        """Test creating an entitlement."""
        url = reverse("license_management:entitlement-list")
        data = {
            "sku": sku.id,
            "contract_ref": "CONTRACT-NEW",
            "quantity": 50,
            "effective_date": timezone.now().date().isoformat(),
            "expiry_date": (timezone.now() + timedelta(days=365)).date().isoformat(),
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Entitlement.objects.filter(contract_ref="CONTRACT-NEW").exists()

    def test_approve_entitlement_action(self, authenticated_client, sku, user):
        """Test approving an entitlement."""
        entitlement = Entitlement.objects.create(
            sku=sku,
            contract_ref="CONTRACT-PENDING",
            quantity=25,
            effective_date=timezone.now().date(),
            expiry_date=(timezone.now() + timedelta(days=365)).date(),
            created_by=user,
            status=EntitlementStatus.PENDING,
        )

        url = reverse("license_management:entitlement-approve", kwargs={"pk": entitlement.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        entitlement.refresh_from_db()
        assert entitlement.status == EntitlementStatus.ACTIVE

    def test_approve_entitlement_already_active(self, authenticated_client, entitlement):
        """Test approving already active entitlement fails."""
        url = reverse("license_management:entitlement-approve", kwargs={"pk": entitlement.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestLicensePoolViewSet:
    """Tests for LicensePoolViewSet."""

    def test_list_pools(self, authenticated_client, pool):
        """Test listing pools."""
        url = reverse("license_management:pool-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_create_pool(self, authenticated_client, sku):
        """Test creating a pool."""
        url = reverse("license_management:pool-list")
        data = {
            "sku": sku.id,
            "name": "Finance Pool",
            "scope_type": ScopeType.BUSINESS_UNIT,
            "scope_id": "FIN",
            "allocated_quantity": 30,
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED


class TestAssignmentViewSet:
    """Tests for AssignmentViewSet."""

    def test_list_assignments(self, authenticated_client, assignment):
        """Test listing assignments."""
        url = reverse("license_management:assignment-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_create_assignment(self, authenticated_client, pool):
        """Test creating an assignment."""
        url = reverse("license_management:assignment-list")
        data = {
            "pool": pool.id,
            "principal_type": PrincipalType.USER,
            "principal_id": "new@example.com",
            "principal_name": "New User",
        }
        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_revoke_assignment_action(self, authenticated_client, assignment):
        """Test revoking an assignment."""
        url = reverse("license_management:assignment-revoke", kwargs={"pk": assignment.id})
        response = authenticated_client.post(url, {"reason": "Test revocation"})

        assert response.status_code == status.HTTP_200_OK
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.REVOKED

    def test_filter_assignments_by_pool(self, authenticated_client, assignment, pool):
        """Test filtering assignments by pool."""
        url = reverse("license_management:assignment-list") + f"?pool={pool.id}"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


class TestConsumptionSignalViewSet:
    """Tests for ConsumptionSignalViewSet."""

    def test_list_signals(self, authenticated_client, sku):
        """Test listing signals."""
        ConsumptionSignal.objects.create(
            source_system="entra_id",
            raw_id="LOGIN-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku=sku,
        )

        url = reverse("license_management:signal-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_filter_signals_by_source(self, authenticated_client, sku):
        """Test filtering signals by source system."""
        ConsumptionSignal.objects.create(
            source_system="entra_id",
            raw_id="LOGIN-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku=sku,
        )
        ConsumptionSignal.objects.create(
            source_system="intune",
            raw_id="APP-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.DEVICE,
            principal_id="DEVICE-001",
            sku=sku,
        )

        url = reverse("license_management:signal-list") + "?source_system=entra_id"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


class TestConsumptionSnapshotViewSet:
    """Tests for ConsumptionSnapshotViewSet."""

    def test_list_snapshots(self, authenticated_client, sku, user):
        """Test listing snapshots."""
        run = ReconciliationRun.objects.create(triggered_by=user)
        ConsumptionSnapshot.objects.create(
            sku=sku,
            reconciliation_run=run,
            entitled_quantity=100,
            allocated_quantity=50,
            consumed_quantity=25,
            available_quantity=25,
            utilization_percent=Decimal("50.0"),
        )

        url = reverse("license_management:snapshot-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_snapshot_evidence_action(self, authenticated_client, sku, user):
        """Test snapshot evidence download action."""
        run = ReconciliationRun.objects.create(triggered_by=user)
        snapshot = ConsumptionSnapshot.objects.create(
            sku=sku,
            reconciliation_run=run,
            entitled_quantity=100,
            allocated_quantity=50,
            consumed_quantity=25,
            available_quantity=25,
            utilization_percent=Decimal("50.0"),
        )

        url = reverse("license_management:snapshot-evidence", kwargs={"pk": snapshot.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "evidence_pack_ref" in response.data
        assert "download_url" in response.data


class TestReconcileView:
    """Tests for ReconcileView."""

    def test_trigger_reconciliation(self, authenticated_client):
        """Test triggering a reconciliation."""
        url = reverse("license_management:reconcile")
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert ReconciliationRun.objects.count() == 1

    def test_get_reconciliation_status(self, authenticated_client, user):
        """Test getting reconciliation status."""
        ReconciliationRun.objects.create(
            triggered_by=user,
            status=ReconciliationStatus.COMPLETED,
        )

        url = reverse("license_management:reconcile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == ReconciliationStatus.COMPLETED

    def test_reconciliation_conflict_when_running(self, authenticated_client, user):
        """Test triggering reconciliation when one is running."""
        ReconciliationRun.objects.create(
            triggered_by=user,
            status=ReconciliationStatus.RUNNING,
        )

        url = reverse("license_management:reconcile")
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_409_CONFLICT


class TestLicenseAlertViewSet:
    """Tests for LicenseAlertViewSet."""

    def test_list_alerts(self, authenticated_client, sku):
        """Test listing alerts."""
        LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.OVER_ALLOCATION,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            message="Test message",
        )

        url = reverse("license_management:alert-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_acknowledge_alert_action(self, authenticated_client, sku):
        """Test acknowledging an alert."""
        alert = LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.EXPIRY_WARNING,
            severity=AlertSeverity.MEDIUM,
            title="Expiry Warning",
            message="Entitlement expiring soon",
        )

        url = reverse("license_management:alert-acknowledge", kwargs={"pk": alert.id})
        response = authenticated_client.post(url, {"notes": "Renewal in progress"})

        assert response.status_code == status.HTTP_200_OK
        alert.refresh_from_db()
        assert alert.acknowledged is True
        assert alert.resolution_notes == "Renewal in progress"

    def test_acknowledge_already_acknowledged(self, authenticated_client, sku, user):
        """Test acknowledging already acknowledged alert fails."""
        alert = LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.CONSUMPTION_SPIKE,
            severity=AlertSeverity.LOW,
            title="Spike",
            message="Spike detected",
            acknowledged=True,
            acknowledged_by=user,
            acknowledged_at=timezone.now(),
        )

        url = reverse("license_management:alert-acknowledge", kwargs={"pk": alert.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_filter_alerts_by_severity(self, authenticated_client, sku):
        """Test filtering alerts by severity."""
        LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.OVER_ALLOCATION,
            severity=AlertSeverity.HIGH,
            title="High Alert",
            message="High severity",
        )
        LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.EXPIRY_WARNING,
            severity=AlertSeverity.LOW,
            title="Low Alert",
            message="Low severity",
        )

        url = reverse("license_management:alert-list") + f"?severity={AlertSeverity.HIGH}"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


class TestIngestSignalView:
    """Tests for IngestSignalView."""

    def test_ingest_signal(self, authenticated_client, sku):
        """Test ingesting a consumption signal."""
        url = reverse("license_management:ingest")
        data = {
            "source_system": "entra_id",
            "raw_id": "LOGIN-12345",
            "timestamp": timezone.now().isoformat(),
            "principal_type": PrincipalType.USER,
            "principal_id": "user@example.com",
            "sku_id": str(sku.id),
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert ConsumptionSignal.objects.filter(raw_id="LOGIN-12345").exists()

    def test_ingest_signal_missing_field(self, authenticated_client):
        """Test ingesting signal with missing required field."""
        url = reverse("license_management:ingest")
        data = {
            "source_system": "entra_id",
            # Missing other required fields
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Missing required field" in response.data["error"]

    def test_ingest_signal_invalid_sku(self, authenticated_client):
        """Test ingesting signal with invalid SKU."""
        url = reverse("license_management:ingest")
        data = {
            "source_system": "entra_id",
            "raw_id": "LOGIN-12345",
            "timestamp": timezone.now().isoformat(),
            "principal_type": PrincipalType.USER,
            "principal_id": "user@example.com",
            "sku_id": "00000000-0000-0000-0000-000000000000",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestCorrelationIdIsolation:
    """Tests for correlation ID isolation (MANDATORY per CLAUDE.md)."""

    def test_vendor_has_correlation_id(self, vendor):
        """Test vendor has correlation ID."""
        assert vendor.correlation_id is not None

    def test_sku_has_correlation_id(self, sku):
        """Test SKU has correlation ID."""
        assert sku.correlation_id is not None

    def test_entitlement_has_correlation_id(self, entitlement):
        """Test entitlement has correlation ID."""
        assert entitlement.correlation_id is not None

    def test_pool_has_correlation_id(self, pool):
        """Test pool has correlation ID."""
        assert pool.correlation_id is not None

    def test_assignment_has_correlation_id(self, assignment):
        """Test assignment has correlation ID."""
        assert assignment.correlation_id is not None

    def test_correlation_ids_are_unique(self, db, vendor):
        """Test correlation IDs are unique across objects."""
        vendor2 = Vendor.objects.create(
            name="Adobe",
            vendor_code="ADBE",
        )
        assert vendor.correlation_id != vendor2.correlation_id
