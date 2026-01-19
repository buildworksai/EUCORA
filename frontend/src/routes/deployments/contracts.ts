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
 * Example usage:
 * 
 * ```typescript
 * import { ENDPOINTS, type DeploymentListResponse } from './contracts';
 * import { api } from '@/lib/api/client';
 * 
 * const response = await api.get<DeploymentListResponse>(ENDPOINTS.DEPLOYMENTS_LIST);
 * ```
 */
