# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for SRE Agent API.
"""
from rest_framework import serializers

from .models import (
    HealthCheckResult,
    HealthEndpoint,
    MonitoringPlatform,
    Runbook,
    RunbookExecution,
    SelfHealingExecution,
    SelfHealingRule,
    SLODefinition,
    SLOMetric,
)


class MonitoringPlatformSerializer(serializers.ModelSerializer):
    """Serializer for monitoring platforms."""

    class Meta:
        model = MonitoringPlatform
        fields = [
            "id",
            "name",
            "platform_type",
            "connection_config",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HealthEndpointSerializer(serializers.ModelSerializer):
    """Serializer for health endpoints."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    last_check_status = serializers.SerializerMethodField()

    class Meta:
        model = HealthEndpoint
        fields = [
            "id",
            "name",
            "application",
            "application_name",
            "url",
            "method",
            "expected_status",
            "timeout_seconds",
            "check_interval_minutes",
            "is_active",
            "last_check_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_last_check_status(self, obj: HealthEndpoint) -> str:
        """Get last check status."""
        last_check = obj.check_results.first()
        return last_check.status if last_check else "unknown"


class HealthCheckResultSerializer(serializers.ModelSerializer):
    """Serializer for health check results."""

    endpoint_name = serializers.CharField(source="endpoint.name", read_only=True)
    endpoint_url = serializers.URLField(source="endpoint.url", read_only=True)

    class Meta:
        model = HealthCheckResult
        fields = [
            "id",
            "endpoint",
            "endpoint_name",
            "endpoint_url",
            "check_time",
            "status",
            "response_time_ms",
            "status_code",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SLODefinitionSerializer(serializers.ModelSerializer):
    """Serializer for SLO definitions."""

    metric_count = serializers.SerializerMethodField()
    current_compliance = serializers.SerializerMethodField()

    class Meta:
        model = SLODefinition
        fields = [
            "id",
            "name",
            "service_name",
            "slo_type",
            "target_value",
            "target_unit",
            "measurement_window",
            "error_budget_policy",
            "is_active",
            "metric_count",
            "current_compliance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_metric_count(self, obj: SLODefinition) -> int:
        """Get count of metrics."""
        return obj.metrics.count()

    def get_current_compliance(self, obj: SLODefinition) -> float:
        """Get current compliance percentage."""
        recent_metrics = obj.metrics.order_by("-measurement_time")[:10]
        if not recent_metrics:
            return 0.0
        compliant_count = sum(1 for m in recent_metrics if m.target_met)
        return (compliant_count / len(recent_metrics)) * 100


class SLOMetricSerializer(serializers.ModelSerializer):
    """Serializer for SLO metrics."""

    slo_name = serializers.CharField(source="slo.name", read_only=True)
    service_name = serializers.CharField(source="slo.service_name", read_only=True)

    class Meta:
        model = SLOMetric
        fields = [
            "id",
            "slo",
            "slo_name",
            "service_name",
            "measurement_time",
            "actual_value",
            "target_met",
            "error_budget_remaining",
            "burn_rate",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SelfHealingRuleSerializer(serializers.ModelSerializer):
    """Serializer for self-healing rules."""

    execution_count = serializers.SerializerMethodField()

    class Meta:
        model = SelfHealingRule
        fields = [
            "id",
            "name",
            "description",
            "trigger_type",
            "trigger_config",
            "target_type",
            "target_config",
            "remediation_script",
            "script_type",
            "risk_level",
            "requires_approval",
            "max_executions_per_hour",
            "cooldown_minutes",
            "is_active",
            "execution_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_execution_count(self, obj: SelfHealingRule) -> int:
        """Get count of executions."""
        return obj.executions.count()


class SelfHealingExecutionSerializer(serializers.ModelSerializer):
    """Serializer for self-healing executions."""

    rule_name = serializers.CharField(source="rule.name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.username", read_only=True)

    class Meta:
        model = SelfHealingExecution
        fields = [
            "id",
            "correlation_id",
            "rule",
            "rule_name",
            "trigger_event",
            "status",
            "approved_by",
            "approved_by_name",
            "started_at",
            "completed_at",
            "output",
            "error_message",
            "metrics_before",
            "metrics_after",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
        ]


class RunbookSerializer(serializers.ModelSerializer):
    """Serializer for runbooks."""

    execution_count = serializers.SerializerMethodField()
    step_count = serializers.SerializerMethodField()

    class Meta:
        model = Runbook
        fields = [
            "id",
            "name",
            "description",
            "category",
            "steps",
            "automation_level",
            "risk_level",
            "estimated_duration_minutes",
            "is_active",
            "execution_count",
            "step_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_execution_count(self, obj: Runbook) -> int:
        """Get count of executions."""
        return obj.executions.count()

    def get_step_count(self, obj: Runbook) -> int:
        """Get count of steps."""
        return len(obj.steps) if isinstance(obj.steps, list) else 0


class RunbookExecutionSerializer(serializers.ModelSerializer):
    """Serializer for runbook executions."""

    runbook_name = serializers.CharField(source="runbook.name", read_only=True)
    executed_by_name = serializers.CharField(source="executed_by.username", read_only=True)

    class Meta:
        model = RunbookExecution
        fields = [
            "id",
            "correlation_id",
            "runbook",
            "runbook_name",
            "executed_by",
            "executed_by_name",
            "trigger_reason",
            "status",
            "current_step",
            "step_results",
            "started_at",
            "completed_at",
            "evidence",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at"]
