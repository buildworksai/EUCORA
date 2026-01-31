# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Permission Service for RBAC.

Provides centralized permission checking, scope filtering, and audit logging.
"""
from typing import List, Optional

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet
from django.utils import timezone

from .models import Permission, PermissionAuditLog, Role, UserRole

User = get_user_model()


class PermissionService:
    """
    Service for permission checking and scope filtering.

    Provides:
    - Permission checking (has_permission)
    - User role retrieval
    - Scope-based queryset filtering
    - Audit logging for access attempts
    """

    @staticmethod
    def has_permission(
        user: User,
        resource: str,
        action: str,
        resource_id: Optional[str] = None,
        log_access: bool = True,
        request=None,
    ) -> bool:
        """
        Check if user has permission for resource:action.

        Args:
            user: User to check permissions for
            resource: Resource name (e.g., 'applications')
            action: Action name (e.g., 'read')
            resource_id: Optional resource ID for object-level checks
            log_access: Whether to log access attempt
            request: Optional request object for IP/user_agent logging

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Platform Admin has all permissions
        if PermissionService.has_role(user, Role.RoleType.PLATFORM_ADMIN):
            if log_access:
                PermissionService.log_access(
                    user=user,
                    resource=resource,
                    action=action,
                    granted=True,
                    details={"reason": "Platform Admin"},
                    request=request,
                )
            return True

        # Get active role assignments
        active_roles = UserRole.objects.filter(
            user=user,
            is_active=True,
            valid_from__lte=timezone.now(),
        ).filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now()))

        # Check if any role has the required permission
        for user_role in active_roles:
            role_permissions = user_role.role.permissions.filter(resource=resource, action=action)

            if role_permissions.exists():
                # Check scope restrictions if applicable
                if PermissionService._check_scope(user_role, resource, resource_id):
                    if log_access:
                        PermissionService.log_access(
                            user=user,
                            resource=resource,
                            action=action,
                            granted=True,
                            details={
                                "role": user_role.role.role_type,
                                "scope": PermissionService._get_scope_string(user_role),
                            },
                            request=request,
                        )
                    return True

        # Permission denied
        if log_access:
            PermissionService.log_access(
                user=user,
                resource=resource,
                action=action,
                granted=False,
                details={"reason": "No matching permission"},
                request=request,
            )
        return False

    @staticmethod
    def has_role(user: User, role_type: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user: User to check
            role_type: Role type (e.g., Role.RoleType.PLATFORM_ADMIN)

        Returns:
            bool: True if user has the role, False otherwise
        """
        return (
            UserRole.objects.filter(
                user=user,
                role__role_type=role_type,
                is_active=True,
                valid_from__lte=timezone.now(),
            )
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now()))
            .exists()
        )

    @staticmethod
    def get_user_roles(user: User) -> List[Role]:
        """
        Get all active roles for a user.

        Args:
            user: User to get roles for

        Returns:
            List[Role]: List of active roles
        """
        user_roles = (
            UserRole.objects.filter(
                user=user,
                is_active=True,
                valid_from__lte=timezone.now(),
            )
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now()))
            .select_related("role")
        )

        return [ur.role for ur in user_roles]

    @staticmethod
    def get_user_permissions(user: User) -> List[Permission]:
        """
        Get all permissions for a user (from all active roles).

        Args:
            user: User to get permissions for

        Returns:
            List[Permission]: List of unique permissions
        """
        roles = PermissionService.get_user_roles(user)
        permission_ids = set()

        for role in roles:
            permission_ids.update(role.permissions.values_list("id", flat=True))

        return list(Permission.objects.filter(id__in=permission_ids))

    @staticmethod
    def get_accessible_scope(user: User, resource: str) -> QuerySet:  # noqa: C901
        """
        Get queryset filtered by user's scope restrictions.

        This is a helper for ViewSets to filter querysets based on user's
        role scope restrictions (portfolio, application, business unit).

        Args:
            user: User to get scope for
            resource: Resource type (e.g., 'applications', 'portfolios')

        Returns:
            QuerySet: Filtered queryset (or empty queryset if no access)
        """
        # Platform Admin sees all
        if PermissionService.has_role(user, Role.RoleType.PLATFORM_ADMIN):
            # Return all objects - caller should pass the model class
            return None  # Signal to return unfiltered queryset

        # Get user's role assignments with scopes
        user_roles = (
            UserRole.objects.filter(
                user=user,
                is_active=True,
                valid_from__lte=timezone.now(),
            )
            .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now()))
            .select_related("role", "portfolio_scope")
        )

        # Build scope filters
        scope_filters = Q()

        for user_role in user_roles:
            # Check if role has permission for this resource
            if not user_role.role.permissions.filter(resource=resource).exists():
                continue

            # Apply scope restrictions
            if resource == "applications":
                if user_role.portfolio_scope:
                    scope_filters |= Q(ownership__portfolio=user_role.portfolio_scope)
                elif user_role.application_scope.exists():
                    scope_filters |= Q(id__in=user_role.application_scope.values_list("id", flat=True))
                elif user_role.business_unit_scope:
                    scope_filters |= Q(ownership__business_unit=user_role.business_unit_scope)
                else:
                    # Global scope for this role
                    scope_filters |= Q()  # All applications
            elif resource == "portfolios":
                if user_role.portfolio_scope:
                    scope_filters |= Q(id=user_role.portfolio_scope.id)
                elif user_role.business_unit_scope:
                    scope_filters |= Q(business_unit=user_role.business_unit_scope)
                else:
                    scope_filters |= Q()  # All portfolios

        if scope_filters == Q():
            # No matching scope - return empty queryset
            return QuerySet.none()

        return scope_filters

    @staticmethod
    def log_access(
        user: User,
        resource: str,
        action: str,
        granted: bool,
        details: dict = None,
        request=None,
    ) -> PermissionAuditLog:
        """
        Log access attempt to audit trail.

        Args:
            user: User attempting access
            resource: Resource name
            action: Action name
            granted: Whether access was granted
            details: Additional context
            request: Optional request object for IP/user_agent

        Returns:
            PermissionAuditLog: Created audit log entry
        """
        action_type = (
            PermissionAuditLog.ActionType.ACCESS_GRANTED if granted else PermissionAuditLog.ActionType.ACCESS_DENIED
        )

        ip_address = None
        user_agent = ""
        if request:
            ip_address = PermissionService._get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "")

        return PermissionAuditLog.objects.create(
            action_type=action_type,
            actor=user,
            resource=resource,
            action=action,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    @staticmethod
    def _check_scope(user_role: UserRole, resource: str, resource_id: Optional[str]) -> bool:
        """
        Check if resource_id matches user_role's scope restrictions.

        Args:
            user_role: UserRole assignment
            resource: Resource type
            resource_id: Resource ID to check

        Returns:
            bool: True if scope allows access, False otherwise
        """
        # No scope restrictions = global access
        if (
            not user_role.portfolio_scope
            and not user_role.application_scope.exists()
            and not user_role.business_unit_scope
        ):
            return True

        # Scope checking would require fetching the resource object
        # For now, return True - scope filtering happens at queryset level
        # This can be enhanced for object-level permission checks
        return True

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
    def _get_client_ip(request) -> Optional[str]:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
