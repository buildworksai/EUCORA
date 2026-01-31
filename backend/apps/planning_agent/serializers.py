# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for Planning Agent API.
"""
from rest_framework import serializers

from .models import (
    BlastRadiusAnalysis,
    ChangeFreezePeriod,
    DeploymentPlan,
    DeploymentWindow,
    RingAssignment,
    RingDevice,
    RollbackPlan,
)


class DeploymentPlanSerializer(serializers.ModelSerializer):
    """Serializer for deployment plans."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    ring_count = serializers.SerializerMethodField()
    total_devices = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source="created_by.username", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.username", read_only=True, allow_null=True)

    class Meta:
        model = DeploymentPlan
        fields = [
            "id",
            "correlation_id",
            "name",
            "application",
            "application_name",
            "version",
            "target_scope",
            "status",
            "input_request",
            "reasoning",
            "overall_risk_score",
            "risk_factors",
            "created_by",
            "created_by_name",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "ring_count",
            "total_devices",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at", "approved_at"]

    def get_ring_count(self, obj: DeploymentPlan) -> int:
        """Get count of rings."""
        return obj.rings.count()

    def get_total_devices(self, obj: DeploymentPlan) -> int:
        """Get total device count across all rings."""
        return sum(ring.device_count for ring in obj.rings.all())


class RingAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ring assignments."""

    plan_name = serializers.CharField(source="plan.name", read_only=True)
    device_count_actual = serializers.SerializerMethodField()

    class Meta:
        model = RingAssignment
        fields = [
            "id",
            "plan",
            "plan_name",
            "ring_number",
            "ring_name",
            "device_count",
            "device_count_actual",
            "device_criteria",
            "scheduled_start",
            "scheduled_end",
            "success_threshold",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_device_count_actual(self, obj: RingAssignment) -> int:
        """Get actual device count."""
        return obj.devices.count()


class RingDeviceSerializer(serializers.ModelSerializer):
    """Serializer for ring devices."""

    ring_name = serializers.CharField(source="ring.ring_name", read_only=True)

    class Meta:
        model = RingDevice
        fields = [
            "id",
            "ring",
            "ring_name",
            "device_id",
            "device_name",
            "user_principal",
            "selection_reason",
            "health_score",
            "criticality",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DeploymentWindowSerializer(serializers.ModelSerializer):
    """Serializer for deployment windows."""

    class Meta:
        model = DeploymentWindow
        fields = [
            "id",
            "name",
            "description",
            "day_of_week",
            "start_time",
            "end_time",
            "timezone",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChangeFreezePeriodSerializer(serializers.ModelSerializer):
    """Serializer for change freeze periods."""

    class Meta:
        model = ChangeFreezePeriod
        fields = [
            "id",
            "name",
            "reason",
            "start_date",
            "end_date",
            "scope",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class BlastRadiusAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for blast radius analysis."""

    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = BlastRadiusAnalysis
        fields = [
            "id",
            "correlation_id",
            "plan",
            "plan_name",
            "total_users_affected",
            "vip_users_affected",
            "departments_affected",
            "regions_affected",
            "critical_systems_affected",
            "productivity_impact_score",
            "recommendations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]


class RollbackPlanSerializer(serializers.ModelSerializer):
    """Serializer for rollback plans."""

    deployment_plan_name = serializers.CharField(source="deployment_plan.name", read_only=True)

    class Meta:
        model = RollbackPlan
        fields = [
            "id",
            "deployment_plan",
            "deployment_plan_name",
            "trigger_conditions",
            "rollback_steps",
            "estimated_duration_minutes",
            "requires_cab_approval",
            "tested",
            "tested_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "tested_at"]
