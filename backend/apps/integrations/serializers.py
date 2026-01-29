# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for integration models.
"""
from rest_framework import serializers

from apps.integrations.models import ExternalSystem, IntegrationSyncLog


class ExternalSystemSerializer(serializers.ModelSerializer):
    """Serializer for ExternalSystem model."""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    auth_type_display = serializers.CharField(source="get_auth_type_display", read_only=True)
    last_sync_status_display = serializers.CharField(source="get_last_sync_status_display", read_only=True)

    class Meta:
        model = ExternalSystem
        fields = [
            "id",
            "correlation_id",
            "name",
            "type",
            "type_display",
            "is_enabled",
            "api_url",
            "auth_type",
            "auth_type_display",
            "credentials",  # In production, this should be masked
            "sync_interval_minutes",
            "last_sync_at",
            "last_sync_status",
            "last_sync_status_display",
            "metadata",
            "is_demo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "last_sync_at",
            "last_sync_status",
            "created_at",
            "updated_at",
        ]


class ExternalSystemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating ExternalSystem (with credential validation)."""

    class Meta:
        model = ExternalSystem
        fields = [
            "name",
            "type",
            "is_enabled",
            "api_url",
            "auth_type",
            "credentials",
            "sync_interval_minutes",
            "metadata",
        ]

    def validate_credentials(self, value):
        """Validate credentials structure based on auth_type."""
        auth_type = self.initial_data.get("auth_type")

        if auth_type == ExternalSystem.AuthType.OAUTH2:
            required_fields = ["client_id", "client_secret", "tenant_id"]
        elif auth_type == ExternalSystem.AuthType.BASIC:
            required_fields = ["username", "password"]
        elif auth_type == ExternalSystem.AuthType.TOKEN:
            required_fields = ["api_token"]
        elif auth_type == ExternalSystem.AuthType.CERTIFICATE:
            required_fields = ["certificate_path", "key_path"]
        elif auth_type == ExternalSystem.AuthType.SERVER_TOKEN:
            required_fields = ["server_token"]
        else:
            raise serializers.ValidationError(f"Unsupported auth_type: {auth_type}")

        missing_fields = [field for field in required_fields if field not in value]
        if missing_fields:
            raise serializers.ValidationError(
                f'Missing required credential fields for {auth_type}: {", ".join(missing_fields)}'
            )

        return value


class IntegrationSyncLogSerializer(serializers.ModelSerializer):
    """Serializer for IntegrationSyncLog model."""

    system_name = serializers.CharField(source="system.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = IntegrationSyncLog
        fields = [
            "id",
            "correlation_id",
            "system",
            "system_name",
            "sync_started_at",
            "sync_completed_at",
            "status",
            "status_display",
            "records_fetched",
            "records_created",
            "records_updated",
            "records_failed",
            "error_message",
            "error_details",
            "duration_seconds",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "sync_started_at",
            "sync_completed_at",
            "status",
            "records_fetched",
            "records_created",
            "records_updated",
            "records_failed",
            "error_message",
            "error_details",
            "duration_seconds",
            "created_at",
        ]
