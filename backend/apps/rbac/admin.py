# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Django admin configuration for RBAC.
"""
from django.contrib import admin

from .models import Permission, PermissionAuditLog, Role, UserRole


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Admin for Permission model."""

    list_display = ("resource", "action", "description", "created_at")
    list_filter = ("resource", "action")
    search_fields = ("resource", "action", "description")
    ordering = ("resource", "action")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin for Role model."""

    list_display = ("display_name", "role_type", "is_system", "created_at")
    list_filter = ("is_system", "role_type")
    search_fields = ("display_name", "description")
    filter_horizontal = ("permissions",)
    readonly_fields = ("is_system",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin for UserRole model."""

    list_display = (
        "user",
        "role",
        "portfolio_scope",
        "business_unit_scope",
        "is_active",
        "valid_from",
        "valid_until",
    )
    list_filter = ("is_active", "role", "valid_from", "valid_until")
    search_fields = ("user__username", "user__email", "role__display_name")
    filter_horizontal = ("application_scope",)
    date_hierarchy = "valid_from"
    readonly_fields = ("assigned_by",)


@admin.register(PermissionAuditLog)
class PermissionAuditLogAdmin(admin.ModelAdmin):
    """Admin for PermissionAuditLog model (read-only)."""

    list_display = (
        "action_type",
        "actor",
        "target_user",
        "resource",
        "action",
        "created_at",
    )
    list_filter = ("action_type", "created_at")
    search_fields = ("actor__username", "target_user__username", "resource", "correlation_id")
    date_hierarchy = "created_at"
    readonly_fields = (
        "correlation_id",
        "action_type",
        "actor",
        "target_user",
        "resource",
        "resource_id",
        "action",
        "details",
        "ip_address",
        "user_agent",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        """Audit logs are immutable - cannot be created via admin."""
        return False

    def has_change_permission(self, request, obj=None):
        """Audit logs are immutable - cannot be modified."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Audit logs are immutable - cannot be deleted."""
        return False
