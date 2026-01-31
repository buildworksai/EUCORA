# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for SLA Governance Agent API.
"""
from rest_framework import serializers

from .models import (
    KPIDefinition,
    KPIMeasurement,
    ServiceCatalogItem,
    SLABreach,
    SLACompliance,
    SLADefinition,
    SLAKPILink,
    SLATarget,
    SLATemplate,
)


class ServiceCatalogItemSerializer(serializers.ModelSerializer):
    """Serializer for service catalog items."""

    sla_count = serializers.SerializerMethodField()

    class Meta:
        model = ServiceCatalogItem
        fields = [
            "id",
            "name",
            "description",
            "category",
            "owner",
            "status",
            "servicenow_sys_id",
            "sla_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_sla_count(self, obj: ServiceCatalogItem) -> int:
        """Get count of SLAs for this service."""
        return obj.slas.count()


class SLATargetSerializer(serializers.ModelSerializer):
    """Serializer for SLA targets."""

    kpi_count = serializers.SerializerMethodField()

    class Meta:
        model = SLATarget
        fields = [
            "id",
            "sla",
            "name",
            "metric_type",
            "target_value",
            "target_unit",
            "measurement_period",
            "applies_to",
            "kpi_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_kpi_count(self, obj: SLATarget) -> int:
        """Get count of linked KPIs."""
        return obj.kpi_links.count()


class SLADefinitionSerializer(serializers.ModelSerializer):
    """Serializer for SLA definitions."""

    service_name = serializers.CharField(source="service.name", read_only=True)
    target_count = serializers.SerializerMethodField()
    compliance_status = serializers.SerializerMethodField()
    breach_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.username", read_only=True, allow_null=True)

    class Meta:
        model = SLADefinition
        fields = [
            "id",
            "correlation_id",
            "name",
            "description",
            "service",
            "service_name",
            "version",
            "effective_from",
            "effective_until",
            "status",
            "original_request",
            "created_by",
            "created_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "target_count",
            "compliance_status",
            "breach_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at", "approved_at"]

    def get_target_count(self, obj: SLADefinition) -> int:
        """Get count of SLA targets."""
        return obj.targets.count()

    def get_compliance_status(self, obj: SLADefinition) -> str:
        """Get latest compliance status."""
        latest = obj.compliance_records.first()
        return latest.status if latest else None

    def get_breach_count(self, obj: SLADefinition) -> int:
        """Get count of breaches."""
        return obj.breaches.count()


class KPIDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for KPI definitions."""

    measurement_count = serializers.SerializerMethodField()
    latest_value = serializers.SerializerMethodField()
    latest_status = serializers.SerializerMethodField()

    class Meta:
        model = KPIDefinition
        fields = [
            "id",
            "name",
            "description",
            "formula",
            "data_sources",
            "unit",
            "direction",
            "thresholds",
            "is_active",
            "measurement_count",
            "latest_value",
            "latest_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_measurement_count(self, obj: KPIDefinition) -> int:
        """Get count of measurements."""
        return obj.measurements.count()

    def get_latest_value(self, obj: KPIDefinition) -> float:
        """Get latest measurement value."""
        latest = obj.measurements.first()
        return latest.value if latest else None

    def get_latest_status(self, obj: KPIDefinition) -> str:
        """Get latest measurement status."""
        latest = obj.measurements.first()
        return latest.status if latest else None


class SLAKPILinkSerializer(serializers.ModelSerializer):
    """Serializer for SLA-KPI links."""

    sla_target_name = serializers.CharField(source="sla_target.name", read_only=True)
    kpi_name = serializers.CharField(source="kpi.name", read_only=True)

    class Meta:
        model = SLAKPILink
        fields = [
            "id",
            "sla_target",
            "sla_target_name",
            "kpi",
            "kpi_name",
            "weight",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class KPIMeasurementSerializer(serializers.ModelSerializer):
    """Serializer for KPI measurements."""

    kpi_name = serializers.CharField(source="kpi.name", read_only=True)
    kpi_unit = serializers.CharField(source="kpi.unit", read_only=True)

    class Meta:
        model = KPIMeasurement
        fields = [
            "id",
            "kpi",
            "kpi_name",
            "kpi_unit",
            "measurement_time",
            "value",
            "status",
            "data_points",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SLAComplianceSerializer(serializers.ModelSerializer):
    """Serializer for SLA compliance records."""

    sla_name = serializers.CharField(source="sla.name", read_only=True)
    sla_version = serializers.CharField(source="sla.version", read_only=True)

    class Meta:
        model = SLACompliance
        fields = [
            "id",
            "correlation_id",
            "sla",
            "sla_name",
            "sla_version",
            "period_start",
            "period_end",
            "overall_compliance",
            "target_compliances",
            "breach_count",
            "near_miss_count",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class SLABreachSerializer(serializers.ModelSerializer):
    """Serializer for SLA breaches."""

    sla_name = serializers.CharField(source="sla.name", read_only=True)
    target_name = serializers.CharField(source="target.name", read_only=True)

    class Meta:
        model = SLABreach
        fields = [
            "id",
            "correlation_id",
            "sla",
            "sla_name",
            "target",
            "target_name",
            "breach_time",
            "severity",
            "target_value",
            "actual_value",
            "root_cause",
            "remediation",
            "servicenow_incident",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class SLATemplateSerializer(serializers.ModelSerializer):
    """Serializer for SLA templates."""

    class Meta:
        model = SLATemplate
        fields = [
            "id",
            "name",
            "description",
            "category",
            "default_targets",
            "variables",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
