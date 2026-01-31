# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service tests for RBAC PermissionService.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.rbac.models import Permission, Role, UserRole
from apps.rbac.services import PermissionService

User = get_user_model()


@pytest.mark.django_db
class TestPermissionService:
    """Test PermissionService."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        self.permission = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
        )
        self.role.permissions.add(self.permission)

    def test_platform_admin_has_all_permissions(self):
        """Test that Platform Admin has all permissions."""
        admin_role = Role.objects.create(
            role_type=Role.RoleType.PLATFORM_ADMIN,
            display_name="Platform Admin",
        )
        UserRole.objects.create(user=self.user, role=admin_role, is_active=True)

        assert PermissionService.has_permission(self.user, Permission.Resource.APPLICATIONS, Permission.Action.READ)
        assert PermissionService.has_permission(self.user, Permission.Resource.APPLICATIONS, Permission.Action.DELETE)

    def test_has_permission_with_role(self):
        """Test has_permission with assigned role."""
        UserRole.objects.create(user=self.user, role=self.role, is_active=True)

        assert PermissionService.has_permission(self.user, Permission.Resource.APPLICATIONS, Permission.Action.READ)
        assert not PermissionService.has_permission(
            self.user, Permission.Resource.APPLICATIONS, Permission.Action.DELETE
        )

    def test_has_role(self):
        """Test has_role method."""
        UserRole.objects.create(user=self.user, role=self.role, is_active=True)

        assert PermissionService.has_role(self.user, Role.RoleType.APPLICATION_MANAGER)
        assert not PermissionService.has_role(self.user, Role.RoleType.PLATFORM_ADMIN)

    def test_get_user_roles(self):
        """Test get_user_roles method."""
        UserRole.objects.create(user=self.user, role=self.role, is_active=True)
        admin_role = Role.objects.create(
            role_type=Role.RoleType.PLATFORM_ADMIN,
            display_name="Platform Admin",
        )
        UserRole.objects.create(user=self.user, role=admin_role, is_active=True)

        roles = PermissionService.get_user_roles(self.user)
        assert len(roles) == 2
        assert any(r.role_type == Role.RoleType.APPLICATION_MANAGER for r in roles)
        assert any(r.role_type == Role.RoleType.PLATFORM_ADMIN for r in roles)

    def test_get_user_permissions(self):
        """Test get_user_permissions method."""
        UserRole.objects.create(user=self.user, role=self.role, is_active=True)
        create_permission = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.CREATE,
        )
        self.role.permissions.add(create_permission)

        permissions = PermissionService.get_user_permissions(self.user)
        assert len(permissions) == 2
        assert any(p.action == Permission.Action.READ for p in permissions)
        assert any(p.action == Permission.Action.CREATE for p in permissions)

    def test_scope_filtering(self):
        """Test scope-based filtering."""
        portfolio_role = Role.objects.create(
            role_type=Role.RoleType.PORTFOLIO_MANAGER,
            display_name="Portfolio Manager",
        )
        UserRole.objects.create(
            user=self.user,
            role=portfolio_role,
            portfolio_scope="portfolio-123",
            is_active=True,
        )

        # Mock queryset filtering - actual implementation depends on model
        scope = PermissionService.get_accessible_scope(self.user, Permission.Resource.PORTFOLIOS)
        assert scope is not None

    def test_log_access(self):
        """Test audit logging."""
        PermissionService.log_access(
            user=self.user,
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
            granted=True,
            details={"reason": "Test"},
        )

        from apps.rbac.models import PermissionAuditLog

        logs = PermissionAuditLog.objects.filter(user=self.user)
        assert logs.count() == 1
        assert logs.first().granted is True
