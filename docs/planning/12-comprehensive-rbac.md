# E3: Comprehensive RBAC — 9-Persona Role-Based Access Control

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P0-Blocker
**Dependencies**: None

---

## Overview

Implement a comprehensive Role-Based Access Control (RBAC) system with 9 distinct personas, strict operation isolation, and immutable audit trail. This is a **P0-Blocker** as all other enhancements depend on proper access control.

---

## Persona Matrix

| Persona | Scope | Primary Functions | Data Access |
|---------|-------|-------------------|-------------|
| **Platform Admin** | Global | Platform configuration, integrations, all settings | Full system access |
| **Application Manager** | Owned Apps | Application lifecycle, deployment requests, health monitoring | Own applications + portfolio |
| **Portfolio Manager** | Managed Portfolio | Team oversight, cost analysis, license optimization | Portfolio applications + team metrics |
| **Packaging Engineer** | Assigned Requests | Artifact creation, SBOM, signing, test documentation | Packaging requests assigned |
| **License Manager** | License Domain | License inventory, assignments, true-up, vendor management | All license data |
| **CAB Approver** | CAB Scope | Approval decisions, evidence review, conditions | CAB queue + evidence packs |
| **Security Reviewer** | Security Domain | Exception approval, vulnerability policy, PKI | Security policies + exceptions |
| **Publisher** | Publishing Scope | Publish approved artifacts to execution planes | Approved artifacts only |
| **Auditor** | Audit Domain | Read-only access to all audit trails and evidence | Immutable read-only |

---

## Data Model

### Backend Models (Django)

```python
# backend/apps/rbac/models.py

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
    is_system = models.BooleanField(default=True)  # Cannot be deleted

    # Hierarchical permissions
    permissions = models.ManyToManyField('Permission', related_name='roles')

    class Meta:
        ordering = ['display_name']


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
        unique_together = ['resource', 'action']
        ordering = ['resource', 'action']

    def __str__(self):
        return f"{self.resource}:{self.action}"


class UserRole(TimeStampedModel):
    """User-to-role assignments with optional scope restrictions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_assignments')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_assignments')

    # Scope restrictions (null = global)
    portfolio_scope = models.ForeignKey(
        'portfolio_management.Portfolio',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='role_assignments',
        help_text="Restrict to this portfolio (null = all portfolios)"
    )
    application_scope = models.ManyToManyField(
        'application_portfolio.Application',
        blank=True,
        related_name='role_assignments',
        help_text="Restrict to these applications (empty = all applications)"
    )
    business_unit_scope = models.CharField(
        max_length=128, blank=True,
        help_text="Restrict to this business unit (empty = all)"
    )

    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)

    # Audit
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='role_assignments_made'
    )

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['role', 'is_active']),
        ]


class PermissionAuditLog(TimeStampedModel):
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
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)

    action_type = models.CharField(max_length=32, choices=ActionType.choices)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='+')

    resource = models.CharField(max_length=64, blank=True)
    resource_id = models.CharField(max_length=128, blank=True)
    action = models.CharField(max_length=32, blank=True)

    details = models.JSONField(default=dict)  # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['target_user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
        ]
```

---

## Role Permission Matrix

### Platform Admin
```python
PLATFORM_ADMIN_PERMISSIONS = [
    # Full access to all resources
    ("platform_settings", ["create", "read", "update", "delete"]),
    ("storage_config", ["create", "read", "update", "delete"]),
    ("ai_providers", ["create", "read", "update", "delete"]),
    ("integrations", ["create", "read", "update", "delete"]),
    ("users", ["create", "read", "update", "delete"]),
    ("roles", ["create", "read", "update", "delete"]),
    ("applications", ["create", "read", "update", "delete"]),
    ("portfolios", ["create", "read", "update", "delete"]),
    ("policy_documents", ["create", "read", "update", "delete"]),
    ("audit_trail", ["read", "export"]),
    # ... all other resources
]
```

