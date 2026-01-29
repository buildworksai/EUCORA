# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for license_management models."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.license_management.models import (
    AlertSeverity,
    AlertType,
    Assignment,
    AssignmentStatus,
    ConsumptionSignal,
    ConsumptionSnapshot,
    ConsumptionUnit,
    Entitlement,
    EntitlementStatus,
    ImportJob,
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


class TestVendorModel:
    """Tests for Vendor model."""

    def test_create_vendor(self, db):
        """Test creating a vendor."""
        vendor = Vendor.objects.create(
            name="Adobe",
            vendor_code="ADBE",
            contact_email="licensing@adobe.com",
        )
        assert vendor.id is not None
        assert vendor.name == "Adobe"
        assert vendor.vendor_code == "ADBE"
        assert vendor.is_active is True

    def test_vendor_str(self, vendor):
        """Test vendor string representation."""
        assert str(vendor) == "Microsoft (MSFT)"

    def test_vendor_unique_code(self, vendor, db):
        """Test vendor code uniqueness."""
        with pytest.raises(Exception):  # IntegrityError
            Vendor.objects.create(
                name="Another Vendor",
                vendor_code="MSFT",  # Duplicate
            )

    def test_vendor_timestamps(self, vendor):
        """Test vendor has timestamps."""
        assert vendor.created_at is not None
        assert vendor.updated_at is not None


class TestLicenseSKUModel:
    """Tests for LicenseSKU model."""

    def test_create_sku(self, db, vendor):
        """Test creating a SKU."""
        sku = LicenseSKU.objects.create(
            vendor=vendor,
            sku_code="O365-E3",
            name="Office 365 E3",
            license_model_type=LicenseModelType.USER_SUBSCRIPTION,
        )
        assert sku.id is not None
        assert sku.vendor == vendor

    def test_sku_str(self, sku):
        """Test SKU string representation."""
        assert str(sku) == "Microsoft 365 E5 (M365-E5)"

    def test_sku_license_types(self, db, vendor):
        """Test different license model types."""
        for model_type in LicenseModelType:
            sku = LicenseSKU.objects.create(
                vendor=vendor,
                sku_code=f"TEST-{model_type.value}",
                name=f"Test SKU {model_type.value}",
                license_model_type=model_type,
            )
            assert sku.license_model_type == model_type

    def test_sku_unique_vendor_code(self, db, vendor, sku):
        """Test SKU code uniqueness per vendor."""
        with pytest.raises(Exception):  # IntegrityError
            LicenseSKU.objects.create(
                vendor=vendor,
                sku_code="M365-E5",  # Duplicate for same vendor
                name="Another SKU",
                license_model_type=LicenseModelType.USER_SUBSCRIPTION,
            )


class TestEntitlementModel:
    """Tests for Entitlement model."""

    def test_create_entitlement(self, db, sku, user):
        """Test creating an entitlement."""
        entitlement = Entitlement.objects.create(
            sku=sku,
            contract_ref="CONTRACT-002",
            quantity=50,
            effective_date=timezone.now().date(),
            expiry_date=(timezone.now() + timedelta(days=365)).date(),
            created_by=user,
        )
        assert entitlement.id is not None
        assert entitlement.status == EntitlementStatus.PENDING

    def test_entitlement_is_expired(self, db, sku, user):
        """Test entitlement is_expired property."""
        expired = Entitlement.objects.create(
            sku=sku,
            contract_ref="CONTRACT-EXP",
            quantity=10,
            effective_date=(timezone.now() - timedelta(days=400)).date(),
            expiry_date=(timezone.now() - timedelta(days=30)).date(),
            created_by=user,
            status=EntitlementStatus.ACTIVE,
        )
        assert expired.is_expired is True

    def test_entitlement_not_expired(self, entitlement):
        """Test entitlement not expired."""
        assert entitlement.is_expired is False

    def test_entitlement_days_until_expiry(self, entitlement):
        """Test days until expiry calculation."""
        days = entitlement.days_until_expiry
        assert days is not None
        assert 360 <= days <= 366  # ~1 year

    def test_entitlement_str(self, entitlement):
        """Test entitlement string representation."""
        assert "100" in str(entitlement)
        assert "M365-E5" in str(entitlement)


class TestLicensePoolModel:
    """Tests for LicensePool model."""

    def test_create_pool(self, db, sku):
        """Test creating a license pool."""
        pool = LicensePool.objects.create(
            sku=sku,
            name="Finance Pool",
            scope_type=ScopeType.BUSINESS_UNIT,
            scope_id="FIN",
            allocated_quantity=25,
        )
        assert pool.id is not None
        assert pool.consumed_quantity == 0

    def test_pool_available_quantity(self, pool):
        """Test available quantity calculation."""
        assert pool.available_quantity == 50  # 50 allocated - 0 consumed

    def test_pool_utilization_percent(self, pool):
        """Test utilization percent calculation."""
        assert pool.utilization_percent == Decimal("0")

        # Update consumed
        pool.consumed_quantity = 25
        pool.save()
        assert pool.utilization_percent == Decimal("50.0")

    def test_pool_str(self, pool):
        """Test pool string representation."""
        assert "IT Department Pool" in str(pool)


