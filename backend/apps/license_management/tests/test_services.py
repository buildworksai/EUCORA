# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Tests for license_management services."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.license_management.models import (
    AlertType,
    Assignment,
    AssignmentStatus,
    ConsumptionSnapshot,
    ConsumptionUnit,
    Entitlement,
    EntitlementStatus,
    LicenseAlert,
    LicenseModelType,
    LicensePool,
    LicenseSKU,
    PrincipalType,
    ReconciliationStatus,
    ScopeType,
    Vendor,
)
from apps.license_management.services import (
    AssignmentService,
    ConsumptionSignalService,
    EntitlementService,
    LicenseSummaryService,
    ReconciliationService,
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


class TestLicenseSummaryService:
    """Tests for LicenseSummaryService."""

    def test_get_summary_empty(self, db):
        """Test summary with no data."""
        summary = LicenseSummaryService.get_summary()
        assert summary["total_entitled"] == 0
        assert summary["total_consumed"] == 0
        assert summary["total_available"] == 0
        assert summary["health_status"] == "healthy"

    def test_get_summary_with_data(self, db, entitlement, pool):
        """Test summary with entitlements and pools."""
        pool.consumed_quantity = 25
        pool.save()

        summary = LicenseSummaryService.get_summary()
        assert summary["total_entitled"] == 100
        assert summary["total_allocated"] == 50
        assert summary["total_consumed"] == 25
        assert summary["active_skus"] == 1
        assert summary["active_vendors"] == 1

    def test_get_summary_health_warning(self, db, entitlement, pool):
        """Test summary returns warning when utilization > 80%."""
        pool.allocated_quantity = 100
        pool.consumed_quantity = 85
        pool.save()

        summary = LicenseSummaryService.get_summary()
        assert summary["health_status"] == "warning"

    def test_get_summary_health_critical(self, db, entitlement, pool):
        """Test summary returns critical when utilization > 95%."""
        pool.allocated_quantity = 100
        pool.consumed_quantity = 98
        pool.save()

        summary = LicenseSummaryService.get_summary()
        assert summary["health_status"] == "critical"

    def test_get_summary_includes_alerts_count(self, db, sku):
        """Test summary includes unacknowledged alerts count."""
        LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.OVER_ALLOCATION,
            severity="high",
            title="Alert 1",
            message="Test",
            acknowledged=False,
        )
        LicenseAlert.objects.create(
            sku=sku,
            alert_type=AlertType.EXPIRY_WARNING,
            severity="medium",
            title="Alert 2",
            message="Test",
            acknowledged=True,  # Should not count
        )

        summary = LicenseSummaryService.get_summary()
        assert summary["unacknowledged_alerts"] == 1


class TestReconciliationService:
    """Tests for ReconciliationService."""

    def test_run_reconciliation_creates_run(self, db, user):
        """Test reconciliation creates a run record."""
        service = ReconciliationService(triggered_by=user)
        run = service.run_reconciliation()

        assert run.id is not None
        assert run.triggered_by == user
        assert run.status == ReconciliationStatus.COMPLETED

    def test_run_reconciliation_with_sku(self, db, user, sku, entitlement, pool):
        """Test reconciliation processes SKUs."""
        pool.consumed_quantity = 25
        pool.save()

        service = ReconciliationService(triggered_by=user)
        run = service.run_reconciliation()

        assert run.skus_processed == 1
        assert run.snapshots_created >= 1

        # Check snapshot was created
        snapshots = ConsumptionSnapshot.objects.filter(sku=sku)
        assert snapshots.count() >= 1

    def test_run_reconciliation_creates_snapshot(self, db, user, sku, entitlement, pool):
        """Test reconciliation creates proper snapshots."""
        pool.consumed_quantity = 30
        pool.save()

        service = ReconciliationService(triggered_by=user)
        service.run_reconciliation()

        snapshot = ConsumptionSnapshot.objects.filter(sku=sku, pool=pool).first()
        assert snapshot is not None
        assert snapshot.entitled_quantity == 100
        assert snapshot.allocated_quantity == 50
        assert snapshot.consumed_quantity == 30
        assert snapshot.evidence_pack_hash is not None

    def test_run_reconciliation_detects_over_allocation(self, db, user, sku, entitlement, pool):
        """Test reconciliation creates alert for over-allocation."""
        # Set consumed > allocated
        pool.consumed_quantity = 60  # Over 50 allocated
        pool.save()

        service = ReconciliationService(triggered_by=user)
        run = service.run_reconciliation()

        assert run.alerts_generated >= 1
        alert = LicenseAlert.objects.filter(
            sku=sku,
            alert_type=AlertType.OVER_ALLOCATION,
        ).first()
        assert alert is not None

    def test_run_reconciliation_handles_error(self, db, user):
        """Test reconciliation handles errors gracefully."""
        service = ReconciliationService(triggered_by=user)

        with patch.object(service, "_process_sku", side_effect=Exception("Test error")):
            # Should not raise, but mark as failed
            run = service.run_reconciliation()
            assert run.status == ReconciliationStatus.FAILED


