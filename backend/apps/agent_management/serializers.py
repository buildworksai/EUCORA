# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for agent management REST API.
"""
from rest_framework import serializers

from .models import Agent, AgentDeploymentStatus, AgentTask, AgentTelemetry


class AgentRegistrationSerializer(serializers.Serializer):
    """Serializer for agent registration."""

    hostname = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=["windows", "macos", "linux"])
    platform_version = serializers.CharField(max_length=100)
    agent_version = serializers.CharField(max_length=50)
    registration_key = serializers.CharField(max_length=255)
    cpu_cores = serializers.IntegerField(min_value=0)
    memory_mb = serializers.IntegerField(min_value=0)
    disk_gb = serializers.IntegerField(min_value=0)
    ip_address = serializers.IPAddressField()
    mac_address = serializers.CharField(max_length=17)
    tags = serializers.JSONField(required=False, default=dict)


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for agent details."""

    is_online = serializers.ReadOnlyField()

    class Meta:
        model = Agent
        fields = [
            "id",
            "hostname",
            "platform",
            "platform_version",
            "agent_version",
            "status",
            "is_online",
            "last_heartbeat_at",
            "cpu_cores",
            "memory_mb",
            "disk_gb",
            "ip_address",
            "mac_address",
            "tags",
            "metadata",
            "first_seen_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "is_online", "first_seen_at", "created_at", "updated_at"]


class AgentTaskSerializer(serializers.ModelSerializer):
    """Serializer for agent tasks."""

    agent_hostname = serializers.CharField(source="agent.hostname", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)

    class Meta:
        model = AgentTask
        fields = [
            "id",
            "agent",
            "agent_hostname",
            "task_type",
            "status",
            "payload",
            "assigned_at",
            "started_at",
            "completed_at",
            "timeout_seconds",
            "result",
            "error_message",
            "exit_code",
            "correlation_id",
            "created_by",
            "created_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "agent_hostname", "created_by_username", "created_at", "updated_at"]


class AgentTaskCreateSerializer(serializers.Serializer):
    """Serializer for creating agent tasks."""

    agent_id = serializers.UUIDField()
    task_type = serializers.ChoiceField(choices=["DEPLOY", "REMEDIATE", "COLLECT", "UPDATE", "HEALTHCHECK"])
    payload = serializers.JSONField()
    timeout_seconds = serializers.IntegerField(default=3600, min_value=60, max_value=86400)


class AgentTaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status."""

    status = serializers.ChoiceField(choices=["IN_PROGRESS", "COMPLETED", "FAILED", "CANCELLED"])
    result = serializers.JSONField(required=False, allow_null=True)
    error_message = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    exit_code = serializers.IntegerField(required=False, allow_null=True)


class AgentTelemetrySerializer(serializers.ModelSerializer):
    """Serializer for telemetry data."""

    agent_hostname = serializers.CharField(source="agent.hostname", read_only=True)

    class Meta:
        model = AgentTelemetry
        fields = [
            "id",
            "agent",
            "agent_hostname",
            "cpu_usage_percent",
            "memory_usage_percent",
            "disk_usage_percent",
            "network_bytes_sent",
            "network_bytes_received",
            "process_count",
            "installed_software",
            "collected_at",
            "received_at",
            "correlation_id",
        ]
        read_only_fields = ["id", "agent_hostname", "received_at"]


class AgentTelemetrySubmitSerializer(serializers.Serializer):
    """Serializer for submitting telemetry."""

    agent_id = serializers.UUIDField()
    cpu_usage_percent = serializers.FloatField(min_value=0, max_value=100)
    memory_usage_percent = serializers.FloatField(min_value=0, max_value=100)
    disk_usage_percent = serializers.FloatField(min_value=0, max_value=100)
    network_bytes_sent = serializers.IntegerField(default=0, min_value=0)
    network_bytes_received = serializers.IntegerField(default=0, min_value=0)
    process_count = serializers.IntegerField(default=0, min_value=0)
    installed_software = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    collected_at = serializers.DateTimeField(required=False)


class AgentDeploymentStatusSerializer(serializers.ModelSerializer):
    """Serializer for deployment status."""

    agent_hostname = serializers.CharField(source="agent.hostname", read_only=True)

    class Meta:
        model = AgentDeploymentStatus
        fields = [
            "id",
            "agent",
            "agent_hostname",
            "deployment_intent_id",
            "status",
            "progress_percent",
            "started_at",
            "completed_at",
            "error_message",
            "exit_code",
            "package_name",
            "package_version",
            "package_hash",
            "correlation_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "agent_hostname", "created_at", "updated_at"]