### Application Manager
```python
APPLICATION_MANAGER_PERMISSIONS = [
    # Applications (scoped to owned applications)
    ("applications", ["read", "update"]),  # Cannot create/delete
    ("application_versions", ["read"]),
    ("artifacts", ["read"]),

    # Packaging requests
    ("packaging_requests", ["create", "read", "update"]),

    # Deployment (initiate, not publish)
    ("deployment_intents", ["create", "read", "update"]),
    ("cab_requests", ["create", "read"]),

    # Monitoring
    ("assets", ["read"]),
    ("dex_data", ["read"]),
    ("compliance_data", ["read"]),

    # License (view own applications)
    ("license_assignments", ["read"]),
]
```

### Portfolio Manager
```python
PORTFOLIO_MANAGER_PERMISSIONS = [
    # Portfolio management
    ("portfolios", ["read", "update"]),
    ("portfolio_metrics", ["read", "export"]),

    # Team oversight
    ("applications", ["read"]),  # All in portfolio
    ("deployment_intents", ["read"]),

    # Cost & License
    ("license_inventory", ["read"]),
    ("license_assignments", ["read"]),
    ("license_forecasts", ["read"]),

    # Metrics & Reporting
    ("compliance_data", ["read", "export"]),
    ("dex_data", ["read"]),
]
```

### Packaging Engineer
```python
PACKAGING_ENGINEER_PERMISSIONS = [
    # Packaging
    ("packaging_requests", ["read", "update"]),  # Assigned only
    ("artifacts", ["create", "read", "update"]),
    ("sbom", ["create", "read"]),
    ("vulnerability_scans", ["read"]),

    # Evidence
    ("evidence_packs", ["create", "read"]),

    # Applications (read-only)
    ("applications", ["read"]),
    ("application_versions", ["read"]),
]
```

### License Manager
```python
LICENSE_MANAGER_PERMISSIONS = [
    # Full license management
    ("license_inventory", ["create", "read", "update", "delete"]),
    ("license_assignments", ["create", "read", "update", "delete"]),
    ("license_forecasts", ["create", "read", "update"]),
    ("vendors", ["create", "read", "update", "delete"]),

    # Applications (read-only for context)
    ("applications", ["read"]),
    ("assets", ["read"]),

    # Reporting
    ("audit_trail", ["read"]),  # License-related only
]
```

### CAB Approver
```python
CAB_APPROVER_PERMISSIONS = [
    # CAB operations
    ("cab_requests", ["read", "approve", "reject"]),
    ("evidence_packs", ["read"]),
    ("approval_decisions", ["create", "read"]),

    # Context
    ("applications", ["read"]),
    ("artifacts", ["read"]),
    ("deployment_intents", ["read"]),
    ("vulnerability_scans", ["read"]),
]
```

### Security Reviewer
```python
SECURITY_REVIEWER_PERMISSIONS = [
    # Security policy
    ("security_exceptions", ["create", "read", "update", "approve", "reject"]),
    ("vulnerability_policy", ["create", "read", "update"]),
    ("pki_management", ["create", "read", "update"]),

    # Vulnerability data
    ("vulnerability_scans", ["read"]),
    ("sbom", ["read"]),

    # Audit
    ("audit_trail", ["read"]),
    ("event_store", ["read"]),
]
```

### Publisher
```python
PUBLISHER_PERMISSIONS = [
    # Publishing (approved only)
    ("publishing", ["execute"]),
    ("execution_planes", ["read", "execute"]),

    # Context (read-only)
    ("artifacts", ["read"]),  # Approved only
    ("deployment_intents", ["read"]),  # Approved only
    ("ring_promotions", ["read", "execute"]),
    ("rollbacks", ["execute"]),

    # Audit
    ("audit_trail", ["read"]),
]
```

### Auditor
```python
AUDITOR_PERMISSIONS = [
    # Read-only access to all audit data
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
```

