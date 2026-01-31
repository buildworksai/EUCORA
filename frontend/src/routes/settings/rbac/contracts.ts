// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: RBAC domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for RBAC
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * RBAC domain types
 */

export type RoleType =
  | 'platform_admin'
  | 'application_manager'
  | 'portfolio_manager'
  | 'packaging_engineer'
  | 'license_manager'
  | 'cab_approver'
  | 'security_reviewer'
  | 'publisher'
  | 'auditor';

export type ResourceType =
  | 'platform_settings'
  | 'storage_config'
  | 'ai_providers'
  | 'integrations'
  | 'users'
  | 'roles'
  | 'applications'
  | 'application_versions'
  | 'artifacts'
  | 'portfolios'
  | 'portfolio_metrics'
  | 'packaging_requests'
  | 'sbom'
  | 'vulnerability_scans'
  | 'license_inventory'
  | 'license_assignments'
  | 'license_forecasts'
  | 'vendors'
  | 'cab_requests'
  | 'evidence_packs'
  | 'approval_decisions'
  | 'security_exceptions'
  | 'vulnerability_policy'
  | 'pki_management'
  | 'deployment_intents'
  | 'ring_promotions'
  | 'rollbacks'
  | 'publishing'
  | 'execution_planes'
  | 'assets'
  | 'dex_data'
  | 'compliance_data'
  | 'audit_trail'
  | 'event_store'
  | 'ai_agents'
  | 'ai_workflows'
  | 'policy_documents'
  | 'knowledge_config'
  | 'knowledge_search'
  // E10: CMDB Integration Agent
  | 'cmdb_connections'
  | 'cmdb_discrepancies'
  | 'cmdb_sync'
  // E11: Change Communications Agent
  | 'change_records'
  | 'stakeholder_groups'
  | 'communication_templates'
  // E14: Discovery Agent
  | 'discovery_sources'
  | 'normalized_applications'
  | 'license_gaps'
  | 'patch_gaps';

export type ActionType =
  | 'create'
  | 'read'
  | 'update'
  | 'delete'
  | 'execute'
  | 'approve'
  | 'reject'
  | 'publish'
  | 'export';

export type AuditActionType =
  | 'role_assigned'
  | 'role_revoked'
  | 'scope_modified'
  | 'permission_granted'
  | 'permission_revoked'
  | 'access_denied'
  | 'access_granted';

export interface Permission {
  id: string;
  resource: ResourceType;
  resource_label: string;
  action: ActionType;
  action_label: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: string;
  role_type: RoleType;
  display_name: string;
  description: string;
  is_system: boolean;
  permissions?: Permission[];
  permission_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface UserRole {
  id: string;
  user: string;
  user_username: string;
  user_email: string;
  role: Role;
  role_id: string;
  portfolio_scope?: string;
  portfolio_name?: string;
  application_scope?: string[];
  application_names?: string[];
  business_unit_scope?: string;
  is_active: boolean;
  valid_from: string;
  valid_until?: string;
  assigned_by?: string;
  assigned_by_username?: string;
  created_at: string;
  updated_at: string;
}

export interface UserRoleCreate {
  role_id: string;
  portfolio_scope?: string;
  application_scope?: string[];
  business_unit_scope?: string;
  valid_from?: string;
  valid_until?: string;
}

export interface PermissionAuditLog {
  id: string;
  correlation_id: string;
  action_type: AuditActionType;
  action_type_label: string;
  actor?: string;
  actor_username?: string;
  target_user?: string;
  target_user_username?: string;
  resource: string;
  resource_id: string;
  action: string;
  details: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  updated_at: string;
}

export interface MyPermissions {
  permissions: Permission[];
  roles: Role[];
  is_admin: boolean;
}

export interface CheckPermissionRequest {
  resource: ResourceType;
  action: ActionType;
  resource_id?: string;
}

export interface CheckPermissionResponse {
  has_permission: boolean;
  resource: ResourceType;
  action: ActionType;
}

/**
 * ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  PERMISSIONS: '/api/v1/rbac/permissions/',
  PERMISSION_DETAIL: (id: string) => `/api/v1/rbac/permissions/${id}/`,
  ROLES: '/api/v1/rbac/roles/',
  ROLE_DETAIL: (id: string) => `/api/v1/rbac/roles/${id}/`,
  ROLE_PERMISSIONS: (id: string) => `/api/v1/rbac/roles/${id}/permissions/`,
  ROLE_USERS: (id: string) => `/api/v1/rbac/roles/${id}/users/`,
  MY_PERMISSIONS: '/api/v1/rbac/my-permissions/',
  CHECK_PERMISSION: '/api/v1/rbac/check-permission/',
  USER_ROLES: (userId: string) => `/api/v1/rbac/users/${userId}/roles/`,
  USER_ROLE_DETAIL: (userId: string, roleId: string) =>
    `/api/v1/rbac/users/${userId}/roles/${roleId}/`,
  USER_ROLES_LIST: '/api/v1/rbac/user-roles/',
  USER_ROLE_DETAIL_BY_ID: (id: string) => `/api/v1/rbac/user-roles/${id}/`,
  AUDIT_LOG: '/api/v1/rbac/audit-log/',
  AUDIT_LOG_DETAIL: (id: string) => `/api/v1/rbac/audit-log/${id}/`,
} as const;
