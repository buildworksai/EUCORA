# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Business logic services for license_management.
"""
import hashlib
import json
import logging
import uuid
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from .models import (
    AlertSeverity,
    AlertType,
    Assignment,
    AssignmentStatus,
    ConsumptionSignal,
    ConsumptionSnapshot,
    ConsumptionUnit,
    Entitlement,
    EntitlementStatus,
    LicenseAlert,
    LicensePool,
    LicenseSKU,
    ReconciliationRun,
    ReconciliationStatus,
    Vendor,
)

logger = logging.getLogger(__name__)

# Reconciliation ruleset version
RECONCILIATION_RULESET_VERSION = "1.0.0"

# Stale threshold for reconciliation (2x the scheduled interval)
STALE_THRESHOLD_SECONDS = 7200  # 2 hours


class LicenseSummaryService:
    """Service for computing license summary statistics."""

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        """
        Get overall license summary.

        Returns:
            Dictionary with summary statistics and health status.
        """
        # Get totals from latest snapshots (SKU-level only, no pool)
        latest_snapshots = []
        for sku in LicenseSKU.objects.filter(is_active=True):
            snapshot = sku.consumption_snapshots.filter(pool__isnull=True).order_by("-reconciled_at").first()
            if snapshot:
                latest_snapshots.append(snapshot)

        total_entitled = sum(s.entitled for s in latest_snapshots)
        total_consumed = sum(s.consumed for s in latest_snapshots)
        total_remaining = sum(s.remaining for s in latest_snapshots)

        # Get last reconciliation time
        last_run = (
            ReconciliationRun.objects.filter(status=ReconciliationStatus.COMPLETED).order_by("-completed_at").first()
        )
        last_reconciled_at = last_run.completed_at if last_run else None

        # Determine health status
        health_status, health_message, stale_duration = LicenseSummaryService._compute_health(
            last_reconciled_at, latest_snapshots
        )

        return {
            "total_entitled": total_entitled,
            "total_consumed": total_consumed,
            "total_remaining": total_remaining,
            "last_reconciled_at": last_reconciled_at,
            "health_status": health_status,
            "health_message": health_message,
            "stale_duration_seconds": stale_duration,
            "vendor_count": Vendor.objects.filter(is_active=True).count(),
            "sku_count": LicenseSKU.objects.filter(is_active=True).count(),
            "active_alerts_count": LicenseAlert.objects.filter(acknowledged=False, auto_resolved=False).count(),
        }

    @staticmethod
    def _compute_health(
        last_reconciled_at: Optional[timezone.datetime], snapshots: List[ConsumptionSnapshot]
    ) -> Tuple[str, Optional[str], Optional[int]]:
        """Compute health status based on data freshness and alert state."""
        now = timezone.now()

        # Check for stale data
        if last_reconciled_at:
            stale_seconds = (now - last_reconciled_at).total_seconds()
            if stale_seconds > STALE_THRESHOLD_SECONDS:
                return (
                    "stale",
                    f"Reconciliation data is {int(stale_seconds / 60)} minutes old",
                    int(stale_seconds),
                )
        else:
            return ("failed", "No reconciliation data available", None)

        # Check for overconsumption
        for snapshot in snapshots:
            if snapshot.remaining < 0:
                return (
                    "degraded",
                    f"Overconsumption detected for {snapshot.sku.name}",
                    None,
                )

        # Check for critical alerts
        critical_alerts = LicenseAlert.objects.filter(
            severity=AlertSeverity.CRITICAL, acknowledged=False, auto_resolved=False
        ).count()
        if critical_alerts > 0:
            return ("degraded", f"{critical_alerts} critical alert(s) require attention", None)

        return ("ok", None, None)


class ReconciliationService:
    """Service for license reconciliation operations."""

    def __init__(self, triggered_by=None, correlation_id: Optional[str] = None):
        """
        Initialize reconciliation service.

        Args:
            triggered_by: User who triggered the reconciliation
            correlation_id: Correlation ID for tracing
        """
        self.triggered_by = triggered_by
        self.correlation_id = correlation_id or str(uuid.uuid4())

    @transaction.atomic
    def run_reconciliation(self) -> ReconciliationRun:
        """
        Execute a full reconciliation run.

        Creates ConsumptionSnapshots for all active SKUs.

        Returns:
            ReconciliationRun instance with results.
        """
        run = ReconciliationRun.objects.create(
            ruleset_version=RECONCILIATION_RULESET_VERSION,
            triggered_by=self.triggered_by,
            trigger_type="manual" if self.triggered_by else "scheduled",
        )
        run.correlation_id = uuid.UUID(self.correlation_id)
        run.save()

        try:
            active_skus = LicenseSKU.objects.filter(is_active=True)
            run.skus_total = active_skus.count()
            run.save()

            for sku in active_skus:
                try:
                    self._reconcile_sku(sku, run)
                    run.skus_processed += 1
                    run.save()
                except Exception as e:
                    logger.exception(f"Error reconciling SKU {sku.sku_code}: {e}")
                    run.errors.append({"sku_id": str(sku.id), "error": str(e)})
                    run.save()

            run.status = ReconciliationStatus.COMPLETED
            run.completed_at = timezone.now()
            run.save()

            # Generate alerts for anomalies
            self._generate_alerts(run)

        except Exception as e:
            logger.exception(f"Reconciliation run failed: {e}")
            run.status = ReconciliationStatus.FAILED
            run.completed_at = timezone.now()
            run.errors.append({"error": str(e)})
            run.save()

        return run

    def _reconcile_sku(self, sku: LicenseSKU, run: ReconciliationRun) -> None:
        """Reconcile a single SKU and create snapshot."""
        # Calculate entitled from active entitlements
        entitled = (
            Entitlement.objects.filter(
                sku=sku,
                status=EntitlementStatus.ACTIVE,
                start_date__lte=timezone.now().date(),
            )
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=timezone.now().date()))
            .aggregate(total=Sum("entitled_quantity"))["total"]
            or 0
        )

        # Calculate consumed from active consumption units
        consumed = (
            ConsumptionUnit.objects.filter(sku=sku, status=AssignmentStatus.ACTIVE).aggregate(total=Sum("unit_count"))[
                "total"
            ]
            or 0
        )

        # Get reserved from pools
        reserved = (
            LicensePool.objects.filter(sku=sku, is_active=True).aggregate(total=Sum("reserved_quantity"))["total"] or 0
        )

        # Calculate remaining
        remaining = entitled - consumed - reserved

        # Create evidence pack
        evidence = self._generate_evidence_pack(sku, entitled, consumed, reserved)

        # Create snapshot
        ConsumptionSnapshot.objects.create(
            sku=sku,
            reconciled_at=timezone.now(),
            ruleset_version=RECONCILIATION_RULESET_VERSION,
            entitled=entitled,
            consumed=consumed,
            reserved=reserved,
            remaining=remaining,
            evidence_pack_hash=evidence["hash"],
            evidence_pack_ref=evidence["ref"],
            reconciliation_run=run,
        )

        run.snapshots_created += 1

        # Process any pending signals
        pending_signals = ConsumptionSignal.objects.filter(sku=sku, is_processed=False)
        run.signals_processed += pending_signals.count()
        pending_signals.update(is_processed=True, processed_at=timezone.now())

    def _generate_evidence_pack(self, sku: LicenseSKU, entitled: int, consumed: int, reserved: int) -> Dict[str, str]:
        """Generate evidence pack for reconciliation."""
        evidence_data = {
            "sku_id": str(sku.id),
            "sku_code": sku.sku_code,
            "reconciled_at": timezone.now().isoformat(),
            "ruleset_version": RECONCILIATION_RULESET_VERSION,
            "entitled": entitled,
            "consumed": consumed,
            "reserved": reserved,
            "remaining": entitled - consumed - reserved,
            "entitlements": list(
                Entitlement.objects.filter(sku=sku, status=EntitlementStatus.ACTIVE).values(
                    "id", "contract_id", "entitled_quantity"
                )
            ),
            "consumption_units_count": ConsumptionUnit.objects.filter(sku=sku, status=AssignmentStatus.ACTIVE).count(),
        }

        # Convert UUIDs to strings for JSON serialization
        for ent in evidence_data["entitlements"]:
            ent["id"] = str(ent["id"])

        evidence_json = json.dumps(evidence_data, sort_keys=True, default=str)
        evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()

        # In production, this would upload to MinIO and return the path
        evidence_ref = f"evidence/reconciliation/{sku.sku_code}/{timezone.now().strftime('%Y%m%d%H%M%S')}.json"

        return {"hash": evidence_hash, "ref": evidence_ref}

    def _generate_alerts(self, run: ReconciliationRun) -> None:
        """Generate alerts for anomalies detected during reconciliation."""
        # Check for overconsumption
        for snapshot in run.snapshots.all():
            if snapshot.remaining < 0:
                LicenseAlert.objects.create(
                    sku=snapshot.sku,
                    alert_type=AlertType.OVERCONSUMPTION,
                    severity=AlertSeverity.CRITICAL,
                    message=f"License overconsumption detected: {abs(snapshot.remaining)} units over entitled",
                    details={
                        "entitled": snapshot.entitled,
                        "consumed": snapshot.consumed,
                        "remaining": snapshot.remaining,
                        "reconciliation_run_id": str(run.id),
                    },
                )

        # Check for expiring entitlements (within 30 days)
        expiring_threshold = timezone.now().date() + timedelta(days=30)
        expiring_entitlements = Entitlement.objects.filter(
            status=EntitlementStatus.ACTIVE,
            end_date__isnull=False,
            end_date__lte=expiring_threshold,
        )
        for entitlement in expiring_entitlements:
            # Check if alert already exists
            existing = LicenseAlert.objects.filter(
                sku=entitlement.sku,
                alert_type=AlertType.EXPIRING,
                acknowledged=False,
                auto_resolved=False,
                details__entitlement_id=str(entitlement.id),
            ).exists()
            if not existing:
                LicenseAlert.objects.create(
                    sku=entitlement.sku,
                    alert_type=AlertType.EXPIRING,
                    severity=AlertSeverity.WARNING,
                    message=f"Entitlement expiring on {entitlement.end_date}",
                    details={
                        "entitlement_id": str(entitlement.id),
                        "contract_id": entitlement.contract_id,
                        "end_date": str(entitlement.end_date),
                        "days_until_expiry": entitlement.days_until_expiry,
                    },
                )


class ConsumptionSignalService:
    """Service for processing consumption signals."""

    @staticmethod
    @transaction.atomic
    def ingest_signal(
        source_system: str,
        raw_id: str,
        timestamp: timezone.datetime,
        principal_type: str,
        principal_id: str,
        sku_id: str,
        confidence: float = 1.0,
        raw_payload: Optional[Dict] = None,
        principal_name: str = "",
    ) -> ConsumptionSignal:
        """
        Ingest a consumption signal from a source system.

        Args:
            source_system: Source system identifier (intune, jamf, etc.)
            raw_id: ID from source system
            timestamp: When consumption was detected
            principal_type: Type of principal (user, device)
            principal_id: Principal identifier
            sku_id: License SKU ID
            confidence: Match confidence (0.0-1.0)
            raw_payload: Original signal payload
            principal_name: Principal display name

        Returns:
            Created ConsumptionSignal instance.
        """
        # Check for duplicate
        existing = ConsumptionSignal.objects.filter(source_system=source_system, raw_id=raw_id).first()
        if existing:
            logger.info(f"Duplicate signal received: {source_system}:{raw_id}")
            return existing

        # Get SKU
        try:
            sku = LicenseSKU.objects.get(id=sku_id)
        except LicenseSKU.DoesNotExist:
            raise ValueError(f"Invalid SKU ID: {sku_id}")

        # Compute payload hash
        payload_json = json.dumps(raw_payload or {}, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

        signal = ConsumptionSignal.objects.create(
            source_system=source_system,
            raw_id=raw_id,
            timestamp=timestamp,
            principal_type=principal_type,
            principal_id=principal_id,
            principal_name=principal_name,
            sku=sku,
            confidence=confidence,
            raw_payload_hash=payload_hash,
            raw_payload=raw_payload or {},
        )

        # Auto-create or update consumption unit if confidence is high enough
        if confidence >= 0.9:
            ConsumptionSignalService._update_consumption_unit(signal)

        return signal

    @staticmethod
    def _update_consumption_unit(signal: ConsumptionSignal) -> None:
        """Create or update consumption unit from high-confidence signal."""
        # Check if unit already exists for this principal/SKU
        unit = ConsumptionUnit.objects.filter(
            sku=signal.sku,
            principal_type=signal.principal_type,
            principal_id=signal.principal_id,
            status=AssignmentStatus.ACTIVE,
        ).first()

        if unit:
            # Add signal to existing unit
            unit.signals.add(signal)
        else:
            # Create new unit
            unit = ConsumptionUnit.objects.create(
                sku=signal.sku,
                principal_type=signal.principal_type,
                principal_id=signal.principal_id,
                principal_name=signal.principal_name,
                effective_from=signal.timestamp,
                status=AssignmentStatus.ACTIVE,
            )
            unit.signals.add(signal)

        signal.is_processed = True
        signal.processed_at = timezone.now()
        signal.save()


class EntitlementService:
    """Service for entitlement management."""

    @staticmethod
    @transaction.atomic
    def approve_entitlement(entitlement: Entitlement, approver) -> Entitlement:
        """
        Approve a pending entitlement.

        Args:
            entitlement: Entitlement to approve
            approver: User approving the entitlement

        Returns:
            Updated Entitlement instance.
        """
        if entitlement.status != EntitlementStatus.PENDING:
            raise ValueError(f"Cannot approve entitlement in status: {entitlement.status}")

        entitlement.status = EntitlementStatus.ACTIVE
        entitlement.approved_by = approver
        entitlement.approved_at = timezone.now()
        entitlement.save()

        logger.info(f"Entitlement {entitlement.id} approved by {approver.username}")
        return entitlement

    @staticmethod
    @transaction.atomic
    def expire_entitlements() -> int:
        """
        Expire entitlements past their end date.

        Returns:
            Number of entitlements expired.
        """
        today = timezone.now().date()
        expired = Entitlement.objects.filter(status=EntitlementStatus.ACTIVE, end_date__lt=today).update(
            status=EntitlementStatus.EXPIRED
        )

        if expired > 0:
            logger.info(f"Expired {expired} entitlements")

        return expired


class AssignmentService:
    """Service for license assignment management."""

    @staticmethod
    @transaction.atomic
    def revoke_assignment(assignment: Assignment, revoker, reason: str = "") -> Assignment:
        """
        Revoke a license assignment.

        Args:
            assignment: Assignment to revoke
            revoker: User revoking the assignment
            reason: Reason for revocation

        Returns:
            Updated Assignment instance.
        """
        if assignment.status != AssignmentStatus.ACTIVE:
            raise ValueError(f"Cannot revoke assignment in status: {assignment.status}")

        assignment.status = AssignmentStatus.REVOKED
        assignment.revoked_by = revoker
        assignment.revoked_at = timezone.now()
        assignment.revocation_reason = reason
        assignment.save()

        logger.info(f"Assignment {assignment.id} revoked by {revoker.username}")
        return assignment

    @staticmethod
    @transaction.atomic
    def expire_assignments() -> int:
        """
        Expire assignments past their expiry date.

        Returns:
            Number of assignments expired.
        """
        now = timezone.now()
        expired = Assignment.objects.filter(status=AssignmentStatus.ACTIVE, expires_at__lt=now).update(
            status=AssignmentStatus.EXPIRED
        )

        if expired > 0:
            logger.info(f"Expired {expired} assignments")

        return expired
