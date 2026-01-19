// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Settings domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for settings
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

/**
 * Settings domain types
 */
export interface UserProfile {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  last_login: string | null;
}

export interface UpdateProfileData {
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface AIProvider {
  id: number;
  name: string;
  provider_type: 'OPENAI' | 'ANTHROPIC' | 'GROQ';
  api_key_configured: boolean;
  default_model: string;
  enabled: boolean;
}

export interface UpdateAIProviderData {
  api_key?: string;
  default_model?: string;
  enabled?: boolean;
}

export interface Integration {
  id: number;
  name: string;
  type: 'INTUNE' | 'JAMF' | 'SCCM' | 'LANDSCAPE' | 'ANSIBLE' | 'JIRA' | 'SERVICENOW';
  status: 'CONNECTED' | 'DISCONNECTED' | 'ERROR';
  last_sync: string | null;
  configuration: Record<string, unknown>;
}

export interface IntegrationListResponse {
  integrations: Integration[];
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  PROFILE: '/auth/profile/',
  PROFILE_UPDATE: '/auth/profile/',
  AI_PROVIDERS: '/ai-providers/',
  AI_PROVIDER_UPDATE: (id: number) => `/ai-providers/${id}/`,
  INTEGRATIONS: '/integrations/',
  INTEGRATION_DETAIL: (id: number) => `/integrations/${id}/`,
  INTEGRATION_UPDATE: (id: number) => `/integrations/${id}/`,
  USERS: '/users/',
  USER_DETAIL: (id: number) => `/users/${id}/`,
} as const;

/**
 * Example usage:
 * 
 * ```typescript
 * import { ENDPOINTS, type UserProfile } from './contracts';
 * import { api } from '@/lib/api/client';
 * 
 * const response = await api.get<UserProfile>(ENDPOINTS.PROFILE);
 * ```
 */
