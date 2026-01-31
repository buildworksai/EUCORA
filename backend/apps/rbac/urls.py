# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""URL configuration for RBAC API."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CheckPermissionView,
    MyPermissionsView,
    PermissionAuditLogViewSet,
    PermissionViewSet,
    RoleViewSet,
    UserRolesView,
    UserRoleViewSet,
)

app_name = "rbac"

router = DefaultRouter()
router.register(r"permissions", PermissionViewSet, basename="permission")
router.register(r"roles", RoleViewSet, basename="role")
router.register(r"user-roles", UserRoleViewSet, basename="user-role")
router.register(r"audit-log", PermissionAuditLogViewSet, basename="audit-log")

urlpatterns = [
    path("my-permissions/", MyPermissionsView.as_view(), name="my-permissions"),
    path("check-permission/", CheckPermissionView.as_view(), name="check-permission"),
    path("users/<uuid:user_id>/roles/", UserRolesView.as_view(), name="user-roles"),
    path("users/<uuid:user_id>/roles/<uuid:role_id>/", UserRolesView.as_view(), name="user-role-detail"),
    path("", include(router.urls)),
]
