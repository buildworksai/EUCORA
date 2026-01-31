# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF Permission classes and ViewSet mixins for RBAC.

Provides:
- RBACPermission: Factory function returning DRF permission class
- RBACViewSetMixin: Mixin for automatic permission checking in ViewSets
"""
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from .services import PermissionService


def RBACPermission(resource: str, action: str) -> type:
    """
    Factory function that returns a DRF Permission class for RBAC.

    Usage:
        permission_classes = [RBACPermission('applications', 'read')]

    Args:
        resource: Resource name (e.g., 'applications')
        action: Action name (e.g., 'read')

    Returns:
        Permission class (not instance) for DRF
    """

    class _RBACPermissionClass(BasePermission):
        """Generated permission class for specific resource/action."""

        def has_permission(self, request, view):
            """
            Check if user has permission for this view.

            Args:
                request: DRF request object
                view: DRF view object

            Returns:
                bool: True if user has permission
            """
            # In DEBUG mode, allow unauthenticated access (for demo/testing)
            if settings.DEBUG and not request.user.is_authenticated:
                return True

            if not request.user.is_authenticated:
                return False

            # In DEBUG mode, allow authenticated users (for development/demo)
            # This bypasses RBAC checks but still requires authentication
            if settings.DEBUG:
                return True

            return PermissionService.has_permission(
                user=request.user,
                resource=resource,
                action=action,
                log_access=True,
                request=request,
            )

        def has_object_permission(self, request, view, obj):
            """
            Check object-level permission.

            Args:
                request: DRF request object
                view: DRF view object
                obj: Object instance

            Returns:
                bool: True if user has permission for this object
            """
            # For now, object-level checks use same permission
            # Can be enhanced for resource-specific object checks
            return self.has_permission(request, view)

    # Set a descriptive name for debugging
    _RBACPermissionClass.__name__ = f"RBACPermission_{resource}_{action}"
    _RBACPermissionClass.__qualname__ = _RBACPermissionClass.__name__

    return _RBACPermissionClass


class RBACViewSetMixin:
    """
    Mixin for ViewSets with automatic RBAC permission checking.

    Usage:
        class MyViewSet(RBACViewSetMixin, viewsets.ModelViewSet):
            permission_map = {
                'list': ('applications', 'read'),
                'retrieve': ('applications', 'read'),
                'create': ('applications', 'create'),
                'update': ('applications', 'update'),
                'partial_update': ('applications', 'update'),
                'destroy': ('applications', 'delete'),
            }

            def apply_user_scope(self, queryset):
                # Override to implement resource-specific scoping
                return queryset
    """

    # Define required permissions per action
    # Override in subclass
    permission_map = {}

    def get_permissions(self):
        """
        Return permissions based on action.

        Returns:
            List[BasePermission]: List of permission instances
        """
        action = self.action
        if action in self.permission_map:
            resource, perm_action = self.permission_map[action]
            # RBACPermission returns a class, so instantiate it
            return [RBACPermission(resource, perm_action)()]

        # Fallback to default permissions
        return super().get_permissions()

    def get_queryset(self):
        """
        Filter queryset based on user's scope.

        Returns:
            QuerySet: Filtered queryset
        """
        qs = super().get_queryset()

        # In DEBUG mode, allow unauthenticated access
        if settings.DEBUG and not self.request.user.is_authenticated:
            return qs

        if not self.request.user.is_authenticated:
            return qs.none()

        # Apply user scope filtering
        return self.apply_user_scope(qs)

    def apply_user_scope(self, queryset):
        """
        Override to implement resource-specific scoping.

        Default implementation uses PermissionService.get_accessible_scope().

        Args:
            queryset: Base queryset

        Returns:
            QuerySet: Scoped queryset
        """
        # Get resource from permission_map
        action = self.action
        if action in self.permission_map:
            resource, _ = self.permission_map[action]
            scope_filters = PermissionService.get_accessible_scope(user=self.request.user, resource=resource)

            if scope_filters is None:
                # Platform Admin - return all
                return queryset
            elif scope_filters == queryset.model.objects.none():
                # No access - return empty queryset
                return queryset.none()
            else:
                # Apply scope filters
                return queryset.filter(scope_filters)

        return queryset

    def check_permission(self, resource: str, action: str):
        """
        Helper method to check permission and raise PermissionDenied if denied.

        Args:
            resource: Resource name
            action: Action name

        Raises:
            PermissionDenied: If user doesn't have permission
        """
        if not PermissionService.has_permission(
            user=self.request.user,
            resource=resource,
            action=action,
            log_access=True,
            request=self.request,
        ):
            raise PermissionDenied(detail=f"You do not have {action} permission for {resource}")
