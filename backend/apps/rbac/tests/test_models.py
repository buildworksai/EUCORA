# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Model tests for RBAC app.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.rbac.models import Permission, PermissionAuditLog, Role, UserRole

User = get_user_model()


@pytest.mark.django_db
class TestPermission:
    """Test Permission model."""

    def test_create_permission(self):
        """Test creating a permission."""
        permission = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
            description="Read applications",
        )
        assert permission.resource == Permission.Resource.APPLICATIONS
        assert permission.action == Permission.Action.READ
        assert str(permission) == "applications:read"

    def test_permission_unique_constraint(self):
        """Test that resource:action pairs are unique."""
        Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
        )
        # Creating duplicate should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError
            Permission.objects.create(
                resource=Permission.Resource.APPLICATIONS,
                action=Permission.Action.READ,
            )


@pytest.mark.django_db
class TestRole:
    """Test Role model."""

    def test_create_role(self):
        """Test creating a role."""
        role = Role.objects.create(
            role_type=Role.RoleType.PLATFORM_ADMIN,
            display_name="Platform Administrator",
            description="Full system access",
        )
        assert role.role_type == Role.RoleType.PLATFORM_ADMIN
        assert role.display_name == "Platform Administrator"
        assert str(role) == "Platform Administrator"

    def test_role_with_permissions(self):
        """Test assigning permissions to a role."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        permission1 = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
        )
        permission2 = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.CREATE,
        )

        role.permissions.add(permission1, permission2)
        assert role.permissions.count() == 2


@pytest.mark.django_db
class TestUserRole:
    """Test UserRole model."""

    def test_create_user_role(self):
        """Test creating a user role assignment."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )

        user_role = UserRole.objects.create(
            user=user,
            role=role,
            is_active=True,
            valid_from=timezone.now(),
        )
        assert user_role.user == user
        assert user_role.role == role
        assert user_role.is_active is True

    def test_user_role_with_scope(self):
        """Test user role with portfolio scope."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        role = Role.objects.create(
            role_type=Role.RoleType.PORTFOLIO_MANAGER,
            display_name="Portfolio Manager",
        )

        user_role = UserRole.objects.create(
            user=user,
            role=role,
            portfolio_scope="portfolio-123",
            is_active=True,
        )
        assert user_role.portfolio_scope == "portfolio-123"

    def test_user_role_with_application_scope(self):
        """Test user role with application scope."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )

        user_role = UserRole.objects.create(
            user=user,
            role=role,
            application_scope=["app-1", "app-2"],
            is_active=True,
        )
        assert len(user_role.application_scope) == 2
        assert "app-1" in user_role.application_scope


@pytest.mark.django_db
class TestPermissionAuditLog:
    """Test PermissionAuditLog model."""

    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        user = User.objects.create_user(username="testuser", email="test@example.com")
        correlation_id = "test-corr-001"

        audit_log = PermissionAuditLog.objects.create(
            correlation_id=correlation_id,
            user=user,
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
            granted=True,
            details={"reason": "Has permission"},
        )
        assert audit_log.user == user
        assert audit_log.resource == Permission.Resource.APPLICATIONS
        assert audit_log.granted is True
        assert audit_log.correlation_id == correlation_id