class TestAssignmentModel:
    """Tests for Assignment model."""

    def test_create_assignment(self, db, pool, user):
        """Test creating an assignment."""
        assignment = Assignment.objects.create(
            pool=pool,
            principal_type=PrincipalType.DEVICE,
            principal_id="DEVICE-001",
            principal_name="Workstation 1",
            assigned_by=user,
        )
        assert assignment.id is not None
        assert assignment.status == AssignmentStatus.ACTIVE

    def test_assignment_str(self, assignment):
        """Test assignment string representation."""
        assert "user@example.com" in str(assignment)
        assert "M365-E5" in str(assignment)

    def test_assignment_revocation(self, assignment, user):
        """Test assignment revocation fields."""
        assignment.status = AssignmentStatus.REVOKED
        assignment.revoked_by = user
        assignment.revoked_at = timezone.now()
        assignment.revocation_reason = "User left company"
        assignment.save()

        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.REVOKED
        assert assignment.revoked_by == user


class TestConsumptionSignalModel:
    """Tests for ConsumptionSignal model."""

    def test_create_signal(self, db, sku):
        """Test creating a consumption signal."""
        signal = ConsumptionSignal.objects.create(
            source_system="entra_id",
            raw_id="LOGIN-12345",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku=sku,
        )
        assert signal.id is not None
        assert signal.is_processed is False

    def test_signal_str(self, db, sku):
        """Test signal string representation."""
        signal = ConsumptionSignal.objects.create(
            source_system="intune",
            raw_id="APP-USAGE-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.DEVICE,
            principal_id="DEVICE-001",
            sku=sku,
        )
        assert "intune" in str(signal)


class TestConsumptionUnitModel:
    """Tests for ConsumptionUnit model."""

    def test_create_unit(self, db, sku, assignment):
        """Test creating a consumption unit."""
        unit = ConsumptionUnit.objects.create(
            sku=sku,
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            assignment=assignment,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        assert unit.id is not None
        assert unit.is_active is True

    def test_unit_str(self, db, sku, assignment):
        """Test unit string representation."""
        unit = ConsumptionUnit.objects.create(
            sku=sku,
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            assignment=assignment,
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now(),
        )
        assert "user@example.com" in str(unit)


class TestConsumptionSnapshotModel:
    """Tests for ConsumptionSnapshot model."""

    def test_create_snapshot(self, db, sku, pool, user):
        """Test creating a consumption snapshot."""
        run = ReconciliationRun.objects.create(triggered_by=user)
        snapshot = ConsumptionSnapshot.objects.create(
            sku=sku,
            pool=pool,
            reconciliation_run=run,
            entitled_quantity=100,
            allocated_quantity=50,
            consumed_quantity=25,
            available_quantity=25,
            utilization_percent=Decimal("50.0"),
        )
        assert snapshot.id is not None
        assert snapshot.evidence_pack_ref is not None

    def test_snapshot_immutable_hash(self, db, sku, user):
        """Test snapshot generates hash."""
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
        assert snapshot.evidence_pack_hash is not None
        assert len(snapshot.evidence_pack_hash) == 64  # SHA-256


class TestReconciliationRunModel:
    """Tests for ReconciliationRun model."""

    def test_create_run(self, db, user):
        """Test creating a reconciliation run."""
        run = ReconciliationRun.objects.create(triggered_by=user)
        assert run.id is not None
        assert run.status == ReconciliationStatus.PENDING

    def test_run_completion(self, db, user):
        """Test run completion."""
        run = ReconciliationRun.objects.create(
            triggered_by=user,
            status=ReconciliationStatus.RUNNING,
            started_at=timezone.now(),
        )
        run.status = ReconciliationStatus.COMPLETED
        run.completed_at = timezone.now()
        run.skus_processed = 10
        run.snapshots_created = 50
        run.alerts_generated = 2
        run.save()

        run.refresh_from_db()
        assert run.status == ReconciliationStatus.COMPLETED
        assert run.skus_processed == 10


class TestLicenseAlertModel:
    """Tests for LicenseAlert model."""

    def test_create_alert(self, db, sku):
        """Test creating a license alert."""
        alert = LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.OVER_ALLOCATION,
            severity=AlertSeverity.HIGH,
            title="Over-allocation detected",
            message="SKU M365-E5 is over-allocated by 10 licenses.",
        )
        assert alert.id is not None
        assert alert.acknowledged is False

    def test_alert_acknowledge(self, db, sku, user):
        """Test alert acknowledgement."""
        alert = LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.EXPIRY_WARNING,
            severity=AlertSeverity.MEDIUM,
            title="Entitlement expiring soon",
            message="Entitlement expires in 30 days.",
        )
        alert.acknowledged = True
        alert.acknowledged_by = user
        alert.acknowledged_at = timezone.now()
        alert.resolution_notes = "Renewal in progress"
        alert.save()

        alert.refresh_from_db()
        assert alert.acknowledged is True

    def test_alert_str(self, db, sku):
        """Test alert string representation."""
        alert = LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.CONSUMPTION_SPIKE,
            severity=AlertSeverity.LOW,
            title="Spike detected",
            message="Consumption spike detected.",
        )
        assert "consumption_spike" in str(alert).lower()


class TestImportJobModel:
    """Tests for ImportJob model."""

    def test_create_import_job(self, db, user):
        """Test creating an import job."""
        job = ImportJob.objects.create(
            source_type="csv",
            filename="licenses.csv",
            uploaded_by=user,
        )
        assert job.id is not None
        assert job.status == "pending"

    def test_import_job_completion(self, db, user):
        """Test import job completion."""
        job = ImportJob.objects.create(
            source_type="api",
            filename="",
            uploaded_by=user,
        )
        job.status = "completed"
        job.completed_at = timezone.now()
        job.records_processed = 100
        job.records_succeeded = 95
        job.records_failed = 5
        job.save()

        job.refresh_from_db()
        assert job.status == "completed"
        assert job.records_processed == 100
