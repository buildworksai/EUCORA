# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
RBAC models for EUCORA Control Plane.

Implements comprehensive Role-Based Access Control with:
- 9 distinct personas (Platform Admin, Application Manager, etc.)
- Granular resource:action permissions
- Scope-based access restrictions (portfolio/application/business unit)
- Immutable audit trail for all permission changes
"""
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.core.models import CorrelationIdModel, TimeStampedModel

User = get_user_model()


class Permission(TimeStampedModel):
    """Granular permissions for resources and actions."""

    class Resource(models.TextChoices):
        # Platform
        PLATFORM_SETTINGS = "platform_settings", "Platform Settings"
        STORAGE_CONFIG = "storage_config", "Storage Configuration"
        AI_PROVIDERS = "ai_providers", "AI Providers"
        INTEGRATIONS = "integrations", "External Integrations"

        # User Management
        USERS = "users", "User Management"
        ROLES = "roles", "Role Management"

        # Applications
        APPLICATIONS = "applications", "Applications"
        APPLICATION_VERSIONS = "application_versions", "Application Versions"
        ARTIFACTS = "artifacts", "Artifacts"

        # Portfolio
        PORTFOLIOS = "portfolios", "Portfolios"
        PORTFOLIO_METRICS = "portfolio_metrics", "Portfolio Metrics"

        # Packaging
        PACKAGING_REQUESTS = "packaging_requests", "Packaging Requests"
        SBOM = "sbom", "SBOM Data"
        VULNERABILITY_SCANS = "vulnerability_scans", "Vulnerability Scans"

        # Licenses
        LICENSE_INVENTORY = "license_inventory", "License Inventory"
        LICENSE_ASSIGNMENTS = "license_assignments", "License Assignments"
        LICENSE_FORECASTS = "license_forecasts", "License Forecasts"
        VENDORS = "vendors", "Vendor Management"

        # CAB & Approvals
        CAB_REQUESTS = "cab_requests", "CAB Requests"
        EVIDENCE_PACKS = "evidence_packs", "Evidence Packs"
        APPROVAL_DECISIONS = "approval_decisions", "Approval Decisions"

        # Security
        SECURITY_EXCEPTIONS = "security_exceptions", "Security Exceptions"
        VULNERABILITY_POLICY = "vulnerability_policy", "Vulnerability Policy"
        PKI_MANAGEMENT = "pki_management", "PKI Management"

        # Deployments
        DEPLOYMENT_INTENTS = "deployment_intents", "Deployment Intents"
        RING_PROMOTIONS = "ring_promotions", "Ring Promotions"
        ROLLBACKS = "rollbacks", "Rollbacks"

        # Publishing
        PUBLISHING = "publishing", "Publishing Operations"
        EXECUTION_PLANES = "execution_planes", "Execution Planes"

        # Assets & Telemetry
        ASSETS = "assets", "Asset Inventory"
        DEX_DATA = "dex_data", "DEX Telemetry"
        COMPLIANCE_DATA = "compliance_data", "Compliance Data"

        # Audit
        AUDIT_TRAIL = "audit_trail", "Audit Trail"
        EVENT_STORE = "event_store", "Event Store"

        # AI Agents
        AI_AGENTS = "ai_agents", "AI Agents"
        AI_WORKFLOWS = "ai_workflows", "AI Workflows"

        # Policy Documents
        POLICY_DOCUMENTS = "policy_documents", "Policy Documents"

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        READ = "read", "Read"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        EXECUTE = "execute", "Execute"
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        PUBLISH = "publish", "Publish"
        EXPORT = "export", "Export"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    resource = models.CharField(max_length=64, choices=Resource.choices)
    action = models.CharField(max_length=32, choices=Action.choices)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ["resource", "action"]
        ordering = ["resource", "action"]
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return f"{self.resource}:{self.action}"


class Role(TimeStampedModel):
    """System roles with predefined permissions."""

    class RoleType(models.TextChoices):
        PLATFORM_ADMIN = "platform_admin", "Platform Administrator"
        APPLICATION_MANAGER = "application_manager", "Application Manager"
        PORTFOLIO_MANAGER = "portfolio_manager", "Portfolio Manager"
        PACKAGING_ENGINEER = "packaging_engineer", "Packaging Engineer"
        LICENSE_MANAGER = "license_manager", "License Manager"
        CAB_APPROVER = "cab_approver", "CAB Approver"
        SECURITY_REVIEWER = "security_reviewer", "Security Reviewer"
        PUBLISHER = "publisher", "Publisher"
        AUDITOR = "auditor", "Auditor"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    role_type = models.CharField(max_length=32, choices=RoleType.choices, unique=True)
    display_name = models.CharField(max_length=128)
    description = models.TextField()
    is_system = models.BooleanField(default=True, help_text="System roles cannot be deleted")

    # Hierarchical permissions
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)

    class Meta:
        ordering = ["display_name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.display_name


class UserRole(TimeStampedModel):
    """User-to-role assignments with optional scope restrictions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_assignments")

    # Scope restrictions (null = global)
    portfolio_scope = models.ForeignKey(
        "portfolio_management.Portfolio",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="role_assignments",
        help_text="Restrict to this portfolio (null = all portfolios)",
    )
    application_scope = models.ManyToManyField(
        "application_portfolio.Application",
        blank=True,
        related_name="role_assignments",
        help_text="Restrict to these applications (empty = all applications)",
    )
    business_unit_scope = models.CharField(
        max_length=128,
        blank=True,
        help_text="Restrict to this business unit (empty = all)",
    )

    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Audit
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="role_assignments_made",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["role", "is_active"]),
        ]
        verbose_name = "User Role Assignment"
        verbose_name_plural = "User Role Assignments"

    def __str__(self):
        scope_str = ""
        if self.portfolio_scope:
            scope_str = f" (Portfolio: {self.portfolio_scope.name})"
        elif self.business_unit_scope:
            scope_str = f" (BU: {self.business_unit_scope})"
        return f"{self.user.username} - {self.role.display_name}{scope_str}"


class PermissionAuditLog(TimeStampedModel, CorrelationIdModel):
    """Immutable audit log for permission changes."""

    class ActionType(models.TextChoices):
        ROLE_ASSIGNED = "role_assigned", "Role Assigned"
        ROLE_REVOKED = "role_revoked", "Role Revoked"
        SCOPE_MODIFIED = "scope_modified", "Scope Modified"
        PERMISSION_GRANTED = "permission_granted", "Permission Granted"
        PERMISSION_REVOKED = "permission_revoked", "Permission Revoked"
        ACCESS_DENIED = "access_denied", "Access Denied"
        ACCESS_GRANTED = "access_granted", "Access Granted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    action_type = models.CharField(max_length=32, choices=ActionType.choices)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    resource = models.CharField(max_length=64, blank=True)
    resource_id = models.CharField(max_length=128, blank=True)
    action = models.CharField(max_length=32, blank=True)

    details = models.JSONField(default=dict, help_text="Additional context")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["target_user", "created_at"]),
            models.Index(fields=["action_type", "created_at"]),
            models.Index(fields=["correlation_id"]),
        ]
        verbose_name = "Permission Audit Log"
        verbose_name_plural = "Permission Audit Logs"

    def __str__(self):
        return f"{self.action_type} - {self.created_at}"
