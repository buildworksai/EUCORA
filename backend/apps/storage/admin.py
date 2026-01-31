# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin configuration for storage.
"""
from django.contrib import admin

from .models import AWSS3Config, AzureBlobConfig, MinIOConfig, StorageMetrics, StorageProvider


@admin.register(StorageProvider)
class StorageProviderAdmin(admin.ModelAdmin):
    """Admin for StorageProvider model."""

    list_display = (
        "name",
        "provider_type",
        "status",
        "is_primary",
        "is_enabled",
        "priority",
        "last_health_check",
    )
    list_filter = ("provider_type", "status", "is_primary", "is_enabled")
    search_fields = ("name",)
    ordering = ("priority", "name")
    readonly_fields = ("last_health_check", "health_check_error")


@admin.register(MinIOConfig)
class MinIOConfigAdmin(admin.ModelAdmin):
    """Admin for MinIOConfig model."""

    list_display = ("provider", "endpoint_url", "bucket_name", "use_ssl", "region")
    search_fields = ("provider__name", "bucket_name", "endpoint_url")


@admin.register(AWSS3Config)
class AWSS3ConfigAdmin(admin.ModelAdmin):
    """Admin for AWSS3Config model."""

    list_display = ("provider", "bucket_name", "region", "auth_method")
    list_filter = ("auth_method", "region")
    search_fields = ("provider__name", "bucket_name")


@admin.register(AzureBlobConfig)
class AzureBlobConfigAdmin(admin.ModelAdmin):
    """Admin for AzureBlobConfig model."""

    list_display = ("provider", "account_name", "container_name", "auth_method")
    list_filter = ("auth_method",)
    search_fields = ("provider__name", "account_name", "container_name")


@admin.register(StorageMetrics)
class StorageMetricsAdmin(admin.ModelAdmin):
    """Admin for StorageMetrics model (read-only)."""

    list_display = (
        "provider",
        "recorded_at",
        "used_bytes",
        "total_bytes",
        "object_count",
        "uploads",
        "downloads",
    )
    list_filter = ("provider", "recorded_at")
    search_fields = ("provider__name",)
    date_hierarchy = "recorded_at"
    readonly_fields = (
        "provider",
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
    )

    def has_add_permission(self, request):
        """Metrics are created automatically."""
        return False

    def has_change_permission(self, request, obj=None):
        """Metrics are immutable."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Metrics can be deleted for cleanup."""
        return True