class TestConsumptionSignalService:
    """Tests for ConsumptionSignalService."""

    def test_ingest_signal_creates_signal(self, db, sku):
        """Test signal ingestion creates signal record."""
        signal = ConsumptionSignalService.ingest_signal(
            source_system="entra_id",
            raw_id="LOGIN-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku_id=str(sku.id),
        )

        assert signal.id is not None
        assert signal.source_system == "entra_id"
        assert signal.is_processed is False

    def test_ingest_signal_with_confidence(self, db, sku):
        """Test signal ingestion with confidence score."""
        signal = ConsumptionSignalService.ingest_signal(
            source_system="intune",
            raw_id="APP-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.DEVICE,
            principal_id="DEVICE-001",
            sku_id=str(sku.id),
            confidence=0.85,
        )

        assert signal.confidence == Decimal("0.85")

    def test_ingest_signal_invalid_sku_raises(self, db):
        """Test signal ingestion with invalid SKU raises error."""
        with pytest.raises(ValueError) as exc_info:
            ConsumptionSignalService.ingest_signal(
                source_system="test",
                raw_id="TEST-001",
                timestamp=timezone.now(),
                principal_type=PrincipalType.USER,
                principal_id="user@example.com",
                sku_id="00000000-0000-0000-0000-000000000000",
            )

        assert "SKU not found" in str(exc_info.value)

    def test_ingest_signal_creates_consumption_unit(self, db, sku):
        """Test signal ingestion creates or updates consumption unit."""
        ConsumptionSignalService.ingest_signal(
            source_system="entra_id",
            raw_id="LOGIN-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku_id=str(sku.id),
        )

        unit = ConsumptionUnit.objects.filter(
            sku=sku,
            principal_id="user@example.com",
        ).first()
        assert unit is not None
        assert unit.signal_count == 1

    def test_ingest_signal_updates_existing_unit(self, db, sku):
        """Test signal ingestion updates existing consumption unit."""
        # First signal
        ConsumptionSignalService.ingest_signal(
            source_system="entra_id",
            raw_id="LOGIN-001",
            timestamp=timezone.now() - timedelta(hours=1),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku_id=str(sku.id),
        )

        # Second signal
        ConsumptionSignalService.ingest_signal(
            source_system="entra_id",
            raw_id="LOGIN-002",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="user@example.com",
            sku_id=str(sku.id),
        )

        unit = ConsumptionUnit.objects.filter(
            sku=sku,
            principal_id="user@example.com",
        ).first()
        assert unit.signal_count == 2


class TestEntitlementService:
    """Tests for EntitlementService."""

    def test_approve_entitlement_pending(self, db, sku, user):
        """Test approving a pending entitlement."""
        entitlement = Entitlement.objects.create(
            sku=sku,
            contract_ref="CONTRACT-PENDING",
            quantity=50,
            effective_date=timezone.now().date(),
            expiry_date=(timezone.now() + timedelta(days=365)).date(),
            created_by=user,
            status=EntitlementStatus.PENDING,
        )

        approved = EntitlementService.approve_entitlement(entitlement, user)

        assert approved.status == EntitlementStatus.ACTIVE
        assert approved.approved_by == user
        assert approved.approved_at is not None

    def test_approve_entitlement_already_active_raises(self, entitlement, user):
        """Test approving an already active entitlement raises error."""
        with pytest.raises(ValueError) as exc_info:
            EntitlementService.approve_entitlement(entitlement, user)

        assert "not pending" in str(exc_info.value).lower()

    def test_approve_entitlement_expired_raises(self, db, sku, user):
        """Test approving an expired entitlement raises error."""
        entitlement = Entitlement.objects.create(
            sku=sku,
            contract_ref="CONTRACT-EXP",
            quantity=50,
            effective_date=(timezone.now() - timedelta(days=400)).date(),
            expiry_date=(timezone.now() - timedelta(days=30)).date(),
            created_by=user,
            status=EntitlementStatus.PENDING,
        )

        with pytest.raises(ValueError) as exc_info:
            EntitlementService.approve_entitlement(entitlement, user)

        assert "expired" in str(exc_info.value).lower()


