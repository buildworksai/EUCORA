# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Management command to seed RBAC roles and permissions.

Creates:
- All Permission objects (resource:action pairs)
- 9 system roles with their permission sets
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rbac.models import Permission, Role


class Command(BaseCommand):
    help = "Seed RBAC roles and permissions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-existing",
            action="store_true",
            help="Clear existing roles and permissions before seeding",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("EUCORA RBAC Data Seeder"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

        with transaction.atomic():
            if options["clear_existing"]:
                self.stdout.write(self.style.WARNING("Clearing existing RBAC data..."))
                Permission.objects.all().delete()
                Role.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("✓ Cleared existing data"))

            # Step 1: Create all permissions
            self.stdout.write("\n" + self.style.WARNING("[1/2] Creating Permissions..."))
            permissions_created = self._create_permissions()
            self.stdout.write(self.style.SUCCESS(f"✓ Created {permissions_created} permissions"))

            # Step 2: Create roles with permission assignments
            self.stdout.write("\n" + self.style.WARNING("[2/2] Creating Roles..."))
            roles_created = self._create_roles()
            self.stdout.write(self.style.SUCCESS(f"✓ Created {roles_created} roles"))

        self.stdout.write("\n" + self.style.SUCCESS("=" * 70))
        self.stdout.write(self.style.SUCCESS("✓ RBAC data seeding completed"))
        self.stdout.write(self.style.SUCCESS("=" * 70))

    def _create_permissions(self) -> int:
        """Create all Permission objects."""
        permissions_to_create = []

        # All resources
        resources = [choice[0] for choice in Permission.Resource.choices]
        actions = [choice[0] for choice in Permission.Action.choices]

        for resource in resources:
            for action in actions:
                # Skip invalid combinations (e.g., approve/reject on non-CAB resources)
                if not self._is_valid_permission(resource, action):
                    continue

                # Get labels for description
                resource_label = dict(Permission.Resource.choices).get(resource, resource)
                action_label = dict(Permission.Action.choices).get(action, action)

                permission, created = Permission.objects.get_or_create(
                    resource=resource,
                    action=action,
                    defaults={"description": f"{resource_label}: {action_label}"},
                )
                if created:
                    permissions_to_create.append(permission)

        return len(permissions_to_create)

    def _is_valid_permission(self, resource: str, action: str) -> bool:
        """Check if resource:action combination is valid."""
        # Approve/reject only for CAB-related resources
        if action in ["approve", "reject"]:
            return resource in [
                "cab_requests",
                "security_exceptions",
                "approval_decisions",
            ]

        # Publish only for publishing resources
        if action == "publish":
            return resource in ["publishing", "artifacts"]

        # Export only for audit/reporting resources
        if action == "export":
            return resource in [
                "audit_trail",
                "event_store",
                "portfolio_metrics",
                "compliance_data",
            ]

        # All other combinations are valid
        return True

    def _create_roles(self) -> int:
        """Create all roles with their permission assignments."""
        roles_created = 0

        # Platform Admin - Full access to all resources
        platform_admin = self._create_role(  # noqa: F841
            role_type=Role.RoleType.PLATFORM_ADMIN,
            display_name="Platform Administrator",
            description="Full system access - can configure platform, manage users, and access all resources",
            permissions=self._get_platform_admin_permissions(),
        )
        roles_created += 1

        # Application Manager
        app_manager = self._create_role(  # noqa: F841
            role_type=Role.RoleType.APPLICATION_MANAGER,
            display_name="Application Manager",
            description="Manages owned applications, creates packaging requests, initiates deployments",
            permissions=self._get_application_manager_permissions(),
        )
        roles_created += 1

        # Portfolio Manager
        portfolio_manager = self._create_role(  # noqa: F841
            role_type=Role.RoleType.PORTFOLIO_MANAGER,
            display_name="Portfolio Manager",
            description="Oversees portfolio applications, monitors metrics, manages team",
            permissions=self._get_portfolio_manager_permissions(),
        )
        roles_created += 1

        # Packaging Engineer
        packaging_engineer = self._create_role(  # noqa: F841
            role_type=Role.RoleType.PACKAGING_ENGINEER,
            display_name="Packaging Engineer",
            description="Creates artifacts, generates SBOM, handles packaging requests",
            permissions=self._get_packaging_engineer_permissions(),
        )
        roles_created += 1

        # License Manager
        license_manager = self._create_role(  # noqa: F841
            role_type=Role.RoleType.LICENSE_MANAGER,
            display_name="License Manager",
            description="Manages license inventory, assignments, forecasts, and vendors",
            permissions=self._get_license_manager_permissions(),
        )
        roles_created += 1

        # CAB Approver
        cab_approver = self._create_role(  # noqa: F841
            role_type=Role.RoleType.CAB_APPROVER,
            display_name="CAB Approver",
            description="Reviews and approves/rejects CAB requests, reviews evidence packs",
            permissions=self._get_cab_approver_permissions(),
        )
        roles_created += 1

        # Security Reviewer
        security_reviewer = self._create_role(  # noqa: F841
            role_type=Role.RoleType.SECURITY_REVIEWER,
            display_name="Security Reviewer",
            description="Manages security exceptions, vulnerability policies, PKI",
            permissions=self._get_security_reviewer_permissions(),
        )
        roles_created += 1

        # Publisher
        publisher = self._create_role(  # noqa: F841
            role_type=Role.RoleType.PUBLISHER,
            display_name="Publisher",
            description="Publishes approved artifacts to execution planes, manages rollbacks",
            permissions=self._get_publisher_permissions(),
        )
        roles_created += 1

        # Auditor
        auditor = self._create_role(  # noqa: F841
            role_type=Role.RoleType.AUDITOR,
            display_name="Auditor",
            description="Read-only access to all audit trails, evidence packs, and compliance data",
            permissions=self._get_auditor_permissions(),
        )
        roles_created += 1

        return roles_created

    def _create_role(self, role_type: str, display_name: str, description: str, permissions: list) -> Role:
        """Create a role with permission assignments."""
        role, created = Role.objects.get_or_create(
            role_type=role_type,
            defaults={
                "display_name": display_name,
                "description": description,
                "is_system": True,
            },
        )

        if not created:
            # Update display name and description if changed
            role.display_name = display_name
            role.description = description
            role.save()

        # Assign permissions
        permission_objects = Permission.objects.filter(
            resource__in=[p[0] for p in permissions],
            action__in=[a for perm in permissions for a in perm[1]],
        )

        # Filter to exact matches
        assigned_permissions = []
        for perm_obj in permission_objects:
            for resource, actions in permissions:
                if perm_obj.resource == resource and perm_obj.action in actions:
                    assigned_permissions.append(perm_obj)
                    break

        role.permissions.set(assigned_permissions)
        self.stdout.write(f"  - {display_name}: {len(assigned_permissions)} permissions")

        return role

    def _get_platform_admin_permissions(self) -> list:
        """Get permissions for Platform Admin (all resources, all actions)."""
        # Platform Admin gets all permissions
        resources = [choice[0] for choice in Permission.Resource.choices]
        actions = ["create", "read", "update", "delete", "execute", "approve", "reject", "publish", "export"]

        permissions = []
        for resource in resources:
            valid_actions = [a for a in actions if self._is_valid_permission(resource, a)]
            if valid_actions:
                permissions.append((resource, valid_actions))

        return permissions

    def _get_application_manager_permissions(self) -> list:
        """Get permissions for Application Manager."""
        return [
            ("applications", ["read", "update"]),
            ("application_versions", ["read"]),
            ("artifacts", ["read"]),
            ("packaging_requests", ["create", "read", "update"]),
            ("deployment_intents", ["create", "read", "update"]),
            ("cab_requests", ["create", "read"]),
            ("assets", ["read"]),
            ("dex_data", ["read"]),
            ("compliance_data", ["read"]),
            ("license_assignments", ["read"]),
        ]

    def _get_portfolio_manager_permissions(self) -> list:
        """Get permissions for Portfolio Manager."""
        return [
            ("portfolios", ["read", "update"]),
            ("portfolio_metrics", ["read", "export"]),
            ("applications", ["read"]),
            ("deployment_intents", ["read"]),
            ("license_inventory", ["read"]),
            ("license_assignments", ["read"]),
            ("license_forecasts", ["read"]),
            ("compliance_data", ["read", "export"]),
            ("dex_data", ["read"]),
        ]

    def _get_packaging_engineer_permissions(self) -> list:
        """Get permissions for Packaging Engineer."""
        return [
            ("packaging_requests", ["read", "update"]),
            ("artifacts", ["create", "read", "update"]),
            ("sbom", ["create", "read"]),
            ("vulnerability_scans", ["read"]),
            ("evidence_packs", ["create", "read"]),
            ("applications", ["read"]),
            ("application_versions", ["read"]),
        ]

    def _get_license_manager_permissions(self) -> list:
        """Get permissions for License Manager."""
        return [
            ("license_inventory", ["create", "read", "update", "delete"]),
            ("license_assignments", ["create", "read", "update", "delete"]),
            ("license_forecasts", ["create", "read", "update"]),
            ("vendors", ["create", "read", "update", "delete"]),
            ("applications", ["read"]),
            ("assets", ["read"]),
            ("audit_trail", ["read"]),
        ]

    def _get_cab_approver_permissions(self) -> list:
        """Get permissions for CAB Approver."""
        return [
            ("cab_requests", ["read", "approve", "reject"]),
            ("evidence_packs", ["read"]),
            ("approval_decisions", ["create", "read"]),
            ("applications", ["read"]),
            ("artifacts", ["read"]),
            ("deployment_intents", ["read"]),
            ("vulnerability_scans", ["read"]),
        ]

    def _get_security_reviewer_permissions(self) -> list:
        """Get permissions for Security Reviewer."""
        return [
            ("security_exceptions", ["create", "read", "update", "approve", "reject"]),
            ("vulnerability_policy", ["create", "read", "update"]),
            ("pki_management", ["create", "read", "update"]),
            ("vulnerability_scans", ["read"]),
            ("sbom", ["read"]),
            ("audit_trail", ["read"]),
            ("event_store", ["read"]),
        ]

    def _get_publisher_permissions(self) -> list:
        """Get permissions for Publisher."""
        return [
            ("publishing", ["execute"]),
            ("execution_planes", ["read", "execute"]),
            ("artifacts", ["read"]),
            ("deployment_intents", ["read"]),
            ("ring_promotions", ["read", "execute"]),
            ("rollbacks", ["execute"]),
            ("audit_trail", ["read"]),
        ]

    def _get_auditor_permissions(self) -> list:
        """Get permissions for Auditor."""
        return [
            ("audit_trail", ["read", "export"]),
            ("event_store", ["read", "export"]),
            ("evidence_packs", ["read"]),
            ("approval_decisions", ["read"]),
            ("cab_requests", ["read"]),
            ("deployment_intents", ["read"]),
            ("applications", ["read"]),
            ("assets", ["read"]),
            ("vulnerability_scans", ["read"]),
            ("license_inventory", ["read"]),
        ]
