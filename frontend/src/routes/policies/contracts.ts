// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Policy domain contracts
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * Policy setting category
 */
export type SettingCategory =
  | 'installation'
  | 'uninstall'
  | 'update'
  | 'configuration'
  | 'restart'
  | 'dependency'
  | 'compliance';

/**
 * Policy template type
 */
export type TemplateType =
  | 'standard'
  | 'security'
  | 'productivity'
  | 'browser'
  | 'development'
  | 'enterprise'
  | 'optional'
  | 'custom';

/**
 * Application policy
 */
export interface ApplicationPolicy {
  id: string;
  correlation_id: string;
  name: string;
  description: string;
  application: string; // UUID
  application_name: string;
  application_identifier: string;
  application_version: string | null; // UUID
  version_str: string | null;
  platform: string;
  is_active: boolean;
  is_default: boolean;
  created_by: string | null; // UUID
  created_by_username: string | null;
  settings: PolicySetting[];
  settings_dict: Record<string, Record<string, unknown>>;
  created_at: string;
  updated_at: string;
}

/**
 * Policy setting
 */
export interface PolicySetting {
  id: string;
  policy: string; // UUID
  category: SettingCategory;
  setting_key: string;
  setting_value: unknown;
  intune_mapping: Record<string, unknown>;
  jamf_mapping: Record<string, unknown>;
  sccm_mapping: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

/**
 * Policy template
 */
export interface PolicyTemplate {
  id: string;
  name: string;
  template_type: TemplateType;
  description: string;
  settings: Record<string, Record<string, unknown>>;
  is_system: boolean;
  platform: string;
  created_at: string;
  updated_at: string;
}

/**
 * Create policy data
 */
export interface CreatePolicyData {
  name: string;
  description?: string;
  application: string;
  application_version?: string | null;
  platform: string;
  is_active?: boolean;
  is_default?: boolean;
  settings?: Omit<PolicySetting, 'id' | 'policy' | 'created_at' | 'updated_at'>[];
}

/**
 * Update policy data
 */
export interface UpdatePolicyData {
  name?: string;
  description?: string;
  is_active?: boolean;
  is_default?: boolean;
  settings?: Omit<PolicySetting, 'id' | 'policy' | 'created_at' | 'updated_at'>[];
}

/**
 * Apply template data
 */
export interface ApplyTemplateData {
  template_id: string;
}

/**
 * Policy validation response
 */
export interface PolicyValidationResponse {
  valid: boolean;
  errors?: string[];
  message?: string;
}

/**
 * Policy mapping preview response
 */
export interface PolicyMappingPreviewResponse {
  target_plane: 'intune' | 'jamf' | 'sccm';
  mapping: Record<string, unknown>;
}

/**
 * Policy list response
 */
export interface PolicyListResponse {
  results: ApplicationPolicy[];
  count: number;
}

/**
 * Template list response
 */
export interface TemplateListResponse {
  results: PolicyTemplate[];
  count: number;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  POLICIES_LIST: '/api/v1/policy/policies/',
  POLICY_DETAIL: (id: string) => `/api/v1/policy/policies/${id}/`,
  POLICY_CREATE: '/api/v1/policy/policies/',
  POLICY_UPDATE: (id: string) => `/api/v1/policy/policies/${id}/`,
  POLICY_DELETE: (id: string) => `/api/v1/policy/policies/${id}/`,
  POLICY_APPLY_TEMPLATE: (id: string) => `/api/v1/policy/policies/${id}/apply_template/`,
  POLICY_VALIDATE: (id: string) => `/api/v1/policy/policies/${id}/validate/`,
  POLICY_PREVIEW_MAPPING: (id: string) => `/api/v1/policy/policies/${id}/preview_mapping/`,
  TEMPLATES_LIST: '/api/v1/policy/templates/',
  TEMPLATE_DETAIL: (id: string) => `/api/v1/policy/templates/${id}/`,
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type ApplicationPolicy } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<PolicyListResponse>(ENDPOINTS.POLICIES_LIST);
 * const policy = await api.get<ApplicationPolicy>(ENDPOINTS.POLICY_DETAIL('123'));
 * ```
 */
