# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for RBAC API.
"""
from rest_framework import serializers

from .models import Permission, PermissionAuditLog, Role, UserRole


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model."""

    resource_label = serializers.CharField(source="get_resource_display", read_only=True)
    action_label = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = Permission
        fields = [
            "id",
            "resource",
            "resource_label",
            "action",
            "action_label",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RoleListSerializer(serializers.ModelSerializer):
    """Compact serializer for role lists."""

    permission_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = [
            "id",
            "role_type",
            "display_name",
            "description",
            "is_system",
            "permission_count",
        ]

    def get_permission_count(self, obj: Role) -> int:
        """Get count of permissions for this role."""
        return obj.permissions.count()


class RoleSerializer(serializers.ModelSerializer):
    """Detailed serializer for Role model."""

    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        source="permissions",
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = [
            "id",
            "role_type",
            "display_name",
            "description",
            "is_system",
            "permissions",
            "permission_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model."""

    role = RoleListSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source="role",
        write_only=True,
    )
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    portfolio_name = serializers.CharField(source="portfolio_scope.name", read_only=True)
    application_names = serializers.SerializerMethodField()
    assigned_by_username = serializers.CharField(source="assigned_by.username", read_only=True)

    class Meta:
        model = UserRole
        fields = [
            "id",
            "user",
            "user_username",
            "user_email",
            "role",
            "role_id",
            "portfolio_scope",
            "portfolio_name",
            "application_scope",
            "application_names",
            "business_unit_scope",
            "is_active",
            "valid_from",
            "valid_until",
            "assigned_by",
            "assigned_by_username",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assigned_by",
            "created_at",
            "updated_at",
        ]

    def get_application_names(self, obj: UserRole) -> list:
        """Get list of application names."""
        return list(obj.application_scope.values_list("name", flat=True))


class UserRoleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating UserRole assignments."""

    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source="role",
    )

    class Meta:
        model = UserRole
        fields = [
            "role_id",
            "portfolio_scope",
            "application_scope",
            "business_unit_scope",
            "valid_from",
            "valid_until",
        ]


class PermissionAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for PermissionAuditLog model (read-only)."""

    action_type_label = serializers.CharField(source="get_action_type_display", read_only=True)
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    target_user_username = serializers.CharField(source="target_user.username", read_only=True)

    class Meta:
        model = PermissionAuditLog
        fields = [
            "id",
            "correlation_id",
            "action_type",
            "action_type_label",
            "actor",
            "actor_username",
            "target_user",
            "target_user_username",
            "resource",
            "resource_id",
            "action",
            "details",
            "ip_address",
            "user_agent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
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
        ]


class CheckPermissionSerializer(serializers.Serializer):
    """Serializer for permission check request."""

    resource = serializers.ChoiceField(choices=Permission.Resource.choices)
    action = serializers.ChoiceField(choices=Permission.Action.choices)
    resource_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class MyPermissionsSerializer(serializers.Serializer):
    """Serializer for current user's permissions."""

    permissions = PermissionSerializer(many=True)
    roles = RoleListSerializer(many=True)
    is_admin = serializers.BooleanField()