---

## API Permission Guards

### Decorator-Based Guards

```python
# backend/apps/rbac/decorators.py

from functools import wraps
from rest_framework.exceptions import PermissionDenied

def require_permission(resource: str, action: str):
    """Decorator to require specific permission for a view."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, resource, action):
                log_access_denied(request, resource, action)
                raise PermissionDenied(
                    f"You do not have {action} permission for {resource}"
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: tuple[str, str]):
    """Require at least one of the specified permissions."""
    pass


def require_all_permissions(*permissions: tuple[str, str]):
    """Require all of the specified permissions."""
    pass


def scope_to_user_resources(queryset_field: str = None):
    """Filter queryset to resources the user has access to."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Get user's accessible scopes
            scopes = get_user_scopes(request.user)

            # Filter queryset
            if hasattr(self, 'get_queryset'):
                original_get_queryset = self.get_queryset
                def scoped_queryset():
                    qs = original_get_queryset()
                    return apply_scope_filter(qs, scopes, queryset_field)
                self.get_queryset = scoped_queryset

            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator
```

### ViewSet Integration

```python
# backend/apps/rbac/mixins.py

class RBACViewSetMixin:
    """Mixin for ViewSets with RBAC enforcement."""

    # Define required permissions per action
    permission_map = {
        'list': ('resource', 'read'),
        'retrieve': ('resource', 'read'),
        'create': ('resource', 'create'),
        'update': ('resource', 'update'),
        'partial_update': ('resource', 'update'),
        'destroy': ('resource', 'delete'),
    }

    def get_permissions(self):
        """Return permissions based on action."""
        action = self.action
        if action in self.permission_map:
            resource, perm_action = self.permission_map[action]
            return [RBACPermission(resource, perm_action)]
        return super().get_permissions()

    def get_queryset(self):
        """Filter queryset based on user's scope."""
        qs = super().get_queryset()
        return self.apply_user_scope(qs)

    def apply_user_scope(self, queryset):
        """Override to implement resource-specific scoping."""
        return queryset


# Example usage
class ApplicationViewSet(RBACViewSetMixin, viewsets.ModelViewSet):
    permission_map = {
        'list': ('applications', 'read'),
        'retrieve': ('applications', 'read'),
        'create': ('applications', 'create'),
        'update': ('applications', 'update'),
        'destroy': ('applications', 'delete'),
    }

    def apply_user_scope(self, queryset):
        user = self.request.user

        # Platform Admin sees all
        if has_role(user, Role.RoleType.PLATFORM_ADMIN):
            return queryset

        # Application Manager sees owned applications
        if has_role(user, Role.RoleType.APPLICATION_MANAGER):
            return queryset.filter(
                Q(ownership__owner=user) |
                Q(ownership__portfolio__in=get_user_portfolios(user))
            )

        # Portfolio Manager sees portfolio applications
        if has_role(user, Role.RoleType.PORTFOLIO_MANAGER):
            return queryset.filter(
                ownership__portfolio__manager=user
            )

        # Others see nothing by default
        return queryset.none()
```

---

## Frontend Route Protection

### Route Guards

```tsx
// frontend/src/lib/auth/routeGuards.ts

interface RouteGuard {
  resource: string;
  action: string;
  redirectTo?: string;
}

export const ROUTE_GUARDS: Record<string, RouteGuard> = {
  '/admin/demo-data': { resource: 'platform_settings', action: 'read' },
  '/admin/policy-documents': { resource: 'policy_documents', action: 'read' },
  '/settings/users': { resource: 'users', action: 'read' },
  '/settings/storage': { resource: 'storage_config', action: 'read' },
  '/settings/integrations': { resource: 'integrations', action: 'read' },
  '/portfolios': { resource: 'portfolios', action: 'read' },
  '/licenses': { resource: 'license_inventory', action: 'read' },
  '/cab': { resource: 'cab_requests', action: 'read' },
  '/deploy': { resource: 'deployment_intents', action: 'create' },
  '/audit': { resource: 'audit_trail', action: 'read' },
};


// frontend/src/components/auth/ProtectedRoute.tsx

export function ProtectedRoute({
  resource,
  action,
  children,
  fallback = <AccessDenied />,
}: {
  resource: string;
  action: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { hasPermission, isLoading } = usePermissions();

  if (isLoading) return <LoadingSpinner />;
  if (!hasPermission(resource, action)) return fallback;

  return <>{children}</>;
}
```

