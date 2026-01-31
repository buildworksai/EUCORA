# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for Storage API.
"""
from rest_framework import serializers

from .models import AWSS3Config, AzureBlobConfig, MinIOConfig, StorageMetrics, StorageProvider


class StorageProviderSerializer(serializers.ModelSerializer):
    """Serializer for StorageProvider model."""

    provider_type_label = serializers.CharField(source="get_provider_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    configured_by_username = serializers.CharField(source="configured_by.username", read_only=True)

    class Meta:
        model = StorageProvider
        fields = [
            "id",
            "name",
            "provider_type",
            "provider_type_label",
            "priority",
            "is_primary",
            "is_enabled",
            "status",
            "status_label",
            "last_health_check",
            "health_check_error",
            "configured_by",
            "configured_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "last_health_check",
            "health_check_error",
            "configured_by",
            "created_at",
            "updated_at",
        ]


class MinIOConfigSerializer(serializers.ModelSerializer):
    """Serializer for MinIOConfig model."""

    class Meta:
        model = MinIOConfig
        fields = [
            "endpoint_url",
            "bucket_name",
            "access_key_id",
            "secret_access_key",
            "use_ssl",
            "region",
            "path_style",
        ]
        extra_kwargs = {
            "access_key_id": {"write_only": True},
            "secret_access_key": {"write_only": True},
        }


class AWSS3ConfigSerializer(serializers.ModelSerializer):
    """Serializer for AWSS3Config model."""

    auth_method_label = serializers.CharField(source="get_auth_method_display", read_only=True)

    class Meta:
        model = AWSS3Config
        fields = [
            "bucket_name",
            "region",
            "auth_method",
            "auth_method_label",
            "access_key_id",
            "secret_access_key",
            "role_arn",
            "external_id",
            "endpoint_url",
            "kms_key_id",
        ]
        extra_kwargs = {
            "access_key_id": {"write_only": True, "required": False},
            "secret_access_key": {"write_only": True, "required": False},
            "role_arn": {"required": False},
            "external_id": {"required": False},
            "endpoint_url": {"required": False},
            "kms_key_id": {"required": False},
        }


class AzureBlobConfigSerializer(serializers.ModelSerializer):
    """Serializer for AzureBlobConfig model."""

    auth_method_label = serializers.CharField(source="get_auth_method_display", read_only=True)

    class Meta:
        model = AzureBlobConfig
        fields = [
            "account_name",
            "container_name",
            "auth_method",
            "auth_method_label",
            "connection_string",
            "account_key",
            "sas_token",
            "tenant_id",
            "client_id",
            "client_secret",
        ]
        extra_kwargs = {
            "connection_string": {"write_only": True, "required": False},
            "account_key": {"write_only": True, "required": False},
            "sas_token": {"write_only": True, "required": False},
            "client_secret": {"write_only": True, "required": False},
            "tenant_id": {"required": False},
            "client_id": {"required": False},
        }


class StorageProviderDetailSerializer(StorageProviderSerializer):
    """Detailed serializer with provider-specific config."""

    minio_config = MinIOConfigSerializer(read_only=True)
    s3_config = AWSS3ConfigSerializer(read_only=True)
    azure_config = AzureBlobConfigSerializer(read_only=True)

    class Meta(StorageProviderSerializer.Meta):
        fields = StorageProviderSerializer.Meta.fields + [
            "minio_config",
            "s3_config",
            "azure_config",
        ]


class StorageProviderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating StorageProvider with config."""

    minio_config = MinIOConfigSerializer(required=False)
    s3_config = AWSS3ConfigSerializer(required=False)
    azure_config = AzureBlobConfigSerializer(required=False)

    class Meta:
        model = StorageProvider
        fields = [
            "name",
            "provider_type",
            "priority",
            "is_primary",
            "is_enabled",
            "minio_config",
            "s3_config",
            "azure_config",
        ]

    def create(self, validated_data):
        """Create provider with nested config."""
        minio_config_data = validated_data.pop("minio_config", None)
        s3_config_data = validated_data.pop("s3_config", None)
        azure_config_data = validated_data.pop("azure_config", None)

        provider = StorageProvider.objects.create(**validated_data, configured_by=self.context["request"].user)

        if minio_config_data:
            MinIOConfig.objects.create(provider=provider, **minio_config_data)
        elif s3_config_data:
            AWSS3Config.objects.create(provider=provider, **s3_config_data)
        elif azure_config_data:
            AzureBlobConfig.objects.create(provider=provider, **azure_config_data)

        return provider


class StorageMetricsSerializer(serializers.ModelSerializer):
    """Serializer for StorageMetrics model."""

    provider_name = serializers.CharField(source="provider.name", read_only=True)

    class Meta:
        model = StorageMetrics
        fields = [
            "id",
            "provider",
            "provider_name",
            "recorded_at",
            "total_bytes",
            "used_bytes",
            "object_count",
            "uploads",
            "downloads",
            "deletes",
            "bytes_uploaded",
            "bytes_downloaded",
            "failed_operations",
        ]
        read_only_fields = [
            "id",
            "recorded_at",
        ]


class ConnectionTestResultSerializer(serializers.Serializer):
    """Serializer for connection test results."""

    success = serializers.BooleanField()
    message = serializers.CharField()
    latency_ms = serializers.FloatField(required=False, allow_null=True)
    tests = serializers.ListField(child=serializers.DictField())


class HealthStatusSerializer(serializers.Serializer):
    """Serializer for overall storage health."""

    is_healthy = serializers.BooleanField()
    primary_provider = StorageProviderSerializer(required=False, allow_null=True)
    available_providers = serializers.IntegerField()
    total_providers = serializers.IntegerField()
