# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for license_management API.
"""
from rest_framework import serializers

from .models import (
    Assignment,
    ConsumptionSignal,
    ConsumptionSnapshot,
    ConsumptionUnit,
    Entitlement,
    ImportJob,
    LicenseAlert,
    LicensePool,
    LicenseSKU,
    ReconciliationRun,
    Vendor,
)


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model."""

    class Meta:
        model = Vendor
        fields = [
            "id",
            "name",
            "identifier",
            "website",
            "support_contact",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class VendorListSerializer(serializers.ModelSerializer):
    """Compact serializer for vendor lists."""

    sku_count = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ["id", "name", "identifier", "is_active", "sku_count"]

    def get_sku_count(self, obj: Vendor) -> int:
        """Get count of SKUs for this vendor."""
        return obj.skus.filter(is_active=True).count()


class LicenseSKUSerializer(serializers.ModelSerializer):
    """Serializer for LicenseSKU model."""

    vendor_name = serializers.CharField(source="vendor.name", read_only=True)

    class Meta:
        model = LicenseSKU
        fields = [
            "id",
            "vendor",
            "vendor_name",
            "sku_code",
            "name",
            "description",
            "license_model_type",
            "unit_rules",
            "normalization_rules",
            "is_active",
            "requires_approval",
            "cost_per_unit",
            "currency",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LicenseSKUListSerializer(serializers.ModelSerializer):
    """Compact serializer for SKU lists with consumption data."""

    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    entitled = serializers.SerializerMethodField()
    consumed = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = LicenseSKU
        fields = [
            "id",
            "vendor_name",
            "sku_code",
            "name",
            "license_model_type",
            "is_active",
            "entitled",
            "consumed",
            "remaining",
        ]

    def get_entitled(self, obj: LicenseSKU) -> int:
        """Get total entitled quantity from latest snapshot."""
        snapshot = obj.consumption_snapshots.filter(pool__isnull=True).order_by("-reconciled_at").first()
        return snapshot.entitled if snapshot else 0

    def get_consumed(self, obj: LicenseSKU) -> int:
        """Get total consumed quantity from latest snapshot."""
        snapshot = obj.consumption_snapshots.filter(pool__isnull=True).order_by("-reconciled_at").first()
        return snapshot.consumed if snapshot else 0

    def get_remaining(self, obj: LicenseSKU) -> int:
        """Get remaining quantity from latest snapshot."""
        snapshot = obj.consumption_snapshots.filter(pool__isnull=True).order_by("-reconciled_at").first()
        return snapshot.remaining if snapshot else 0


class EntitlementSerializer(serializers.ModelSerializer):
    """Serializer for Entitlement model."""

    sku_name = serializers.CharField(source="sku.name", read_only=True)
    vendor_name = serializers.CharField(source="sku.vendor.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)

    class Meta:
        model = Entitlement
        fields = [
            "id",
            "sku",
            "sku_name",
            "vendor_name",
            "contract_id",
            "entitled_quantity",
            "start_date",
            "end_date",
            "renewal_date",
            "terms",
            "document_refs",
            "status",
            "notes",
            "created_by",
            "created_by_username",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "is_expired",
            "days_until_expiry",
            "correlation_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "approved_by",
            "approved_at",
            "correlation_id",
            "created_at",
            "updated_at",
        ]


class EntitlementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating entitlements."""

    class Meta:
        model = Entitlement
        fields = [
            "sku",
            "contract_id",
            "entitled_quantity",
            "start_date",
            "end_date",
            "renewal_date",
            "terms",
            "document_refs",
            "notes",
        ]

    def create(self, validated_data):
        """Create entitlement with audit fields."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["created_by"] = request.user
        return super().create(validated_data)


class LicensePoolSerializer(serializers.ModelSerializer):
    """Serializer for LicensePool model."""

    sku_name = serializers.CharField(source="sku.name", read_only=True)

    class Meta:
        model = LicensePool
        fields = [
            "id",
            "sku",
            "sku_name",
            "name",
            "description",
            "scope_type",
            "scope_value",
            "entitled_quantity_override",
            "reserved_quantity",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model."""

    pool_name = serializers.CharField(source="pool.name", read_only=True)
    sku_name = serializers.CharField(source="pool.sku.name", read_only=True)
    assigned_by_username = serializers.CharField(source="assigned_by.username", read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id",
            "pool",
            "pool_name",
            "sku_name",
            "principal_type",
            "principal_id",
            "principal_name",
            "assigned_at",
            "expires_at",
            "status",
            "assigned_by",
            "assigned_by_username",
            "revoked_by",
            "revoked_at",
            "revocation_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assigned_at",
            "assigned_by",
            "revoked_by",
            "revoked_at",
            "created_at",
            "updated_at",
        ]


class AssignmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating assignments."""

    class Meta:
        model = Assignment
        fields = ["pool", "principal_type", "principal_id", "principal_name", "expires_at"]

    def create(self, validated_data):
        """Create assignment with audit fields."""
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            validated_data["assigned_by"] = request.user
        return super().create(validated_data)


class ConsumptionSignalSerializer(serializers.ModelSerializer):
    """Serializer for ConsumptionSignal model."""

    sku_name = serializers.CharField(source="sku.name", read_only=True)

    class Meta:
        model = ConsumptionSignal
        fields = [
            "id",
            "source_system",
            "raw_id",
            "timestamp",
            "principal_type",
            "principal_id",
            "principal_name",
            "sku",
            "sku_name",
            "confidence",
            "is_processed",
            "processed_at",
            "created_at",
        ]
        read_only_fields = ["id", "is_processed", "processed_at", "created_at"]


class ConsumptionUnitSerializer(serializers.ModelSerializer):
    """Serializer for ConsumptionUnit model."""

    sku_name = serializers.CharField(source="sku.name", read_only=True)
    pool_name = serializers.CharField(source="pool.name", read_only=True)
    signal_count = serializers.SerializerMethodField()

    class Meta:
        model = ConsumptionUnit
        fields = [
            "id",
            "sku",
            "sku_name",
            "pool",
            "pool_name",
            "principal_type",
            "principal_id",
            "principal_name",
            "effective_from",
            "effective_to",
            "status",
            "unit_count",
            "signal_count",
            "created_at",
        ]

    def get_signal_count(self, obj: ConsumptionUnit) -> int:
        """Get count of source signals."""
        return obj.signals.count()


class ConsumptionSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for ConsumptionSnapshot model."""

    sku_name = serializers.CharField(source="sku.name", read_only=True)
    sku_code = serializers.CharField(source="sku.sku_code", read_only=True)
    vendor_name = serializers.CharField(source="sku.vendor.name", read_only=True)
    pool_name = serializers.CharField(source="pool.name", read_only=True)

    class Meta:
        model = ConsumptionSnapshot
        fields = [
            "id",
            "sku",
            "sku_name",
            "sku_code",
            "vendor_name",
            "pool",
            "pool_name",
            "reconciled_at",
            "ruleset_version",
            "entitled",
            "consumed",
            "reserved",
            "remaining",
            "utilization_percent",
            "evidence_pack_hash",
            "evidence_pack_ref",
            "reconciliation_run",
        ]


class ReconciliationRunSerializer(serializers.ModelSerializer):
    """Serializer for ReconciliationRun model."""

    triggered_by_username = serializers.CharField(source="triggered_by.username", read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    progress_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = ReconciliationRun
        fields = [
            "id",
            "status",
            "ruleset_version",
            "started_at",
            "completed_at",
            "skus_total",
            "skus_processed",
            "snapshots_created",
            "signals_processed",
            "errors",
            "diff_summary",
            "triggered_by",
            "triggered_by_username",
            "trigger_type",
            "duration_seconds",
            "progress_percent",
            "correlation_id",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at"]


class LicenseAlertSerializer(serializers.ModelSerializer):
    """Serializer for LicenseAlert model."""

    sku_name = serializers.CharField(source="sku.name", read_only=True)
    pool_name = serializers.CharField(source="pool.name", read_only=True)
    acknowledged_by_username = serializers.CharField(source="acknowledged_by.username", read_only=True)

    class Meta:
        model = LicenseAlert
        fields = [
            "id",
            "sku",
            "sku_name",
            "pool",
            "pool_name",
            "alert_type",
            "severity",
            "message",
            "details",
            "detected_at",
            "acknowledged",
            "acknowledged_by",
            "acknowledged_by_username",
            "acknowledged_at",
            "resolution_notes",
            "auto_resolved",
            "resolved_at",
        ]
        read_only_fields = ["id", "detected_at", "acknowledged_by", "acknowledged_at", "resolved_at"]


class ImportJobSerializer(serializers.ModelSerializer):
    """Serializer for ImportJob model."""

    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = ImportJob
        fields = [
            "id",
            "import_type",
            "status",
            "file_name",
            "file_hash",
            "file_ref",
            "total_rows",
            "processed_rows",
            "success_count",
            "error_count",
            "validation_errors",
            "import_errors",
            "started_at",
            "completed_at",
            "uploaded_by",
            "uploaded_by_username",
            "progress_percent",
            "correlation_id",
            "created_at",
        ]
        read_only_fields = ["id", "uploaded_by", "correlation_id", "created_at"]

    def get_progress_percent(self, obj: ImportJob) -> float:
        """Calculate import progress percentage."""
        if obj.total_rows == 0:
            return 0.0
        return (obj.processed_rows / obj.total_rows) * 100


class LicenseSummarySerializer(serializers.Serializer):
    """Serializer for license summary response."""

    total_entitled = serializers.IntegerField()
    total_consumed = serializers.IntegerField()
    total_remaining = serializers.IntegerField()
    last_reconciled_at = serializers.DateTimeField(allow_null=True)
    health_status = serializers.ChoiceField(choices=["ok", "degraded", "failed", "stale"])
    health_message = serializers.CharField(allow_null=True, required=False)
    stale_duration_seconds = serializers.IntegerField(allow_null=True, required=False)
    vendor_count = serializers.IntegerField()
    sku_count = serializers.IntegerField()
    active_alerts_count = serializers.IntegerField()
