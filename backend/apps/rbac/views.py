# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API views for RBAC.
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Permission, PermissionAuditLog, Role, UserRole
from .permissions import RBACPermission
from .serializers import (
    CheckPermissionSerializer,
    MyPermissionsSerializer,
    PermissionAuditLogSerializer,
    PermissionSerializer,
    RoleListSerializer,
    RoleSerializer,
    UserRoleCreateSerializer,
    UserRoleSerializer,
)
from .services import PermissionService

User = get_user_model()


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Permission (read-only)."""

    permission_classes = [AllowAny]  # Demo mode: AllowAny for unauthenticated access
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    filterset_fields = ["resource", "action"]
    search_fields = ["resource", "action", "description"]
    ordering_fields = ["resource", "action"]
    ordering = ["resource", "action"]


class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Role (read-only, system roles)."""

    permission_classes = [AllowAny]  # Demo mode: AllowAny for unauthenticated access
    queryset = Role.objects.prefetch_related("permissions").all()
    serializer_class = RoleListSerializer
    lookup_field = "id"

    def get_serializer_class(self):
        """Use detailed serializer for retrieve."""
        if self.action == "retrieve":
            return RoleSerializer
        return RoleListSerializer

    @action(detail=True, methods=["get"])
    def permissions(self, request: Request, pk=None) -> Response:
        """Get permissions for a role."""
        role = self.get_object()
        permissions = role.permissions.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def users(self, request: Request, pk=None) -> Response:
        """Get users with this role."""
        role = self.get_object()
        user_roles = UserRole.objects.filter(role=role, is_active=True).select_related("user")
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)


class UserRoleViewSet(viewsets.ModelViewSet):
    """API viewset for UserRole assignments."""

    permission_classes = [RBACPermission("roles", "read")]  # Require role read permission
    queryset = (
        UserRole.objects.select_related("user", "role", "portfolio_scope", "assigned_by")
        .prefetch_related("application_scope")
        .all()
    )
    serializer_class = UserRoleSerializer
    lookup_field = "id"

    def get_queryset(self):
        """Filter by user if provided."""
        qs = super().get_queryset()
        user_id = self.request.query_params.get("user_id")
        if user_id:
            qs = qs.filter(user_id=user_id)
        return qs.filter(is_active=True)

    def get_serializer_class(self):
        """Use create serializer for POST."""
        if self.action == "create":
            return UserRoleCreateSerializer
        return UserRoleSerializer

    def perform_create(self, serializer):
        """Set assigned_by to current user."""
        serializer.save(
            user_id=self.request.data.get("user_id"),
            assigned_by=self.request.user if self.request.user.is_authenticated else None,
        )


class MyPermissionsView(APIView):
    """API endpoint for current user's permissions."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Get current user's permissions and roles.

        Returns:
            {
                "permissions": [...],
                "roles": [...],
                "is_admin": bool
            }
        """
        user = request.user
        permissions = PermissionService.get_user_permissions(user)
        roles = PermissionService.get_user_roles(user)
        is_admin = PermissionService.has_role(user, Role.RoleType.PLATFORM_ADMIN)

        serializer = MyPermissionsSerializer(
            {
                "permissions": permissions,
                "roles": roles,
                "is_admin": is_admin,
            }
        )
        return Response(serializer.data)


class CheckPermissionView(APIView):
    """API endpoint to check if user has a specific permission."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Check if current user has permission.

        Body: {
            "resource": "applications",
            "action": "read",
            "resource_id": "optional-uuid"
        }

        Returns:
            {
                "has_permission": bool,
                "resource": str,
                "action": str
            }
        """
        serializer = CheckPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        resource = serializer.validated_data["resource"]
        action = serializer.validated_data["action"]
        resource_id = serializer.validated_data.get("resource_id")

        has_permission = PermissionService.has_permission(
            user=request.user,
            resource=resource,
            action=action,
            resource_id=resource_id,
            log_access=True,
            request=request,
        )

        return Response(
            {
                "has_permission": has_permission,
                "resource": resource,
                "action": action,
            }
        )


class PermissionAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for PermissionAuditLog (read-only, immutable)."""

    permission_classes = [RBACPermission("audit_trail", "read")]
    queryset = PermissionAuditLog.objects.select_related("actor", "target_user").all()
    serializer_class = PermissionAuditLogSerializer
    filterset_fields = ["action_type", "actor", "target_user", "resource", "action"]
    search_fields = ["actor__username", "target_user__username", "resource", "correlation_id"]
    ordering_fields = ["created_at", "action_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter by correlation_id if provided."""
        qs = super().get_queryset()
        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            try:
                qs = qs.filter(correlation_id=uuid.UUID(correlation_id))
            except ValueError:
                pass
        return qs


# User-specific role management endpoints
class UserRolesView(APIView):
    """API endpoint for managing a user's roles."""

    permission_classes = [RBACPermission("roles", "read")]

    def get(self, request: Request, user_id: str) -> Response:
        """Get all role assignments for a user."""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user_roles = UserRole.objects.filter(user=user, is_active=True).select_related("role", "portfolio_scope")
        serializer = UserRoleSerializer(user_roles, many=True)
        return Response(serializer.data)

    def post(self, request: Request, user_id: str) -> Response:
        """Assign a role to a user."""
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserRoleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user_role = serializer.save(
                user=user,
                assigned_by=request.user if request.user.is_authenticated else None,
            )

            # Log role assignment
            PermissionAuditLog.objects.create(
                action_type=PermissionAuditLog.ActionType.ROLE_ASSIGNED,
                actor=request.user if request.user.is_authenticated else None,
                target_user=user,
                resource="roles",
                resource_id=str(user_role.id),
                details={
                    "role": user_role.role.role_type,
                    "scope": UserRolesView._get_scope_string(user_role),
                },
                ip_address=UserRolesView._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        return Response(UserRoleSerializer(user_role).data, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, user_id: str, role_id: str) -> Response:
        """Revoke a role from a user."""
        try:
            user = User.objects.get(id=user_id)
            user_role = UserRole.objects.get(user=user, role_id=role_id, is_active=True)
        except (User.DoesNotExist, UserRole.DoesNotExist):
            return Response({"error": "User or role assignment not found"}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            user_role.is_active = False
            user_role.save()

            # Log role revocation
            PermissionAuditLog.objects.create(
                action_type=PermissionAuditLog.ActionType.ROLE_REVOKED,
                actor=request.user if request.user.is_authenticated else None,
                target_user=user,
                resource="roles",
                resource_id=str(user_role.id),
                details={
                    "role": user_role.role.role_type,
                },
                ip_address=UserRolesView._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )

        return Response({"message": "Role revoked"}, status=status.HTTP_200_OK)

    @staticmethod
    def _get_scope_string(user_role: UserRole) -> str:
        """Get human-readable scope string."""
        if user_role.portfolio_scope:
            return f"portfolio:{user_role.portfolio_scope.name}"
        elif user_role.business_unit_scope:
            return f"business_unit:{user_role.business_unit_scope}"
        elif user_role.application_scope.exists():
            app_names = list(user_role.application_scope.values_list("name", flat=True))
            return f"applications:{','.join(app_names[:3])}"  # Limit to 3
        return "global"

    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