### Component-Level Guards

```tsx
// frontend/src/components/auth/PermissionGate.tsx

export function PermissionGate({
  resource,
  action,
  children,
  fallback = null,
}: {
  resource: string;
  action: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { hasPermission } = usePermissions();

  if (!hasPermission(resource, action)) return fallback;
  return <>{children}</>;
}

// Usage
<PermissionGate resource="applications" action="delete">
  <Button variant="destructive" onClick={handleDelete}>
    Delete Application
  </Button>
</PermissionGate>
```

---

## User Management UI

### Enhanced Users Tab

```tsx
// frontend/src/routes/settings/UsersTab.tsx

Features:
1. User List with role badges
2. Add User dialog with:
   - Basic info (email, name)
   - Role selection (multi-select for multiple roles)
   - Scope configuration per role:
     - Portfolio Manager → select portfolio
     - Application Manager → select applications
     - Publisher → select business unit
3. Edit User dialog
4. Role assignment history
5. Activity log (recent actions)
6. Bulk operations (enable/disable, assign role)
```

### Role Management Page (Admin Only)

```tsx
// frontend/src/routes/admin/RoleManagement.tsx

Features:
1. Role list with permission summary
2. Role detail view:
   - Permissions grid (resource × action)
   - Users with this role
   - Scope configuration options
3. Custom role creation (if needed)
4. Role comparison view
```

---

## API Endpoints

```python
# backend/apps/rbac/urls.py

# Roles
GET    /api/v1/rbac/roles/                       # List roles
GET    /api/v1/rbac/roles/{id}/                  # Role details
GET    /api/v1/rbac/roles/{id}/permissions/      # Role permissions
GET    /api/v1/rbac/roles/{id}/users/            # Users with role

# Permissions
GET    /api/v1/rbac/permissions/                 # List all permissions
GET    /api/v1/rbac/permissions/my/              # Current user's permissions

# User Roles
GET    /api/v1/rbac/users/{id}/roles/            # User's role assignments
POST   /api/v1/rbac/users/{id}/roles/            # Assign role to user
DELETE /api/v1/rbac/users/{id}/roles/{role_id}/  # Revoke role
PUT    /api/v1/rbac/users/{id}/roles/{role_id}/  # Update scope

# Permission Checks
POST   /api/v1/rbac/check-permission/            # Check if user has permission
GET    /api/v1/rbac/my-permissions/              # Get current user's permissions

# Audit
GET    /api/v1/rbac/audit-log/                   # Permission audit log
```

---

## Migration Strategy

### Phase 1: Data Model
1. Create RBAC models (Role, Permission, UserRole)
2. Seed default roles and permissions
3. Create migration for existing users

### Phase 2: Backend Integration
1. Add RBAC mixins to all ViewSets
2. Implement permission checks on all endpoints
3. Add audit logging

### Phase 3: Frontend Integration
1. Add route guards
2. Add component-level permission gates
3. Update Settings/Users tab

### Phase 4: Testing
1. Permission matrix tests
2. Scope isolation tests
3. Audit log verification

---

## Deliverables

1. `backend/apps/rbac/` Django app
2. Permission decorators and mixins
3. Frontend permission hooks and guards
4. Enhanced user management UI
5. Role management page (admin)
6. API documentation in `docs/api/rbac-api.yaml`
7. Admin guide in `docs/runbooks/rbac-administration.md`
