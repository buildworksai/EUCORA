# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for RBAC endpoints.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.rbac.models import Permission, Role, UserRole

User = get_user_model()


@pytest.mark.django_db
class TestRBACAPI:
    """Test RBAC API endpoints."""

    @pytest.fixture
    def api_client(self):
        """Create API client."""
        return APIClient()

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username="testuser", email="test@example.com", password="testpass")

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Create authenticated API client."""
        api_client.force_authenticate(user=user)
        return api_client

    def test_list_roles(self, authenticated_client):
        """Test GET /api/v1/rbac/roles/."""
        role = Role.objects.create(  # noqa: F841
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        response = authenticated_client.get("/api/v1/rbac/roles/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_retrieve_role(self, authenticated_client):
        """Test GET /api/v1/rbac/roles/{id}/."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        response = authenticated_client.get(f"/api/v1/rbac/roles/{role.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["role_type"] == Role.RoleType.APPLICATION_MANAGER

    def test_list_permissions(self, authenticated_client):
        """Test GET /api/v1/rbac/permissions/."""
        Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
        )
        response = authenticated_client.get("/api/v1/rbac/permissions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 1

    def test_my_permissions(self, authenticated_client, user):
        """Test GET /api/v1/rbac/my-permissions/."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        permission = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
        )
        role.permissions.add(permission)
        UserRole.objects.create(user=user, role=role, is_active=True)

        response = authenticated_client.get("/api/v1/rbac/my-permissions/")
        assert response.status_code == status.HTTP_200_OK
        assert "permissions" in response.data

    def test_check_permission(self, authenticated_client, user):
        """Test POST /api/v1/rbac/check-permission/."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        permission = Permission.objects.create(
            resource=Permission.Resource.APPLICATIONS,
            action=Permission.Action.READ,
        )
        role.permissions.add(permission)
        UserRole.objects.create(user=user, role=role, is_active=True)

        response = authenticated_client.post(
            "/api/v1/rbac/check-permission/",
            {"resource": Permission.Resource.APPLICATIONS, "action": Permission.Action.READ},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["has_permission"] is True

    def test_list_user_roles(self, authenticated_client, user):
        """Test GET /api/v1/rbac/users/{id}/roles/."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        UserRole.objects.create(user=user, role=role, is_active=True)

        response = authenticated_client.get(f"/api/v1/rbac/users/{user.id}/roles/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_assign_role(self, authenticated_client, user):
        """Test POST /api/v1/rbac/users/{id}/roles/."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )

        response = authenticated_client.post(
            f"/api/v1/rbac/users/{user.id}/roles/",
            {"role": role.id, "is_active": True},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert UserRole.objects.filter(user=user, role=role).exists()

    def test_revoke_role(self, authenticated_client, user):
        """Test DELETE /api/v1/rbac/users/{id}/roles/{role_id}/."""
        role = Role.objects.create(
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
        )
        user_role = UserRole.objects.create(user=user, role=role, is_active=True)

        response = authenticated_client.delete(f"/api/v1/rbac/users/{user.id}/roles/{user_role.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserRole.objects.filter(id=user_role.id, is_active=True).exists()

    def test_audit_log_list(self, authenticated_client):
        """Test GET /api/v1/rbac/audit-log/."""
        response = authenticated_client.get("/api/v1/rbac/audit-log/")
        assert response.status_code == status.HTTP_200_OK