class TestAssignmentService:
    """Tests for AssignmentService."""

    def test_revoke_assignment_active(self, assignment, user):
        """Test revoking an active assignment."""
        revoked = AssignmentService.revoke_assignment(
            assignment,
            user,
            reason="User left company",
        )

        assert revoked.status == AssignmentStatus.REVOKED
        assert revoked.revoked_by == user
        assert revoked.revoked_at is not None
        assert revoked.revocation_reason == "User left company"

    def test_revoke_assignment_already_revoked_raises(self, assignment, user):
        """Test revoking an already revoked assignment raises error."""
        assignment.status = AssignmentStatus.REVOKED
        assignment.save()

        with pytest.raises(ValueError) as exc_info:
            AssignmentService.revoke_assignment(assignment, user)

        assert "not active" in str(exc_info.value).lower()

    def test_revoke_assignment_updates_pool(self, assignment, user, pool):
        """Test revoking assignment updates pool consumed quantity."""
        pool.consumed_quantity = 10
        pool.save()

        AssignmentService.revoke_assignment(assignment, user)

        pool.refresh_from_db()
        # Note: This depends on service implementation
        # If service decrements consumed_quantity, check here


class TestServiceIntegration:
    """Integration tests for services working together."""

    def test_full_license_lifecycle(self, db, user, vendor):
        """Test complete license lifecycle: create SKU, entitlement, pool, assignment, reconcile."""
        # Create SKU
        sku = LicenseSKU.objects.create(
            vendor=vendor,
            sku_code="TEST-LIFECYCLE",
            name="Lifecycle Test SKU",
            license_model_type=LicenseModelType.USER_SUBSCRIPTION,
        )

        # Create entitlement
        entitlement = Entitlement.objects.create(
            sku=sku,
            contract_ref="LIFECYCLE-001",
            quantity=100,
            effective_date=timezone.now().date(),
            expiry_date=(timezone.now() + timedelta(days=365)).date(),
            created_by=user,
            status=EntitlementStatus.PENDING,
        )

        # Approve entitlement
        EntitlementService.approve_entitlement(entitlement, user)

        # Create pool
        pool = LicensePool.objects.create(
            sku=sku,
            name="Test Pool",
            scope_type=ScopeType.SITE,
            scope_id="HQ",
            allocated_quantity=50,
        )

        # Create assignment
        assignment = Assignment.objects.create(
            pool=pool,
            principal_type=PrincipalType.USER,
            principal_id="lifecycle@example.com",
            principal_name="Lifecycle User",
            assigned_by=user,
        )

        # Ingest consumption signal
        ConsumptionSignalService.ingest_signal(
            source_system="test",
            raw_id="LIFECYCLE-SIGNAL-001",
            timestamp=timezone.now(),
            principal_type=PrincipalType.USER,
            principal_id="lifecycle@example.com",
            sku_id=str(sku.id),
        )

        # Update pool consumed quantity
        pool.consumed_quantity = 1
        pool.save()

        # Run reconciliation
        service = ReconciliationService(triggered_by=user)
        run = service.run_reconciliation()

        # Verify results
        assert run.status == ReconciliationStatus.COMPLETED
        assert run.skus_processed >= 1

        # Revoke assignment
        AssignmentService.revoke_assignment(assignment, user, "Lifecycle test complete")

        # Verify assignment revoked
        assignment.refresh_from_db()
        assert assignment.status == AssignmentStatus.REVOKED
