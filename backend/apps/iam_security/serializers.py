# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for IAM Security API.
"""
from rest_framework import serializers

from .models import AnomalyDetection, DetectionRule, IdentityProvider, PermissionChange, SecurityAlert, SignInEvent


class IdentityProviderSerializer(serializers.ModelSerializer):
    """Serializer for identity providers."""

    sign_in_count = serializers.SerializerMethodField()
    anomaly_count = serializers.SerializerMethodField()

    class Meta:
        model = IdentityProvider
        fields = [
            "id",
            "name",
            "provider_type",
            "tenant_id",
            "connection_config",
            "sync_interval_minutes",
            "last_sync",
            "is_active",
            "sign_in_count",
            "anomaly_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_sync", "created_at", "updated_at"]

    def get_sign_in_count(self, obj: IdentityProvider) -> int:
        """Get count of sign-in events."""
        return obj.sign_in_events.count()

    def get_anomaly_count(self, obj: IdentityProvider) -> int:
        """Get count of active anomalies."""
        return obj.anomalies.filter(status=AnomalyDetection.Status.NEW).count()

    def to_representation(self, instance: IdentityProvider) -> dict:
        """Mask sensitive connection config."""
        data = super().to_representation(instance)
        if data.get("connection_config"):
            for key in ["client_secret", "password", "api_key", "token"]:
                if key in data["connection_config"]:
                    data["connection_config"][key] = "***"
        return data


class SignInEventSerializer(serializers.ModelSerializer):
    """Serializer for sign-in events."""

    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = SignInEvent
        fields = [
            "id",
            "provider",
            "provider_name",
            "event_id",
            "user_principal",
            "user_display_name",
            "app_display_name",
            "client_ip",
            "location",
            "device_detail",
            "status",
            "failure_reason",
            "risk_level",
            "event_time",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PermissionChangeSerializer(serializers.ModelSerializer):
    """Serializer for permission changes."""

    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = PermissionChange
        fields = [
            "id",
            "provider",
            "provider_name",
            "event_id",
            "actor_principal",
            "target_principal",
            "change_type",
            "resource_type",
            "resource_name",
            "old_value",
            "new_value",
            "event_time",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AnomalyDetectionSerializer(serializers.ModelSerializer):
    """Serializer for anomaly detections."""

    provider_name = serializers.CharField(source="provider.name", read_only=True)
    assigned_to_username = serializers.CharField(source="assigned_to.username", read_only=True)
    alert_count = serializers.SerializerMethodField()

    class Meta:
        model = AnomalyDetection
        fields = [
            "id",
            "correlation_id",
            "provider",
            "provider_name",
            "anomaly_type",
            "severity",
            "user_principal",
            "description",
            "evidence",
            "related_events",
            "detection_rule",
            "status",
            "assigned_to",
            "assigned_to_username",
            "resolved_at",
            "resolution_notes",
            "alert_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "resolved_at",
            "created_at",
            "updated_at",
        ]

    def get_alert_count(self, obj: AnomalyDetection) -> int:
        """Get count of alerts for this anomaly."""
        return obj.alerts.count()


class DetectionRuleSerializer(serializers.ModelSerializer):
    """Serializer for detection rules."""

    class Meta:
        model = DetectionRule
        fields = [
            "id",
            "name",
            "description",
            "anomaly_type",
            "severity",
            "rule_config",
            "threshold_config",
            "is_active",
            "last_triggered",
            "trigger_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_triggered", "trigger_count", "created_at", "updated_at"]


class SecurityAlertSerializer(serializers.ModelSerializer):
    """Serializer for security alerts."""

    anomaly_description = serializers.CharField(source="anomaly.description", read_only=True)

    class Meta:
        model = SecurityAlert
        fields = [
            "id",
            "correlation_id",
            "anomaly",
            "anomaly_description",
            "channel",
            "recipients",
            "subject",
            "body",
            "sent_at",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "sent_at", "created_at"]


class AnomalyResolveSerializer(serializers.Serializer):
    """Serializer for resolving an anomaly."""

    resolution_notes = serializers.CharField(required=False, allow_blank=True)
    is_false_positive = serializers.BooleanField(default=False)
