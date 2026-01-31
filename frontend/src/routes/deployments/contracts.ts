// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * BuildWorks.AI-27001: Deployment domain contracts
 * BuildWorks.AI-27002: Types, endpoints, and examples for deployment intents
 * BuildWorks.AI-27004: Use ENDPOINTS constant, never hardcode URL strings
 */

import type { DeploymentIntent } from '@/types/api';

/**
 * Deployment domain types
 */
export interface DeploymentFilters {
  status?: string;
  ring?: string;
  app_name?: string;
}

export interface CreateDeploymentData {
  app_name: string;
  version: string;
  target_ring: string;
  evidence_pack?: Record<string, unknown>;
}

export interface DeploymentListResponse {
  deployments: DeploymentIntent[];
}

export interface PromoteRingResponse {
  correlation_id: string;
  new_ring: string;
  status: string;
}

export interface RollbackResponse {
  correlation_id: string;
  status: string;
  message: string;
}

/**
 * BuildWorks.AI-27004: ENDPOINTS constant - never hardcode URL strings
 */
export const ENDPOINTS = {
  DEPLOYMENTS_LIST: '/deployments/list',
  DEPLOYMENT_DETAIL: (correlationId: string) => `/deployments/${correlationId}/`,
  DEPLOYMENT_CREATE: '/deployments/',
  DEPLOYMENT_PROMOTE: (correlationId: string) => `/deployments/${correlationId}/promote/`,
  DEPLOYMENT_ROLLBACK: (correlationId: string) => `/deployments/${correlationId}/rollback/`,
} as const;

/**
 * Stack types (E6)
 */
export interface StackRing {
  ring: string;
  success_rate: number;
  success_count: number;
  failure_count: number;
  promoted_at: string | null;
}

export interface StackDeployment {
  id: string;
  correlation_id: string;
  status: string;
  target_ring: string;
  risk_score: number | null;
  created_at: string;
  rings: StackRing[];
}

export interface StackVersion {
  version: string;
  deployments: StackDeployment[];
}

export interface StackApplication {
  id: string;
  name: string;
  versions: StackVersion[];
}

export interface StackApplicationsResponse {
  applications: StackApplication[];
}

export interface StackDependency {
  id: string;
  name: string;
  type: string;
  required?: boolean;
}

export interface StackDependenciesResponse {
  application: {
    id: string;
    name: string;
  };
  dependencies: StackDependency[];
  dependents: StackDependency[];
}

export interface DeploymentEvent {
  id: string;
  type: string;
  title: string;
  description: string;
  status: string;
  timestamp: string;
  user: string;
  item: {
    type: string;
    id: string;
    app_name: string;
    version: string;
  };
}

export interface StackEventsResponse {
  events: DeploymentEvent[];
}

export interface StackFilters {
  search?: string;
  status?: string[];
  platform?: string[];
  ring?: string[];
  owner?: string[];
  dateRange?: { from: Date; to: Date } | null;
}

export type StackItemType = 'application' | 'version' | 'deployment' | 'ring';

export interface StackItem {
  type: StackItemType;
  id: string;
  [key: string]: unknown;
}

/**
 * Stack endpoints (E6)
 */
export const STACK_ENDPOINTS = {
  APPLICATIONS: '/api/v1/deployments/stack/applications/',
  APPLICATION_DEPENDENCIES: (appId: string) => `/api/v1/deployments/stack/applications/${appId}/dependencies/`,
  EVENTS: '/api/v1/deployments/stack/events/',
  PROMOTE: (correlationId: string) => `/api/v1/deployments/stack/deployments/${correlationId}/promote/`,
  PAUSE: (correlationId: string) => `/api/v1/deployments/stack/deployments/${correlationId}/pause/`,
  RESUME: (correlationId: string) => `/api/v1/deployments/stack/deployments/${correlationId}/resume/`,
  ROLLBACK: (correlationId: string) => `/api/v1/deployments/stack/deployments/${correlationId}/rollback/`,
  CANCEL: (correlationId: string) => `/api/v1/deployments/stack/deployments/${correlationId}/cancel/`,
} as const;

/**
 * Example usage:
 *
 * ```typescript
 * import { ENDPOINTS, type DeploymentListResponse } from './contracts';
 * import { api } from '@/lib/api/client';
 *
 * const response = await api.get<DeploymentListResponse>(ENDPOINTS.DEPLOYMENTS_LIST);
 * ```
 */
